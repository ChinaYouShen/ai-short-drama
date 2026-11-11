#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai-short-drama 交付自检

按本技能包自己的字段约定做确定性检查，不依赖任何第三方库，也不读外部 schema。
只查能被机器判定的事：字段结构、时间码、镜长、段长、发声窗口、编号绑定、主色、景别与运镜枚举、正文角色名。
不能机器判定的（表演质量、情绪是否成立、构图是否好看）明确不做，不要指望它替人做美学判断。

一条硬规矩：凡是"格式不合规就跳过"的写法都算 bug。所有检查先抓全部候选，再判格式，
不合规的必须报出来——静默放行比不检查更害人。

用法：

    # 只查分镜 JSON
    python3 scripts/validate.py storyboard.json

    # 同时查 H3 视频提示词正文
    python3 scripts/validate.py storyboard.json --prompt prompt.txt

    # 没有分镜 JSON，只查提示词，并给出角色名清单
    python3 scripts/validate.py --prompt prompt.txt --names 沈砚,苏晚

    # 查某门武功的专属约束（无光门不得出现发光、不给暖点门不得出现暖色）
    python3 scripts/validate.py --prompt prompt.txt --method 独孤九剑

    # 自检：确认脚本本身可用
    python3 scripts/validate.py --self-test

分镜 JSON 形状（缺什么就跳过对应检查，不猜）：

{
  "shots": [
    {"number": 1, "duration": 3.2, "shotSize": "近景", "camera": "缓慢推近",
     "dialogue": "你早就知道了。", "characterNames": ["沈砚"],
     "sceneName": "柴房", "propNames": ["断刃匕首"], "voiceNames": []}
  ],
  "assets": {"characters": ["沈砚", "苏晚"], "scenes": ["柴房"], "props": ["断刃匕首"], "voices": ["沈砚"]}
}

