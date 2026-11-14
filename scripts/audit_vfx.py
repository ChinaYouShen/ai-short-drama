#!/usr/bin/env python3
"""特效主体体检：检查武戏参数表里每一招是否都有可画的「特效主体」。

用法：python3 scripts/audit_vfx.py [--quiet]
退出码 0 表示全部合格，1 表示有问题。

判定一个条目合格的四条（外加破坏三栏，见 check_damage）：
1. 非空，且不以「无」「没有」开头（无光招式也必须给空气锥、尘环这类可见物件）。
2. 长度 ≥ 8 字，避免只写「线状」「面状掌印」这种形状名。
3. 含体量或轨迹线索：数字、「长约/高约/直径」、或运动动词（贯穿、推进、盘旋、收束…）。
4. 同一文件内不与其他招式完全重复（同体系多招共用一套特效，观众分不出是哪招）。
5. 表头关键词必须真的匹配到行；匹配不到即报错，不允许静默跳过（否则整份文件等于没查）。
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 招式表：(文件, 表头关键词, 招式列, 特效列, 打击面列)
TABLES = [
    ("references/wuxi/catalog/jinyong/misc-early.md", "能源形态", 0, 2, 5),
    ("references/wuxi/catalog/jinyong/misc-mid.md", "能源形态", 0, 2, 5),
    ("references/wuxi/catalog/jinyong/shediao.md", "能源形态", 0, 2, 5),
    ("references/wuxi/catalog/jinyong/tianlong.md", "能源形态", 0, 2, 5),
    ("references/wuxi/catalog/jinyong/xiaoao.md", "能源形态", 0, 2, 5),
    ("references/wuxi/catalog/gulong.md", "光形 / 粒子", 0, 2, None),
    ("references/wuxi/catalog/liangyusheng.md", "光形 / 粒子", 0, 2, None),
    ("references/wuxi/catalog/wenyuan.md", "光形 / 粒子", 0, 2, None),
    ("references/wuxi/ultimate/cases/saint-seiya.md", "特效主体与轨迹", 1, 6, 3),
    ("references/wuxi/ultimate/cases/xianglong.md", "龙形动作", 1, 2, 7),
]

MOTION = ("贯穿", "推进", "盘旋", "收束", "扩散", "合拢", "塌缩", "下压", "横扫", "折返",
          "上升", "升起", "下劈", "斜劈", "横贯", "绕身", "前推", "平推", "拖", "射", "飞",
          "落", "攀升", "回旋", "收拢", "弹出", "掠过", "切入", "爬", "卷", "流动", "流转",
          "锁定", "张开", "展开", "炸", "崩", "顶", "扫", "掠", "窜", "贴", "夹", "压", "劈",
          "推", "散", "沉", "降", "刺", "缠", "绕", "甩", "挑", "削", "切", "撞", "震", "爆",
          "拖出", "拧", "折", "交织", "错位", "扩散", "聚", "涌", "喷", "吸", "缠住")
QUANT = ("道", "枚", "条", "片", "根", "束", "圈", "层", "重", "截", "团", "簇", "股", "个", "张", "面", "柄", "把")
SIZE = ("长约", "高约", "直径", "长约", "宽约", "长", "高", "米", "身位", "倍", "尺", "寸", "覆盖")
EMPTY = ("无", "没有", "—", "-")


def _blocks(lines):
    """把连续的表格行切成块：(表头, 分隔行, 数据行列表)。"""
    blocks, cur = [], []
    for line in lines:
        if line.startswith("|"):
            cur.append(line)
        elif cur:
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    out = []
    for b in blocks:
        if len(b) < 2:
            continue
        cells = [c.strip() for c in b[1].strip("|").split("|")]
        if not all(re.fullmatch(r"[-: ]*", c) for c in cells):
            continue
        out.append((b[0], b[1], b[2:]))
    return out


def _col_index(header, name):
    cells = _cells(header)
    for i, c in enumerate(cells):
        if c == name:
            return i
    return None


def _looks_destroyed(text):
    """破坏三栏：人：…／物：…／景：… 三段都要有具体后果，不许只写「轰然」「碎裂」这种空词。"""
    if not text:
        return "空字段"
    parts = text.replace("|", "／").split("／")
    labels = {"人": False, "物": False, "景": False}
    bodies = {}
    for part in parts:
        part = part.strip()
        for k in labels:
            if part.startswith(k + "："):
                labels[k] = True
                bodies[k] = part.split("：", 1)[1].strip()
    missing = [k for k, v in labels.items() if not v]
    if missing:
        return "缺「%s」这一栏" % "、".join(missing)
    if all(v in ("无", "无。", "不适用") for v in bodies.values()):
        return "三栏全写「无」，等于没写破坏"
    thin = [k for k, v in bodies.items() if v not in ("无", "无。", "不适用") and len(v) < 3]
    if thin:
        return "「%s」只写了两个字，没有具体后果" % "、".join(thin)
    return None


def check_damage(path, header_word, damage_col="破坏（人／物／景）", extra=()):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return []
    issues, seen_col, total = [], False, 0
    for header, _sep, data in _blocks(open(full, encoding="utf-8").read().splitlines()):
        if header_word not in header:
            continue
        cells_h = _cells(header)
        idx = _col_index(header, damage_col)
        if idx is None:
            for name in extra:
                if name not in cells_h:
                    issues.append((path.split("/")[-1], "表头没有「%s」，破坏后果无处可写" % name))
                else:
                    seen_col = True
            continue
        seen_col = True
        n = len(cells_h)
        for line in data:
            cells = _cells(line)
            if len(cells) != n:
                continue
            total += 1
            why = _looks_destroyed(cells[idx])
            if why:
                issues.append((cells[0], why))
            death = [w for w in ("死亡", "毙命", "气绝", "断气", "暴毙") if w in cells[idx]]
            if death:
                issues.append((cells[0], "参数表里写了「%s」；表只写命中后的破坏上限，生死属剧情结果，"
                                "放进分镜并加命中条件" % "、".join(death)))
    if not seen_col and not issues:
        issues.append((path.split("/")[-1], "破坏列「%s」未匹配到任何行" % damage_col))
    return issues


def _cells(line):
    return [c.strip() for c in line.strip("|").split("|")]


def rows(path, header_word, move_col, vfx_col, face_col=None):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return None
    out = []
    for header, _sep, data in _blocks(open(full, encoding="utf-8").read().splitlines()):
        if header_word not in header:
            continue
        n = len(_cells(header))
        for line in data:
            cells = _cells(line)
            if len(cells) != n:
                continue
            face = cells[face_col] if face_col is not None and face_col < len(cells) else None
            out.append((cells[move_col], cells[vfx_col], face))
    return out


def check(path, header_word, move_col, vfx_col, face_col=None):
    data = rows(path, header_word, move_col, vfx_col, face_col)
    if data is None:
        return []
    issues = []
    seen = {}
    faces = ("单", "群", "单·群", "群·区", "自", "区", "自·单", "自·群")
    for move, vfx, face in data:
        if face is not None and face not in faces:
            issues.append((move, "打击面写成「%s」，只允许 单／群／单·群／群·区／自／区／自·单／自·群" % face))
        if not vfx:
            issues.append((move, "空字段"))
            continue
        if vfx.startswith(EMPTY):
            issues.append((move, "以「无」开头，没有可见物件"))
        if len(vfx) < 8:
            issues.append((move, "只有形状名，没有体量与轨迹"))
        if not any(w in vfx for w in MOTION) and not any(s in vfx for s in SIZE) and not re.search(r"[一二两三四五六七八九十百千0-9]", vfx):
            issues.append((move, "没有体量或运动线索，画不出来"))
        seen.setdefault(vfx, []).append(move)
    for vfx, moves in seen.items():
        if len(moves) > 1:
            issues.append(("、".join(moves), "同文件共用同一句特效描述「%s」" % vfx[:20]))
    return issues


CROSS = [
    ("references/wuxi/catalog/gulong.md", "打击面", "光形 / 粒子"),
    ("references/wuxi/catalog/liangyusheng.md", "打击面", "光形 / 粒子"),
    ("references/wuxi/catalog/wenyuan.md", "打击面", "光形 / 粒子"),
]


def names_by(path, keyword, col=0):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return None
    out = []
    for header, _sep, data in _blocks(open(full, encoding="utf-8").read().splitlines()):
        if keyword not in _cells(header):
            continue
        n = len(_cells(header))
        for line in data:
            cells = _cells(line)
            if len(cells) == n:
                out.append(cells[col])
    return out


def main():
    quiet = "--quiet" in sys.argv
    total_moves = 0
    total_issues = 0
    broken = []
    for path, hw, mc, vc, fc in TABLES:
        data = rows(path, hw, mc, vc, fc)
        if data is None:
            print("跳过（文件不存在）：", path)
            continue
        if not data:
            # 表头关键词对不上就是零条：以前会静默放行，等于这一份文件没查
            broken.append((path, hw))
            continue
        total_moves += len(data)
        issues = check(path, hw, mc, vc, fc)
        total_issues += len(issues)
        name = path.split("/")[-1]
        if issues:
            print("✗ %s（%d 条）" % (name, len(data)))
            if not quiet:
                for move, why in issues[:12]:
                    print("   - %s：%s" % (move, why))
        else:
            print("✓ %s（%d 条）全部有特效主体" % (name, len(data)))
    DAMAGE = [
        ("references/wuxi/catalog/jinyong/misc-early.md", "能源形态", "破坏（人／物／景）", ()),
        ("references/wuxi/catalog/jinyong/misc-mid.md", "能源形态", "破坏（人／物／景）", ()),
        ("references/wuxi/catalog/jinyong/shediao.md", "能源形态", "破坏（人／物／景）", ()),
        ("references/wuxi/catalog/jinyong/tianlong.md", "能源形态", "破坏（人／物／景）", ()),
        ("references/wuxi/catalog/jinyong/xiaoao.md", "能源形态", "破坏（人／物／景）", ()),
        ("references/wuxi/catalog/gulong.md", "能源形态", "破坏（人／物／景）", ()),
        ("references/wuxi/catalog/liangyusheng.md", "能源形态", "破坏（人／物／景）", ()),
        ("references/wuxi/catalog/wenyuan.md", "能源形态", "破坏（人／物／景）", ()),
        ("references/wuxi/ultimate/cases/saint-seiya.md", "特效主体与轨迹", "破坏（人／物／景）", ()),
        ("references/wuxi/catalog/gulong.md", "光形 / 粒子", None, ("命中", "环境")),
        ("references/wuxi/catalog/liangyusheng.md", "光形 / 粒子", None, ("命中", "环境")),
        ("references/wuxi/catalog/wenyuan.md", "光形 / 粒子", None, ("命中", "环境")),
        ("references/wuxi/ultimate/cases/xianglong.md", "龙形动作", None, ("命中反馈", "环境反应")),
    ]

    for path, ikw, mkw in CROSS:
        idx = names_by(path, ikw)
        mov = names_by(path, mkw)
        if idx is None or mov is None:
            continue
        if set(idx) != set(mov) or len(idx) != len(mov):
            only_i = sorted(set(idx) - set(mov))
            only_m = sorted(set(mov) - set(idx))
            print("✗ %s：索引表与招式表名单不一致（只在索引：%s；只在招式表：%s）"
                  % (path.split("/")[-1], "、".join(only_i) or "无", "、".join(only_m) or "无"))
            total_issues += 1

    for path, hw, dcol, extra in DAMAGE:
        iss = check_damage(path, hw, dcol, extra) if dcol else check_damage(path, hw, "破坏（人／物／景）", extra)
        if iss:
            print("✗ %s：破坏三栏 %d 处问题" % (path.split("/")[-1], len(iss)))
            if not quiet:
                for who, why in iss[:12]:
                    print("   - %s：%s" % (who, why))
            total_issues += len(iss)

    if broken:
        for path, hw in broken:
            print("✗ %s：表头「%s」未匹配到任何行，这份文件等于没查" % (path.split("/")[-1], hw))
        total_issues += len(broken)
    print("合计：%d 条招式，%d 处问题" % (total_moves, total_issues))
    return 1 if total_issues else 0


if __name__ == "__main__":
    sys.exit(main())