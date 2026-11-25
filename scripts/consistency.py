#!/usr/bin/env python3
"""跨文档一致性检查：分镜 JSON 自身，以及与剧本的台词逐字对账。

用法：
    python3 scripts/consistency.py samples/storyboard_sample.json
    python3 scripts/consistency.py 分镜.json --script 第01集.md

只报事实，不改内容。任何一条 ERROR 都表示这份分镜不能直接进生产。
"""
import argparse
import json
import os
import re
import sys

SPEECH_CHARS_PER_SEC = 4.1
TIME_TOL = 0.06
MIN_SHOT = 2.0
MAX_SHOT = 5.0
MAX_PEOPLE = 3

PUNCT = re.compile(r"[\s，。！？、；：…—“”‘’（）()《》〈〉,.!?;:\"'·｜|]+")


def audible(text):
    return len(PUNCT.sub("", text or ""))


def to_seconds(tc):
    m = re.match(r"^(\d+):(\d+)(?:\.(\d+))?$", tc or "")
    if not m:
        return None
    frac = m.group(3) or "0"
    return int(m.group(1)) * 60 + int(m.group(2)) + float("0." + frac)


class Report:
    def __init__(self):
        self.errors = []
        self.warns = []

    def err(self, gate, msg):
        self.errors.append((gate, msg))

    def warn(self, gate, msg):
        self.warns.append((gate, msg))


def check(json_path, script_text, rep):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    shots = data.get("shots")
    if not isinstance(shots, list) or not shots:
        rep.err("C1 结构", "缺少 shots 数组或为空")
        return

    assets = data.get("assets") or {}
    chars = set(assets.get("characters") or [])
    scenes = set(assets.get("scenes") or [])
    props = set(assets.get("props") or [])

    # C1 字段
    required = ("number", "duration", "shotSize", "camera", "dialogue",
                "characterNames", "sceneName", "timecode")
    for i, sh in enumerate(shots, 1):
        missing = [k for k in required if k not in sh]
        if missing:
            rep.err("C1 结构", "第 %d 镜缺字段：%s" % (i, "、".join(missing)))

    # C2 镜号连续
    nums = [sh.get("number") for sh in shots]
    if nums != list(range(1, len(shots) + 1)):
        rep.err("C2 镜号", "镜号不是 1..%d 连续：%s" % (len(shots), nums))

    # C3 时间码连续，逐镜累加
    cursor = 0.0
    for i, sh in enumerate(shots, 1):
        tc = to_seconds(sh.get("timecode"))
        if tc is None:
            rep.err("C3 时间码", "第 %d 镜时间码格式不是 mm:ss.mmm：%r" % (i, sh.get("timecode")))
            continue
        if abs(tc - cursor) > TIME_TOL:
            rep.err("C3 时间码", "第 %d 镜起点 %.3fs，与上一镜结束 %.3fs 不连续" % (i, tc, cursor))
        cursor = tc + float(sh.get("duration") or 0)

    # C4 单镜时长
    for i, sh in enumerate(shots, 1):
        d = float(sh.get("duration") or 0)
        if d < MIN_SHOT or d > MAX_SHOT:
            rep.err("C4 镜长", "第 %d 镜 %.2fs，超出 %.0f～%.0f 秒" % (i, d, MIN_SHOT, MAX_SHOT))

    # C5 台词容量
    for i, sh in enumerate(shots, 1):
        line = sh.get("dialogue") or ""
        n = audible(line)
        if not n:
            continue
        d = float(sh.get("duration") or 0)
        need = n / SPEECH_CHARS_PER_SEC
        if need > d + 0.2:
            rep.err("C5 台词容量", "第 %d 镜 %d 个可发声字需 %.1fs，镜长只有 %.1fs" % (i, n, need, d))

    # C6 人物同框上限
    for i, sh in enumerate(shots, 1):
        people = sh.get("characterNames") or []
        if len(people) > MAX_PEOPLE:
            rep.err("C6 同框人数", "第 %d 镜 %d 人同框，超过 %d 人" % (i, len(people), MAX_PEOPLE))

    # C7 资产引用
    used_chars, used_scenes, used_props = set(), set(), set()
    for i, sh in enumerate(shots, 1):
        for name in sh.get("characterNames") or []:
            used_chars.add(name)
            if chars and name not in chars:
                rep.err("C7 资产引用", "第 %d 镜人物「%s」不在 assets.characters" % (i, name))
        scene = sh.get("sceneName")
        if scene:
            used_scenes.add(scene)
            if scenes and scene not in scenes:
                rep.err("C7 资产引用", "第 %d 镜场景「%s」不在 assets.scenes" % (i, scene))
        for name in sh.get("propNames") or []:
            used_props.add(name)
            if props and name not in props:
                rep.err("C7 资产引用", "第 %d 镜道具「%s」不在 assets.props" % (i, name))

    for name in sorted(chars - used_chars):
        rep.warn("C7 资产引用", "人物「%s」已建卡但整集没出场" % name)
    for name in sorted(scenes - used_scenes):
        rep.warn("C7 资产引用", "场景「%s」已建卡但整集没用" % name)
    for name in sorted(props - used_props):
        rep.warn("C7 资产引用", "道具「%s」已建卡但整集没出现" % name)

    # C8 与剧本台词逐字对账
    if script_text:
        plain_script = PUNCT.sub("", script_text)
        for i, sh in enumerate(shots, 1):
            line = sh.get("dialogue") or ""
            if not audible(line):
                continue
            if PUNCT.sub("", line) not in plain_script:
                rep.err("C8 台词逐字", "第 %d 镜台词在剧本里找不到原句：%s" % (i, line))
        rep.warn("C8 台词逐字", "已对照剧本 %d 字" % len(PUNCT.sub("", script_text)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_file")
    ap.add_argument("--script", default=None, help="分集剧本 Markdown，给定时逐字对账台词")
    args = ap.parse_args()

    if not os.path.exists(args.json_file):
        print("ERROR 文件不存在：%s" % args.json_file)
        return 2

    script_text = ""
    if args.script:
        if not os.path.exists(args.script):
            print("ERROR 剧本不存在：%s" % args.script)
            return 2
        with open(args.script, encoding="utf-8") as f:
            script_text = f.read()

    rep = Report()
    check(args.json_file, script_text, rep)

    for gate, msg in rep.errors:
        print("ERROR %s：%s" % (gate, msg))
    for gate, msg in rep.warns:
        print("WARN  %s：%s" % (gate, msg))
    if not rep.errors:
        print("通过 %d 项检查（%d 镜，%d 条提醒）" % (8, len(json.load(open(args.json_file, encoding="utf-8"))["shots"]), len(rep.warns)))
    print("结果：%s" % ("有 %d 处错误" % len(rep.errors) if rep.errors else "全部通过"))
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