退出码：0 全部通过；1 有阻断项；2 只有警告。
"""

import argparse
import json
import re
import sys
import unicodedata

# ── 本技能包的枚举与阈值（改这里就等于改规则，别散落在各文件里）──
SHOT_SIZES = ["大特写", "特写", "近景", "中近景", "中景", "全景", "远景", "大全景"]
WIDE_BANNED_FOR_PEOPLE = ["远景", "大全景"]
CAMERA_MOVES = ["固定机位", "缓慢推近", "缓慢后移", "横向滑轨", "平移", "跟拍", "平摇", "升降", "焦点变化", "变焦"]
MAX_PEOPLE_IN_SHOT = 3
SPEECH_CHARS_PER_SEC = 4.1      # 中文可发声字/秒，取慢的一端
SEGMENT_MAX_SECONDS = 15.0      # 单段生成上限（动作 + 台词合计）
MIN_CUT_SECONDS = 2.0
MAX_CUT_SECONDS = 5.0
TIMECODE_TOLERANCE = 0.05       # 秒

# H3 字段：基础路线三字段、多参考路线六字段，字段名和顺序都固定
BASE_FIELDS = ["integrated_multimodal_description", "overall_soundscape", "non_diegetic_music"]
REF_FIELDS = ["subject_definitions", "summary", "retention_analysis",
              "detailed_description", "overall_soundscape", "non_diegetic_music"]
REF_FIELDS_ZH = ["主体定义", "摘要", "保留分析", "详细描述", "整体声景", "非叙事配乐"]
# 段起点只认「正文时间线」的字段。主体定义/摘要/保留分析属于同一段的头部，
# 不是新段的开始；把它们列进来会把中文六段误拆成两段（见 --self-test 用例）。
SEGMENT_START_PATTERNS = ["integrated_multimodal_description:", "detailed_description:",
                          "详细描述:"]

# 刻意全不给光的门（正文不得出现发光、光晕、光形）
NO_LIGHT_METHODS = ["打狗棒法", "空明拳", "太极拳", "玄铁剑法", "独孤九剑", "庖丁解牛掌",
                    "八极拳", "越女剑法", "夫妻刀法", "铁剑门剑法", "苗家剑法", "追魂夺命剑"]
LIGHT_WORDS = ["发光", "光晕", "光形", "光效", "光芒", "光尘", "光纹", "光带", "亮起"]
# 刻意不给暖点的门（正文不得出现暖色、暖点、火花）
NO_WARM_METHODS = ["蛤蟆功", "五毒神掌", "玄冥神掌", "化功大法", "冰蚕毒掌", "九阴白骨爪",
                   "十蛛万毒手", "千蛛万毒手", "吸星大法"]
WARM_WORDS = ["暖色", "暖点", "暖光", "暖白", "暖黄", "赤金", "橙红", "橙黄", "火花"]
# 法相比例区间
FAXIANG_RATIO_RANGE = (1.2, 1.5)
# 语言码必须是完整语言名；这些短码模型侧不认
SHORT_LANG_CODES = {"zh", "en", "ja", "jp", "cn", "kr", "ko", "fr", "de", "es", "ru",
                    "eng", "chi", "chs", "cht", "yue", "cmn"}
# 音频保留关系（用了 <Audio N> 就必须在保留分析里有一行账）
AUDIO_RETENTION = ["fully_copy", "partially_copy", "reference", "weak_reference"]

RESULT = []


def ok(gate, msg):
    RESULT.append(("PASS", gate, msg))


def warn(gate, msg):
    RESULT.append(("WARN", gate, msg))


def bad(gate, msg):
    RESULT.append(("FAIL", gate, msg))


def audible_chars(text):
    """可发声字数：去掉标点、空白与括号注释，只数真正要念出来的字。"""
    if not text:
        return 0
    text = re.sub(r"<[^>]+>", "", text)                 # 标签
    text = re.sub(r"（[^）]*）|\([^)]*\)", "", text)      # 括号内为动作/提示，不念
    stripped = "".join(
        ch for ch in text
        if unicodedata.category(ch)[0] in ("L", "N")
    )
    return len(stripped)


def parse_tc(tc):
    """MM:SS.mmm 或 HH:MM:SS.mmm → 秒。"""
    parts = tc.split(":")
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    raise ValueError("时间码格式不对: %r" % tc)


BODY_PATTERNS = ["[Shot", "详细描述", "detailed_description", "integrated_multimodal_description"]


def split_segments(text):
    """按段起始字段切分。

    H3 允许把一条连续剧情拆成多组输出，每组从 00:00.000 重新起算，
    所以时间码、镜号、镜长、段长、台词容量都必须逐段判，不能全篇连起来算。

    只有「当前段已经装了正文时间线」时才允许开新段：主体定义、摘要、保留分析
    是段的头部，不能各自成为一段，否则中文六段会被切成若干空段。
    """
    segs = []
    cur = []
    has_body = False
    for line in text.splitlines():
        stripped = line.strip()
        if (any(stripped.startswith(p) for p in SEGMENT_START_PATTERNS)
                and cur and has_body):
            segs.append("\n".join(cur))
            cur = [line]
            has_body = any(p in line for p in BODY_PATTERNS)
        else:
            cur.append(line)
            if any(p in line for p in BODY_PATTERNS):
                has_body = True
    if cur:
        segs.append("\n".join(cur))
    return segs or [text]


def check_field_structure(text):
    """字段名必须齐全、顺序必须固定。这是 H3 最外层的契约，缺一个字段整段就不成立。"""
    has_ref = ("subject_definitions" in text or "retention_analysis" in text
               or "主体定义" in text or "保留分析" in text)
    want_en = REF_FIELDS if has_ref else BASE_FIELDS
    want_zh = REF_FIELDS_ZH if has_ref else None

    present = []
    if want_zh and sum(1 for f in want_zh if f in text) >= sum(1 for f in want_en if f in text):
        # 中文六段：只要求出现过的都能对上顺序
        names = want_zh
        label = "中文六段"
    else:
        names = want_en
        label = "六段" if has_ref else "三字段"

    missing = [n for n in names if n not in text]
    # 多段输出时，段级字段会重复；主体定义只在开头写一次
    if missing and has_ref and "subject_definitions" in missing and "主体定义" in text:
        missing.remove("subject_definitions")
    if missing:
        bad("P11 字段结构", "%s缺字段：%s（字段名和顺序固定，不能省、不能改名）" % (label, "、".join(missing)))
        return
    pos = [text.index(n) for n in names]
    if pos != sorted(pos):
        bad("P11 字段结构", "%s字段顺序颠倒，应为：%s" % (label, " → ".join(names)))
    else:
        ok("P11 字段结构", "%s字段齐全、顺序正确（%s）" % (label, " → ".join(names)))


def check_segment(seg, idx, method):
    """单段检查：镜号、时间码、镜长、末镜长、段长声明、台词容量、主色、法相比例。"""
    # 镜号：每段都从 1 起
    shot_nums = [int(m) for m in re.findall(r"\[Shot\s+(\d+)\]", seg)]
    if shot_nums:
        if shot_nums == list(range(1, len(shot_nums) + 1)):
            ok("P2 镜号", "第%d段 [Shot N] 顺序正常：%s" % (idx, shot_nums))
        else:
            bad("P2 镜号", "第%d段 [Shot N] 不连续（每段都要从 1 起）：%s" % (idx, shot_nums))
    else:
        bad("P21 时间线", "第%d段没有任何 [Shot N] 镜头标记；提示词必须有逐镜时间线，"
            "每镜写 [Shot N] 与 At mm:ss.mmm，否则无法生成也无法对轴" % idx)

    # 时间码：先抓所有 At 后记号，格式不合规的一条不留地报出来
    raw_tcs = re.findall(r"At\s+([0-9][0-9:.]*)", seg)
    malformed = [t for t in raw_tcs if not re.match(r"^\d{2}:\d{2}\.\d{3}$", t)]
    if malformed:
        bad("P3 时间码格式", "第%d段 At 后的时间码必须是 mm:ss.mmm（两位分、两位秒、三位毫秒），不合规：%s"
            % (idx, "、".join(malformed[:6])))
    tcs = [t for t in raw_tcs if t not in malformed]
    vals = [parse_tc(t) for t in tcs]
    durations = []
    if vals:
        if any(b <= a for a, b in zip(vals, vals[1:])):
            bad("P3 时间码", "第%d段 At 时间码未严格递增：%s" % (idx, tcs))
        elif vals[0] != 0 and vals[0] < MIN_CUT_SECONDS - TIMECODE_TOLERANCE:
            bad("P3 时间码", "第%d段首镜没写 At 时，第一个 At（%s）就是第二镜起点，必须 ≥ %.0fs"
                % (idx, tcs[0], MIN_CUT_SECONDS))
        else:
            ok("P3 时间码", "第%d段 %d 个 At 时间码递增正常，起点 %s" % (idx, len(tcs), tcs[0]))
        # 首镜可以不写 At：此时切点列表的第一个 At 就是第二镜起点，1 号镜从 0 秒算起。
        # 首镜写了 At 00:00.000 时同样成立，两种情况统一补上 0 点再连差。
        starts = vals if (vals and vals[0] == 0) else [0.0] + vals
        durations = [b - a for a, b in zip(starts, starts[1:])]

    bad_du = []
    for i, d in enumerate(durations):
        if d < MIN_CUT_SECONDS - TIMECODE_TOLERANCE:
            bad_du.append("第%d镜 %.1fs < %.0fs" % (i + 1, d, MIN_CUT_SECONDS))
        elif d > MAX_CUT_SECONDS + TIMECODE_TOLERANCE:
            bad_du.append("第%d镜 %.1fs > %.0fs" % (i + 1, d, MAX_CUT_SECONDS))
    if bad_du:
        bad("P7 镜长", "第%d段单镜必须 %.0f～%.0f 秒：%s" % (idx, MIN_CUT_SECONDS, MAX_CUT_SECONDS, "；".join(bad_du)))
    elif durations:
        ok("P7 镜长", "第%d段可推算的 %d 段镜长都在 %.0f～%.0f 秒内" % (idx, len(durations), MIN_CUT_SECONDS, MAX_CUT_SECONDS))

    # 段长声明：末镜结束点不写时间码，只能靠「本段总长约 X 秒」核对
    decl = None
    m = re.search(r"(?:本段|全段|整段)?总[时長长]约?\s*([0-9]+(?:\.[0-9]+)?)\s*秒", seg)
    if not m:
        m = re.search(r"Total duration[^0-9]{0,12}([0-9]+(?:\.[0-9]+)?)", seg, re.I)
    if m:
        decl = float(m.group(1))
    if decl is None:
        warn("P8 段长", "第%d段没有「总时长 X 秒」声明，无法确认 ≤%.0f 秒" % (idx, SEGMENT_MAX_SECONDS))
    elif decl > SEGMENT_MAX_SECONDS + 1e-6:
        bad("P8 段长", "第%d段声明 %.1fs 超过单段上限 %.0fs，必须拆段并各自 ≤%.0fs"
            % (idx, decl, SEGMENT_MAX_SECONDS, SEGMENT_MAX_SECONDS))
    elif vals and vals[-1] >= decl:
        bad("P8 段长", "第%d段末镜起点 %s 已不早于声明总时长 %.1fs" % (idx, tcs[-1], decl))
    else:
        ok("P8 段长", "第%d段声明 %.1fs，在单段上限 %.0fs 内" % (idx, decl, SEGMENT_MAX_SECONDS))

    # 末镜时长：末镜不写结束时间码，但它的长度 = 声明总时长 − 末镜起点，同样必须落在 2～5 秒
    if decl is not None and len(vals) >= 2:
        last = decl - vals[-1]
        if last < MIN_CUT_SECONDS - TIMECODE_TOLERANCE or last > MAX_CUT_SECONDS + TIMECODE_TOLERANCE:
            bad("P12 末镜长", "第%d段末镜 %.1fs（声明 %.1fs − 起点 %.3fs）不在 %.0f～%.0f 秒；"
                "末镜同样要切，或调整声明与切点" % (idx, last, decl, vals[-1], MIN_CUT_SECONDS, MAX_CUT_SECONDS))
        else:
            ok("P12 末镜长", "第%d段末镜 %.1fs，在 %.0f～%.0f 秒内" % (idx, last, MIN_CUT_SECONDS, MAX_CUT_SECONDS))

    # 台词容量
    lines = re.findall(r"<d(?:[^>]*)>(.*?)</d>", seg, re.S)
    if decl is not None and lines:
        spoken = 0
        for body in lines:
            body_d = re.sub(r"^\[[^\]]*\]", "", body.strip())
            spoken += audible_chars(body_d)
        need = spoken / SPEECH_CHARS_PER_SEC
        if need > decl + 0.05:
            bad("P9 台词容量", "第%d段台词 %d 字按 %.1f 字/秒需 %.1fs，超过本段 %.1fs；精简台词或拆段"
                % (idx, spoken, SPEECH_CHARS_PER_SEC, need, decl))
        else:
            ok("P9 台词容量", "第%d段台词 %d 字约 %.1fs，放得进 %.1fs" % (idx, spoken, need, decl))
            if need / decl > 0.71:
                warn("P10 台词密度", "第%d段台词占 %.0f%% 时间（%.1f 字/秒），没给表演留空；"
                     "10/12/15 秒的实写预算是 20～28 / 28～36 / 36～44 字" % (idx, need / decl * 100, spoken / decl))

    # 主色：一招只有一个主色
    colors = re.findall(r"#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})", seg)
    uniq = sorted(set(c.upper() for c in colors))
    if len(uniq) > 1:
        bad("P15 主色", "第%d段出现 %d 个色值 %s；一招只能有一个主色，其余颜色用文字描述，不要再给色值"
            % (idx, len(uniq), "、".join(uniq)))
    elif uniq:
        ok("P15 主色", "第%d段主色 %s 唯一" % (idx, uniq[0]))

    # 法相比例：给了法相就必须写明确比例且落在 1.2～1.5 倍
    if re.search(r"法相|金身|巨像|神像", seg):
        ratios = [float(x) for x in re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*倍", seg)]
        if not ratios:
            bad("P16 法相比例", "第%d段出现法相但没有写明确的倍率；必须写「约 1.2～1.5 倍」中的具体数值" % idx)
        else:
            outside = [r for r in ratios if not (FAXIANG_RATIO_RANGE[0] - 1e-6 <= r <= FAXIANG_RATIO_RANGE[1] + 1e-6)]
            if outside:
                bad("P16 法相比例", "第%d段法相比例 %s 不在 %.1f～%.1f 倍" % (idx, outside, FAXIANG_RATIO_RANGE[0], FAXIANG_RATIO_RANGE[1]))
            else:
                ok("P16 法相比例", "第%d段法相比例 %s，在 %.1f～%.1f 倍内" % (idx, ratios, FAXIANG_RATIO_RANGE[0], FAXIANG_RATIO_RANGE[1]))

    # 门派专属：无光门不得发光、不给暖点门不得暖
    if method:
        if any(n in method for n in NO_LIGHT_METHODS):
            hits = [w for w in LIGHT_WORDS if w in seg]
            if hits:
                bad("P17 无光门", "「%s」是刻意不给光的门，正文出现 %s" % (method, "、".join(hits)))
            else:
                ok("P17 无光门", "「%s」正文无发光词" % method)
        if any(n in method for n in NO_WARM_METHODS):
            hits = [w for w in WARM_WORDS if w in seg]
            if hits:
                bad("P18 不给暖点", "「%s」是刻意不给暖点的门，正文出现 %s" % (method, "、".join(hits)))
            else:
                ok("P18 不给暖点", "「%s」正文无暖色词" % method)


def check_storyboard(data):
    shots = data.get("shots") or []
    if not shots:
        warn("S0", "分镜 JSON 没有 shots 数组，跳过结构检查")
        return

    assets = data.get("assets") or {}
    characters = set(assets.get("characters") or [])
    scenes = set(assets.get("scenes") or [])
    props = set(assets.get("props") or [])
    voices = set(assets.get("voices") or [])

    # 1. 镜号连续
    nums = [s.get("number") for s in shots]
    if all(isinstance(n, int) for n in nums):
        if nums == list(range(1, len(nums) + 1)):
            ok("S1 镜号", "镜号 1..%d 连续" % len(nums))
        else:
            bad("S1 镜号", "镜号不连续或重复：%s" % nums)
    else:
        warn("S1 镜号", "部分镜头没有 number 字段，跳过镜号检查")

    # 2. 时长与段上限
    total = sum(float(s.get("duration") or 0) for s in shots)
    if total > SEGMENT_MAX_SECONDS + TIMECODE_TOLERANCE:
        bad("S2 时长", "合计 %.3fs 超过单段上限 %.0fs，应拆段" % (total, SEGMENT_MAX_SECONDS))
    else:
        ok("S2 时长", "合计 %.3fs，未超单段上限 %.0fs" % (total, SEGMENT_MAX_SECONDS))

    # 3. 单镜时长区间（只在镜数 ≥2 时检查，单镜段不受单镜下限约束）
    if len(shots) >= 2:
        for s in shots:
            d = float(s.get("duration") or 0)
            if d and not (MIN_CUT_SECONDS - 0.01 <= d <= MAX_CUT_SECONDS + 0.01):
                warn("S3 单镜时长", "第 %s 镜 %.2fs 不在 %.0f–%.0fs 区间，除非有明确理由" % (
                    s.get("number"), d, MIN_CUT_SECONDS, MAX_CUT_SECONDS))

    # 4. 时间码累计一致
    acc = 0.0
    tc_checked = 0
    tc_errors = 0
    for s in shots:
        tc = s.get("timecode")
        if tc:
            tc_checked += 1
            try:
                expect = acc
                got = parse_tc(tc)
                if abs(got - expect) > TIMECODE_TOLERANCE:
                    tc_errors += 1
                    bad("S4 时间码", "第 %s 镜写 %s(%.3fs)，累计应为 %.3fs" % (
                        s.get("number"), tc, got, expect))
            except ValueError as e:
                tc_errors += 1
                bad("S4 时间码", "第 %s 镜：%s" % (s.get("number"), e))
        acc += float(s.get("duration") or 0)
    if tc_checked and not tc_errors:
        ok("S4 时间码", "%d 个时间码与各镜时长累计一致（容差 %.2fs）" % (tc_checked, TIMECODE_TOLERANCE))

    # 5. 景别枚举 + 人物入画禁远景
    for s in shots:
        size = s.get("shotSize")
        if size and size not in SHOT_SIZES:
            warn("S5 景别", "第 %s 镜景别「%s」不在枚举内" % (s.get("number"), size))
        if size in WIDE_BANNED_FOR_PEOPLE and (s.get("characterNames") or []):
            bad("S5 景别", "第 %s 镜人物入画却用了「%s」，应收紧到近景或中近景" % (s.get("number"), size))

    # 6. 运镜枚举
    for s in shots:
        cam = s.get("camera")
        if cam and not any(m in cam for m in CAMERA_MOVES):
            warn("S6 运镜", "第 %s 镜运镜「%s」未落在枚举内" % (s.get("number"), cam))

    # 7. 同框人数
    for s in shots:
        n = len(s.get("characterNames") or [])
        if n > MAX_PEOPLE_IN_SHOT:
            bad("S7 同框", "第 %s 镜同框 %d 人，超过 %d 人，需拆镜或写明拆解说明" % (
                s.get("number"), n, MAX_PEOPLE_IN_SHOT))

    # 8. 资产绑定
    missing = []
    for s in shots:
        for name in (s.get("characterNames") or []):
            if characters and name not in characters:
                missing.append("第 %s 镜角色「%s」不在清单" % (s.get("number"), name))
        scene = s.get("sceneName")
        if scene and scenes and scene not in scenes:
            missing.append("第 %s 镜场景「%s」不在清单" % (s.get("number"), scene))
        for name in (s.get("propNames") or []):
            if props and name not in props:
                missing.append("第 %s 镜道具「%s」不在清单" % (s.get("number"), name))
        for name in (s.get("voiceNames") or []):
            if voices and name not in voices:
                missing.append("第 %s 镜声音「%s」不在清单" % (s.get("number"), name))
    if missing:
        bad("S8 资产绑定", "；".join(missing[:6]) + ("…" if len(missing) > 6 else ""))
    elif assets:
        ok("S8 资产绑定", "角色/场景/道具/声音引用均能在清单内找到")

    # 9. 发声窗口
    overloaded = []
    for s in shots:
        text = s.get("dialogue") or ""
        chars = audible_chars(text)
        if not chars:
            continue
        d = float(s.get("duration") or 0)
        if not d:
            continue
        window = d - 0.5 * 2          # 首尾各留约 0.5 秒反应
        capacity = window * SPEECH_CHARS_PER_SEC
        if chars > capacity:
            overloaded.append("第 %s 镜 %d 字 / 窗口容量 %.1f 字（%.1fs 镜长）" % (
                s.get("number"), chars, capacity, d))
    if overloaded:
        bad("S9 口播预算", "台词超载：" + "；".join(overloaded[:4]) +
            "。按顺序处理：删装饰动作 → 并行 → 单一注意中心 → 报冲突拆分")
    else:
        ok("S9 口播预算", "有台词的镜头均在发声窗口内（按 %.1f 字/秒）" % SPEECH_CHARS_PER_SEC)


def check_prompt(text, names, method=None):
    # 字段结构
    check_field_structure(text)

    # 1. 正文禁角色名
    if names:
        hits = []
        for name in names:
            if not name:
                continue
            for line in text.splitlines():
                if name in line and "<d>" not in line:
                    hits.append("%s：%s" % (name, line.strip()[:40]))
                    break
        if hits:
            bad("P1 禁角色名", "视频提示词正文出现角色名（只允许出现在 <d> 台词内）：" + "；".join(hits[:4]))
        else:
            ok("P1 禁角色名", "正文未出现 %d 个角色名" % len(names))

    # 2. 按段跑时间码 / 镜长 / 段长 / 台词容量 / 主色 / 法相 / 门派约束
    segs = split_segments(text)
    for i, seg in enumerate(segs, 1):
        check_segment(seg, i, method)

    # 3. 参考编号不跳号、连续
    for tag in ("Picture", "Video", "Audio", "Subject"):
        refs = [int(m) for m in re.findall(r"<%s\s+(\d+)>" % tag, text)]
        if not refs:
            continue
        uniq = sorted(set(refs))
        if uniq != list(range(1, len(uniq) + 1)):
            bad("P4 编号", "<%s N> 编号跳号或不从 1 起：%s" % (tag, uniq))
        else:
            ok("P4 编号", "<%s N> 共 %d 个，编号连续" % (tag, len(uniq)))

    # 4. 否定式动作粗筛
    neg = re.findall(r"(没有[^，。；]{1,6}|没[^\u4e00-\u9fa5]?(?:接话|按下去|看|动|说话)|不去看|不看他|不看她)", text)
    if neg:
        warn("P5 否定式动作", "疑似否定式动作 %d 处（画面生成不了「没发生的事」，改写成替代动作）：%s" % (
            len(neg), "、".join(neg[:5])))

    # 5. <d> 标签闭合
    open_count = text.count("<d>")
    close_count = text.count("</d>")
    if open_count != close_count:
        bad("P6 台词标签", "<d> 与 </d> 数量不一致：%d / %d" % (open_count, close_count))
    elif open_count:
        ok("P6 台词标签", "%d 组台词标签成对闭合" % open_count)

    # 6. 台词组必须带语言码，且语言码写完整语言名：<d>[Chinese] 原文</d>
    bodies = re.findall(r"<d(?:[^>]*)>(.*?)</d>", text, re.S)
    codes = [b.strip().split("]")[0].lstrip("[") for b in bodies
             if re.match(r"^\[[^\]]+\]", b.strip())]
    nolang = [b.strip()[:18] for b in bodies if not re.match(r"^\[[A-Za-z][A-Za-z-]*\]", b.strip())]
    shorts = [c for c in codes if c.strip().lower() in SHORT_LANG_CODES]
    if nolang:
        bad("P14 语言码", "%d 组台词缺 <d>[语言] 语言码：%s" % (len(nolang), "；".join(nolang[:3])))
    elif shorts:
        bad("P14 语言码", "语言码要写完整语言名（Chinese、English、Japanese…），短码模型侧不认：%s"
            % "、".join(sorted(set(shorts))))
    elif bodies:
        ok("P14 语言码", "%d 组台词都带完整语言名" % len(bodies))

    # 7. 说话人编号按首次发声顺序分配 (S1)(S2)…
    labels = re.findall(r"\(S(\d+)\)", text)
    if labels:
        seen = []
        err = None
        for n in labels:
            v = int(n)
            if v not in seen:
                if v != len(seen) + 1:
                    err = "说话人编号必须按首次发声顺序从 (S1) 连续分配，实际首次出现 (S%d)，此前只有 %d 个说话人" % (
                        v, len(seen))
                    break
                seen.append(v)
        if err:
            bad("P13 说话人", err)
        else:
            ok("P13 说话人", "%d 位说话人编号 (S1)…(S%d) 按首次发声顺序分配" % (len(seen), len(seen)))
    else:
        if bodies:
            bad("P13 说话人", "有台词但没有 (S1)(S2) 说话人标号；同一人跨镜沿用原编号")
        else:
            ok("P13 说话人", "无台词，跳过说话人编号")

    # 8. 音频账：用了 <Audio N> 就必须在保留分析里有一条带保留关系的记录
    aud_nums = sorted({int(n) for n in re.findall(r"<Audio\s+(\d+)>", text)})
    if aud_nums:
        ledger = [ln for ln in text.splitlines() if any(k in ln for k in AUDIO_RETENTION)]
        unledged = [n for n in aud_nums
                    if not any(re.search(r"<Audio\s+%d>" % n, ln) for ln in ledger)]
        if unledged:
            bad("P19 音频账", "<Audio %s> 在保留分析里没有对应行；音频必须写清用在哪个主体、"
                "保留关系是 fully_copy／partially_copy／reference／weak_reference"
                % "、".join(str(n) for n in unledged))
        else:
            ok("P19 音频账", "%d 条音频都写了保留关系" % len(aud_nums))

    # 9. 图片绑定：用了 <Picture N> 就必须在同一行写明它对应哪个 <Subject N>
    pic_nums = sorted({int(n) for n in re.findall(r"<Picture\s+(\d+)>", text)})
    if pic_nums:
        unbound = [n for n in pic_nums
                   if not any(re.search(r"<Picture\s+%d>" % n, ln)
                              and re.search(r"<Subject\s+\d+>", ln)
                              for ln in text.splitlines())]
        if unbound:
            bad("P20 图片绑定", "<Picture %s> 没写明对应哪个 <Subject N>；每张图都要有一句"
                "「<Subject N> 取 <Picture M> 的外形／空间／站位」，不许按上传顺序默认配对"
                % "、".join(str(n) for n in unbound))
        else:
            ok("P20 图片绑定", "%d 张图都写明了绑定对象" % len(pic_nums))

    # 10. 路线一致性：路线由用户选择与素材在时间轴上的作用共同决定，不能自相矛盾
    route = ""
    for k in ("FL2VA", "I2VA", "L2VA", "Ref2VA", "T2VA"):
        if re.search(k, text):
            route = k
            break
    if not route:
        if re.search(r"多参|多参考", text):
            route = "Ref2VA"
        elif re.search(r"reference generation", text):
            route = "Ref2VA"
        elif re.search(r"首帧|尾帧|硬帧", text):
            route = "I2VA"
        elif re.search(r"首尾帧", text):
            route = "FL2VA"
    hard_frame_words = []
    for m in re.finditer(r"(硬首帧|硬尾帧|硬帧|首帧|尾帧)", text):
        prefix = text[max(0, m.start() - 8):m.start()]
        if re.search(r"(不|非|禁止|无需|不用|别|无)", prefix):
            continue  # 「不做首帧锁定」「不作为硬帧」这类否定表述不算违规
        hard_frame_words.append(m.group(1))
    if route in ("I2VA", "L2VA") and len(pic_nums) > 1:
        bad("P22 路线一致", "路线写 %s（单张硬帧），却引用了 %d 张 <Picture N>；"
            "多张参考图应走 Ref2VA，要硬帧就把多余的图移出时间轴" % (route, len(pic_nums)))
    elif route == "FL2VA" and len(pic_nums) > 2:
        bad("P22 路线一致", "路线写 FL2VA（首尾各一张），却引用了 %d 张 <Picture N>" % len(pic_nums))
    elif route in ("Ref2VA", "T2VA") and hard_frame_words:
        bad("P22 路线一致", "路线是多参考／文生视频，正文却出现「%s」；多参里图只锁外形与空间，"
            "不占时间轴，要硬帧请改走 I2VA／L2VA／FL2VA 并说明" % "、".join(sorted(set(hard_frame_words))))
    elif route:
        ok("P22 路线一致", "路线 %s 与素材用法一致" % route)


def self_test():
    data = {
        "shots": [
            {"number": 1, "duration": 3.0, "shotSize": "近景", "camera": "固定机位",
             "dialogue": "你早就知道了。", "characterNames": ["沈砚"], "sceneName": "柴房"},
            {"number": 2, "duration": 4.0, "shotSize": "特写", "camera": "缓慢推近",
             "dialogue": "", "characterNames": ["沈砚", "苏晚"], "sceneName": "柴房"},
        ],
        "assets": {"characters": ["沈砚", "苏晚"], "scenes": ["柴房"], "props": [], "voices": []},
    }
    prompt = """integrated_multimodal_description:
