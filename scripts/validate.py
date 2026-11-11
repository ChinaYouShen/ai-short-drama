#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai-short-drama 交付自检

按本技能包自己的字段约定做确定性检查，不依赖任何第三方库，也不读外部 schema。
只查能被机器判定的事：时间码、发声窗口、编号绑定、景别与运镜枚举、正文角色名。
不能机器判定的（表演质量、情绪是否成立、构图是否好看）明确不做，不要指望它替人做美学判断。

用法：

    # 只查分镜 JSON
    python3 scripts/validate.py storyboard.json

    # 同时查 H3 视频提示词正文
    python3 scripts/validate.py storyboard.json --prompt prompt.txt

    # 没有分镜 JSON，只查提示词，并给出角色名清单
    python3 scripts/validate.py --prompt prompt.txt --names 沈砚,苏晚

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
SEGMENT_MAX_SECONDS = 15.0      # 单段生成上限
MIN_CUT_SECONDS = 2.0
MAX_CUT_SECONDS = 5.0
TIMECODE_TOLERANCE = 0.05       # 秒

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
            "。按顺序处理：删装饰动作 → 并行 → 单注意中心 → 报冲突拆分")
    else:
        ok("S9 口播预算", "有台词的镜头均在发声窗口内（按 %.1f 字/秒）" % SPEECH_CHARS_PER_SEC)


