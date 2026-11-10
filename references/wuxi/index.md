# 武戏按需索引

## 可选设计参数

- `动作载体`：徒手、兵器、能力、位移、混合。
- `战斗人数`：单组交锋、多人交锋。
- `分镜方式`：单镜完成、多镜连续、续接上一段。

用户已明确的选项直接沿用。信息足以完成当前请求时不追问；只有缺失内容会改变动作因果或结果时，才提供简短选择。用户还可以指定目标、招式名、流派、兵器、能力、时长、结果和禁用动作。

动作载体、战斗人数和分镜方式都可以跳过。跳过时按用户已有动作或分镜直接处理，不自动添加载体、人数、招式、结果或镜头类型。

## 按需读取模块

用户要求必杀技、大招、喊招式、法相、能量特效、招式还原时，先读 [ultimate/index.md](ultimate/index.md) 判范式，再按其中路由取模块；必杀技以外的普通武戏不走这条。

动作设计读取 [flow.md](flow.md)，并只加载当前动作载体对应的模块。
制作分镜时读取 [storyboard/index.md](storyboard/index.md)，只加载选定的分镜方式。
H3 镜头应用 [../cinematography.md](../cinematography.md)；只有涉及跨镜、跨段或声音时才读取 [continuity.md](continuity.md) 或 [sound.md](sound.md)。
输出 H3 提示词前按 [validation.md](validation.md) 检查当前交付内容；用户只要求讨论或草拟招式时不要求先走完分镜流程。

## 选择与文件

| 用户选择 | 读取文件 |
| --- | --- |
| 徒手 | [moves/unarmed.md](moves/unarmed.md) |
| 兵器 | [moves/weapon.md](moves/weapon.md) |
| 能力 | [moves/ability.md](moves/ability.md) |
| 位移或轻功 | [moves/movement.md](moves/movement.md) |
| 混合载体 | 只读取被选中的两个或多个动作模块 |
| 单镜 | [storyboard/single.md](storyboard/single.md) |
| 多镜连续 | [storyboard/sequence.md](storyboard/sequence.md) |
| 续接 | [storyboard/continuation.md](storyboard/continuation.md) |
| 多人交锋 | [storyboard/multi.md](storyboard/multi.md) |
| 必杀技、大招、喊招、法相与能量特效 | [ultimate/index.md](ultimate/index.md) |
| 法相或幻影层 | [ultimate/aura.md](ultimate/aura.md) |
| 必杀技配色 | [ultimate/palette.md](ultimate/palette.md) |
| 连打、命中与收束 | [ultimate/finisher.md](ultimate/finisher.md) |
| 圣斗士星矢各角色招式参数 | [ultimate/cases/saint-seiya.md](ultimate/cases/saint-seiya.md) |

同一选择只读取一次。没有选择的动作、分镜和声音模块不参与当前请求。