本段总长约 7 秒。
[Shot 1] At 00:00.000, A middle-aged man in a grey robe stands by the door.
(S1) 中年男子，声音低：<d>[Chinese] 你早就知道了。</d>
[Shot 2] At 00:03.000, a close-up of a young woman's wrist.
overall_soundscape:
门外雨声。
non_diegetic_music:
无。"""
    check_storyboard(data)
    check_prompt(prompt, ["沈砚", "苏晚"])
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for level, _, _ in RESULT:
        counts[level] += 1
    if counts["FAIL"]:
        print("自检未通过：", counts)
        for lvl, gate, msg in RESULT:
            if lvl != "PASS":
                print("  ", lvl, gate, msg)
        return 1

    # 每条新检查都要有一个反例，否则就是"看起来查了、其实没查"
    cases = [
        ("首镜 00:00.000 不得被当成镜长过短",
         "[Shot 1] At 00:00.000, 近景。\n[Shot 2] At 00:02.500, 特写。\nintegrated_multimodal_description:\n本段总长约 5 秒。\noverall_soundscape:\nnone\nnon_diegetic_music:\nnone",
         None, None, lambda r: not any(l != "PASS" and "镜长" in g for l, g, _ in r)),
        ("畸形时间码 00:001.200 必须拦下",
         "[Shot 1] At 00:00.000, 近景。\n[Shot 2] At 00:001.200, 特写。",
         None, "P3 时间码格式", None),
        ("6.5 秒单镜必须拦下",
         "[Shot 1] At 00:00.000, 近景。\n[Shot 2] At 00:06.500, 特写。",
         None, "P7 镜长", None),
        ("多段输出每段从 00:00.000 重算必须放行",
         "integrated_multimodal_description:\n本段总长约 6 秒。\n[Shot 1] At 00:00.000, 近景。\n[Shot 2] At 00:03.000, 特写。\noverall_soundscape:\nx\nnon_diegetic_music:\ny\n\nintegrated_multimodal_description:\n本段总长约 6 秒。\n[Shot 1] At 00:00.000, 近景。\n[Shot 2] At 00:03.000, 特写。\noverall_soundscape:\nx\nnon_diegetic_music:\ny",
         None, None, lambda r: not any(l == "FAIL" and ("P3" in g or "P7" in g or "P2" in g) for l, g, _ in r)),
        ("缺 non_diegetic_music 必须拦下",
         "overall_soundscape:\nx\n[Shot 1] At 00:00.000, 近景。\nintegrated_multimodal_description:\n本段总长约 4 秒。",
         None, "P11 字段结构", None),
        ("末镜 6.5 秒必须拦下",
         "integrated_multimodal_description:\n本段总长约 9.5 秒。\n[Shot 1] At 00:00.000, 近景。\n[Shot 2] At 00:03.000, 特写。\noverall_soundscape:\nx\nnon_diegetic_music:\ny",
         None, "P12 末镜长", None),
        ("有台词没 (S1) 必须拦下",
         "integrated_multimodal_description:\n本段总长约 6 秒。\n[Shot 1] At 00:00.000, 近景。\n<d>[Chinese] 你回来了。</d>\noverall_soundscape:\nx\nnon_diegetic_music:\ny",
         None, "P13 说话人", None),
        ("<d> 缺语言码必须拦下",
         "integrated_multimodal_description:\n本段总长约 6 秒。\n[Shot 1] At 00:00.000, 近景。\n(S1) 女子：<d>你回来了。</d>\noverall_soundscape:\nx\nnon_diegetic_music:\ny",
         None, "P14 语言码", None),
        ("两个主色色值必须拦下",
         "integrated_multimodal_description:\n本段总长约 6 秒。主色 `#5A4A63` 与 `#FF8A3D`。\n[Shot 1] At 00:00.000, 近景。\noverall_soundscape:\nx\nnon_diegetic_music:\ny",
         None, "P15 主色", None),
        ("法相比例 1.0 倍必须拦下",
         "integrated_multimodal_description:\n本段总长约 8 秒。身后浮起金身法相，高约本体 1.0 倍。\n[Shot 1] At 00:00.000, 近景。\noverall_soundscape:\nx\nnon_diegetic_music:\ny",
         None, "P16 法相比例", None),
        ("无光门写光晕必须拦下",
         "integrated_multimodal_description:\n本段总长约 6 秒。剑身泛起冷白光晕。\n[Shot 1] At 00:00.000, 近景。\noverall_soundscape:\nx\nnon_diegetic_music:\ny",
         "独孤九剑", "P17 无光门", None),
        ("没有 [Shot N] 时间线必须拦下",
         "integrated_multimodal_description:\n本段总长约 6 秒，大雨中的废墟。\noverall_soundscape:\nx\nnon_diegetic_music:\ny",
         None, "P21 时间线", None),
        ("多参路线里写硬首帧必须拦下",
         "subject_definitions:\n<Subject 1> 女子，取 <Picture 1> 的外形。\n<Subject 2> 场景，取 <Picture 2> 的空间。\nsummary:\nreference generation。以 <Picture 2> 为硬首帧。\nretention_analysis:\n<Subject 1> partially_preserved：出场。\n<Picture 1> partially_preserved：外形。\n<Picture 2> partially_preserved：空间。\ndetailed_description:\n本段总长约 6 秒。\n[Shot 1] At 00:00.000, 近景。\noverall_soundscape:\nx\nnon_diegetic_music:\ny",
         None, "P22 路线一致", None),
        ("语言码写短码 zh 必须拦下",
         "integrated_multimodal_description:\n本段总长约 6 秒。\n[Shot 1] At 00:00.000, 近景。\n(S1) 男子：<d>[zh] 你回来了。</d>\noverall_soundscape:\nx\nnon_diegetic_music:\ny",
         None, "P14 语言码", None),
        ("<Audio 1> 在保留分析里没账必须拦下",
         "subject_definitions:\n<Subject 1> 男子，取 <Picture 1> 外形，<Audio 1> 音色。\nsummary:\nreference generation。\nretention_analysis:\n<Subject 1> partially_preserved：出场。\n<Picture 1> partially_preserved：外形。\ndetailed_description:\n本段总长约 6 秒。\n[Shot 1] At 00:00.000, 近景。\noverall_soundscape:\nx\nnon_diegetic_music:\ny",
         None, "P19 音频账", None),
        ("<Picture 1> 没写绑定对象必须拦下",
         "subject_definitions:\n<Subject 1> 男子，深灰长衫。\nsummary:\nreference generation。\nretention_analysis:\n<Subject 1> partially_preserved：出场。\ndetailed_description:\n本段总长约 6 秒。\n[Shot 1] At 00:00.000, 近景，<Picture 1> 里的人物走入。\noverall_soundscape:\nx\nnon_diegetic_music:\ny",
         None, "P20 图片绑定", None),
        ("首镜不写 At 时镜长按切点递推，不得从 0 秒重算",
         "integrated_multimodal_description:\n本段总长约 15 秒。\n[Shot 1] 开场。\n[Shot 2] At 00:03.200, 切。\n[Shot 3] At 00:07.400, 再切。\n[Shot 4] At 00:11.600, 收。\noverall_soundscape:\nx\nnon_diegetic_music:\ny",
         None, None,
         lambda r: not any(l == "FAIL" and ("P7" in g or "P12" in g or "P8" in g) for l, g, _ in r)),
        ("中文六段不得被「主体定义」拆成两段",
         "主体定义:\n<Subject 1> 男子。\n摘要:\nx\n保留分析:\ny\n详细描述:\n本段总长约 6 秒。\n[Shot 1] At 00:00.000, 近景。\n[Shot 2] At 00:03.000, 特写。\n整体声景:\nx\n非叙事配乐:\ny",
         None, None, lambda r: not any("第2段" in msg for _, _, msg in r)),
    ]
    for name, bad_text, method, expect_gate, expect_clean in cases:
        RESULT.clear()
        check_prompt(bad_text, [], method)
        if expect_clean is not None:
            if not expect_clean(RESULT):
                print("自检未通过：", name)
                for lvl, gate, msg in RESULT:
                    if lvl != "PASS":
                        print("  ", lvl, gate, msg)
                return 1
        elif not any(lvl == "FAIL" and expect_gate in gate for lvl, gate, _ in RESULT):
            print("自检未通过：", name)
            for lvl, gate, msg in RESULT:
                if lvl != "PASS":
                    print("  ", lvl, gate, msg)
            return 1

    RESULT.clear()
    check_storyboard(data)
    check_prompt(prompt, ["沈砚", "苏晚"])
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for level, _, _ in RESULT:
        counts[level] += 1
    if counts["FAIL"]:
        print("自检未通过：", counts)
        return 1
    print("自检通过：", counts)
    return 0


def main():
    ap = argparse.ArgumentParser(description="ai-short-drama 交付自检")
    ap.add_argument("storyboard", nargs="?", help="分镜 JSON 路径")
    ap.add_argument("--prompt", help="H3 视频提示词正文路径（.txt/.md）")
    ap.add_argument("--names", help="角色名，逗号分隔（没有分镜 JSON 时用）")
    ap.add_argument("--method", help="武功名，用于查无光门／不给暖点门的专属约束")
    ap.add_argument("--self-test", action="store_true", help="跑内置样例，确认脚本可用")
    ap.add_argument("--quiet", action="store_true", help="只打印 FAIL/WARN")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    if not args.storyboard and not args.prompt:
        ap.print_help()
        return 0

    names = []
    if args.storyboard:
        with open(args.storyboard, encoding="utf-8") as f:
            data = json.load(f)
        check_storyboard(data)
        names = list((data.get("assets") or {}).get("characters") or [])
    if args.names:
        names = [n.strip() for n in args.names.split(",") if n.strip()]
    if args.prompt:
        with open(args.prompt, encoding="utf-8") as f:
            check_prompt(f.read(), names, args.method)

    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for level, gate, msg in RESULT:
        counts[level] += 1
        if args.quiet and level == "PASS":
            continue
        icon = {"PASS": "✓", "WARN": "!", "FAIL": "✗"}[level]
        print("%s %s — %s" % (icon, gate, msg))

    print("\n合计：通过 %d，警告 %d，阻断 %d" % (counts["PASS"], counts["WARN"], counts["FAIL"]))
    if counts["FAIL"]:
        print("存在阻断项，先修完再交付。")
        return 1
    if counts["WARN"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