def check_prompt(text, names):
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

    # 2. [Shot N] 连续
    shot_nums = [int(m) for m in re.findall(r"\[Shot\s+(\d+)\]", text)]
    if shot_nums:
        if shot_nums == list(range(1, len(shot_nums) + 1)) or shot_nums[0] == 1 and sorted(set(shot_nums)) == shot_nums:
            ok("P2 镜号", "提示词内 [Shot N] 顺序正常：%s" % shot_nums)
        else:
            bad("P2 镜号", "[Shot N] 不连续：%s" % shot_nums)
    else:
        warn("P2 镜号", "提示词内没有 [Shot N] 标记，跳过")

    # 3. 时间码：格式 / 起点 / 递增 / 镜长
    #    先抓所有 At 后的记号，格式不合规的一条不留地报出来——不能因为正则匹配不上就静默跳过。
    raw_tcs = re.findall(r"At\s+([0-9][0-9:.]*)", text)
    malformed = [t for t in raw_tcs if not re.match(r"^\d{2}:\d{2}\.\d{3}$", t)]
    if malformed:
        bad("P3 时间码格式", "At 后的时间码必须是 mm:ss.mmm（两位分、两位秒、三位毫秒），以下不合规：%s"
            % "、".join(malformed[:6]))
    tcs = [t for t in raw_tcs if t not in malformed]
    if tcs:
        vals = [parse_tc(t) for t in tcs]
        if any(b <= a for a, b in zip(vals, vals[1:])):
            bad("P3 时间码", "At 时间码未严格递增：%s" % tcs)
        else:
            # 首镜写 At 必须是 00:00.000；没写时第一个 At 是第二镜起点，必须够一个最短镜长
            if vals[0] != 0 and vals[0] < MIN_CUT_SECONDS - TIMECODE_TOLERANCE:
                bad("P3 时间码", "首镜没写 At 时，第一个 At（%s）就是第二镜起点，必须 ≥ %.0fs"
                    % (tcs[0], MIN_CUT_SECONDS))
            else:
                ok("P3 时间码", "%d 个 At 时间码递增正常，起点 %s" % (len(tcs), tcs[0]))

        # 镜长：首镜写了 At 就看相邻差值；没写就把第一个 At 值本身当首镜长
        durations = [b - a for a, b in zip(vals, vals[1:])] if vals[0] == 0 else list(vals)
        bad_du = []
        for i, d in enumerate(durations):
            if d < MIN_CUT_SECONDS - TIMECODE_TOLERANCE:
                bad_du.append("第%d镜 %.1fs < %.0fs" % (i + 1, d, MIN_CUT_SECONDS))
            elif d > MAX_CUT_SECONDS + TIMECODE_TOLERANCE:
                bad_du.append("第%d镜 %.1fs > %.0fs" % (i + 1, d, MAX_CUT_SECONDS))
        if bad_du:
            bad("P7 镜长", "单镜必须 %.0f～%.0f 秒：%s" % (MIN_CUT_SECONDS, MAX_CUT_SECONDS, "；".join(bad_du)))
        elif durations:
            ok("P7 镜长", "可推算的 %d 段镜长都在 %.0f～%.0f 秒内" % (len(durations), MIN_CUT_SECONDS, MAX_CUT_SECONDS))
    else:
        warn("P3 时间码", "提示词内没有 At 时间码，跳过")

    # 4. 参考编号不跳号、连续
    for tag in ("Picture", "Video", "Audio", "Subject"):
        refs = [int(m) for m in re.findall(r"<%s\s+(\d+)>" % tag, text)]
        if not refs:
            continue
        uniq = sorted(set(refs))
        if uniq != list(range(1, len(uniq) + 1)):
            bad("P4 编号", "<%s N> 编号跳号或不从 1 起：%s" % (tag, uniq))
        else:
            ok("P4 编号", "<%s N> 共 %d 个，编号连续" % (tag, len(uniq)))

    # 5. 否定式动作粗筛
    neg = re.findall(r"(没有[^，。；]{1,6}|没[^\u4e00-\u9fa5]?(?:接话|按下去|看|动|说话)|不去看|不看他|不看她)", text)
    if neg:
        warn("P5 否定式动作", "疑似否定式动作 %d 处（画面生成不了「没发生的事」，改写成替代动作）：%s" % (
            len(neg), "、".join(neg[:5])))

    # 6. <d> 标签闭合
    open_count = text.count("<d>")
    close_count = text.count("</d>")
    if open_count != close_count:
        bad("P6 台词标签", "<d> 与 </d> 数量不一致：%d / %d" % (open_count, close_count))
    elif open_count:
        ok("P6 台词标签", "%d 组台词标签成对闭合" % open_count)

    # 7. 单段总时长 ≤ 15 秒（动作 + 台词合计），必须有可核对的时长声明
    decl = None
    m = re.search(r"(?:本段|全段|整段)?总[时長长]约?\s*([0-9]+(?:\.[0-9]+)?)\s*秒", text)
    if not m:
        m = re.search(r"Total duration[^0-9]{0,12}([0-9]+(?:\.[0-9]+)?)", text, re.I)
    if m:
        decl = float(m.group(1))
    if decl is None:
        warn("P8 段长", "正文没有「总时长 X 秒」声明，无法确认单段 ≤%.0f 秒；多段时每段都要声明"
             % SEGMENT_MAX_SECONDS)
    elif decl > SEGMENT_MAX_SECONDS + 1e-6:
        bad("P8 段长", "本段总时长 %.1fs 超过单段上限 %.0fs，必须拆段并让每段各自 ≤%.0fs"
            % (decl, SEGMENT_MAX_SECONDS, SEGMENT_MAX_SECONDS))
    else:
        # 末镜起点不应晚于声明总时长
        last_tc = tcs[-1] if tcs else None
        if last_tc and parse_tc(last_tc) >= decl:
            bad("P8 段长", "末镜起点 %s 已不早于声明总时长 %.1fs，时间轴与声明对不上" % (last_tc, decl))
        else:
            ok("P8 段长", "声明总时长 %.1fs，在单段上限 %.0fs 内" % (decl, SEGMENT_MAX_SECONDS))

    # 8. 台词容量：可发声字数 ÷ 4.1 必须放得进本段时间
    lines = re.findall(r"<d(?:[^>]*)>(.*?)</d>", text, re.S)
    if decl is not None and lines:
        spoken = 0
        for seg in lines:
            body_d = re.sub(r"^\[[^\]]*\]", "", seg.strip())   # 去掉 [zh] 语言码
            spoken += audible_chars(body_d)
        need = spoken / SPEECH_CHARS_PER_SEC
        if need > decl + 0.05:
            bad("P9 台词容量", "台词 %d 字按 %.1f 字/秒需 %.1f 秒，超过本段 %.1f 秒；精简台词或拆段"
                % (spoken, SPEECH_CHARS_PER_SEC, need, decl))
        elif need > SEGMENT_MAX_SECONDS:
            bad("P9 台词容量", "台词需 %.1f 秒，超过单段上限 %.0fs，必须拆段" % (need, SEGMENT_MAX_SECONDS))
        else:
            ok("P9 台词容量", "台词 %d 字约 %.1fs，放得进 %.1fs 的本段" % (spoken, need, decl))
            # 密度：说话占掉整段就没有走位与反应的时间，实写预算上限约 2.9 字/秒
            if need / decl > 0.71:
                warn("P10 台词密度", "台词占本段 %.0f%% 时间（%.1f 字/秒），没给表演留空；"
                     "10/12/15 秒的实写预算是 20～28 / 28～36 / 36～44 字" % (need / decl * 100, spoken / decl))


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
    prompt = """本段总长约 7 秒。
[Shot 1] A middle-aged man in a grey robe stands by the door.
<d>[Chinese] 你早就知道了。</d>
[Shot 2] At 00:03.000, a close-up of a young woman's wrist.
<Picture 1> reference for the woman's face."""
    check_storyboard(data)
    check_prompt(prompt, ["沈砚", "苏晚"])

    # 回归 1：首镜写 At 00:00.000 是正常起点，不得被当成「首镜过短」而报警
    RESULT.clear()
    check_prompt("[Shot 1] At 00:00.000, 近景，人站在门口。\n[Shot 2] At 00:03.200, 特写。", [])
    if any("首个 At" in msg or "第二镜起点" in msg for lvl, _, msg in RESULT if lvl != "PASS"):
        print("自检未通过：首镜起点 00:00.000 被误判为镜长过短")
        return 1

    # 回归 2：畸形时间码必须报阻断，不能被正则静默放过
    RESULT.clear()
    check_prompt("[Shot 1] At 00:00.000, 近景。\n[Shot 2] At 00:001.200, 特写。", [])
    if not any(lvl == "FAIL" and "时间码格式" in gate for lvl, gate, _ in RESULT):
        print("自检未通过：畸形时间码 00:001.200 未被拦下")
        return 1

    # 回归 3：单镜超过 5 秒必须报阻断
    RESULT.clear()
    check_prompt("[Shot 1] At 00:00.000, 近景。\n[Shot 2] At 00:06.500, 特写。", [])
    if not any(lvl == "FAIL" and "镜长" in gate for lvl, gate, _ in RESULT):
        print("自检未通过：6.5 秒单镜未被拦下")
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
            check_prompt(f.read(), names)

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
