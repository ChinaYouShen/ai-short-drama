---
name: ai-short-drama
description: 按用户当前要的产物创建或检查短剧、漫剧、人物与场景资产、剧本、对白、钩子、分镜、图片提示词、H3 文戏武戏提示词；阶段可跳过，只加载当前任务需要的文件。关键词：短剧、漫剧、分镜、文戏、武戏、必杀技、H3 提示词、多参考 Ref2VA、首尾帧。
metadata:
  maintainer: YS
  language: zh-CN
---

# AI 短剧技能包

一句话：用户说要什么，按规矩写出来；要检查就只检查，不改写。

## 三条总原则

1. **只做当前要的产物**。用户要剧本，就只给剧本，不顺手把分镜做掉。
2. **缺环直说**。没有对应文件就说「这块没覆盖」，不用通用话术糊过去。
3. **不确定就只问一句**。只问会造成错误的缺项，一次问清，不追问风格偏好。

## 按任务读一个文件

| 用户要什么 | 读哪个 |
| --- | --- |
| 选题、大纲、人物、资产、剧本、对白、钩子、节奏、改编、漫剧、参考片反拆 | [references/guide.md](references/guide.md) |
| 挑毛病、打分、诊断某一处该不该改 | [references/review.md](references/review.md) |
| 分镜、镜头九问、跨镜承接、图片提示词 | [references/board.md](references/board.md) |
| H3 文戏武戏提示词、模型对照、多段拼接、镜头语言 | [references/prompt.md](references/prompt.md) |
| 文戏细则（对白、表演、关系、风格） | [references/wenxi/rules.md](references/wenxi/rules.md) |
| 算生成次数、素材上限、交付关卡、平台口径 | [references/cost.md](references/cost.md) |
| 武戏总则、动作配速、画面可生成性 | [references/wuxi/rules.md](references/wuxi/rules.md) |
| 特效总则、三类型五要素、破坏三栏 | [references/wuxi/vfx.md](references/wuxi/vfx.md) |
| 选门派、选招、查招式参数 | [references/wuxi/catalog/index.md](references/wuxi/catalog/index.md) |
| 查能力边界与未覆盖项 | [references/map.md](references/map.md) |

一次只读一个入口文件；该文件里再指向需要的子页。不要整包加载。

## 六条硬规矩（任何时候都不破）

1. **特效必须是能画出来的主体**：一条金龙、三道爪痕、一面冰墙；只写「耀眼的光」不通过。
2. **打中才写伤**：命中才写甲片崩、吐血、倒地；格挡、擦过、落空只写火花、兵器弯、退半步。
3. **台词按 4.1 字/秒算**，一镜一句，超了先拆句，不硬塞。
4. **单镜 2～5 秒，一镜一个主要动作**；超时先拆镜。
5. **不编原作招名**：原作没有就按意境给描述，不硬造。
6. **写提示词前先答「一镜九问」**，第 6、9 问答不出就不写。

## 用户不知道从哪一步开始时

先问一句「你现在手上有什么」，按结果只给下一步，不甩整套流程：

| 手上有的 | 下一步只做 |
| --- | --- |
| 一个想法或一句话 | 选题判断 + 一句话卖点 |
| 一本小说 | 改编幅度判断 + 人物卡 |
| 大纲 | 第 1 集剧本 |
| 剧本 | 分镜 + 九问 |
| 分镜 | 提示词 |
| 一条参考片 | 反拆表 |

一次只带一关；用户做完再说下一关，不要一次给完。

## 交付形态

默认：分段文字 + 必要表格 + 可整段粘贴的提示词；剧本一次最多交两集。用户要 JSON、应用载荷或指定格式时再转换，不主动输出 JSON。

## 交付前自检

一条命令跑完自检、样例和招式体检：

```bash
python3 scripts/check.py
```

只查某份提示词：

```bash
python3 scripts/validate.py --prompt 我的提示词.txt
```
