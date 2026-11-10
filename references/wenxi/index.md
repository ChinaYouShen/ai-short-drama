# 文戏按需索引

## 先判断

从用户输入识别对白、表演重点、关系变化、在场人数、场景风格和分镜方式。用户已明确选择时直接沿用；任务意图清楚时直接路由，不重复追问。只有不同模块选择会改变成稿且无法从输入判断时，才询问侧重。

侧重和分镜方式都可以跳过。跳过时只加载能完成当前请求的模块，不用默认补齐未选的风格、人物关系或分镜类型。

可合并询问：`文戏侧重：对白 / 情绪表演 / 人物关系与潜台词 / 多人调度 / 独白与旁白 / 沉默反应 / 喜剧节奏 / 悬念揭示；分镜：单镜 / 多镜连续 / 续接。` 可多选。

## 按需读取

1. 读取 [flow.md](flow.md)。
2. 有实际对白时读取 [dialogue/dialogue.md](dialogue/dialogue.md)；声音身份或参考音频是重点时再读 [dialogue/voice.md](dialogue/voice.md)。
3. 按本段需要读取表演、关系、多人、独白、风格模块。
4. 按单镜、多镜或续接选择一个分镜模块。
5. 读取 [../cinematography.md](../cinematography.md)，应用人物景别与运镜要求。
6. 输出前读取 [validation.md](validation.md)。

## 模块路由

| 需求 | 模块 |
| --- | --- |
| 情绪变化、微表演 | [performance/emotion.md](performance/emotion.md) |
| 停顿、沉默、无对白反应 | [performance/silence.md](performance/silence.md) |
| 关系变化、冲突、潜台词 | [dynamics/relationship.md](dynamics/relationship.md) |
| 三人及以上的对话或多线反应 | [dynamics/ensemble.md](dynamics/ensemble.md) |
| 独白、画外音、内心表达 | [dialogue/monologue.md](dialogue/monologue.md) |
| 喜剧节奏 | [styles/comedy.md](styles/comedy.md) |
| 悬念、隐瞒、信息揭示 | [styles/suspense.md](styles/suspense.md) |
| 单镜 | [storyboard/single.md](storyboard/single.md) |
| 多镜连续 | [storyboard/sequence.md](storyboard/sequence.md) |
| 续接上一段 | [storyboard/continuation.md](storyboard/continuation.md) |

每次只加载当前需要的模块。未选风格模块不自动改变剧情、台词、人物动机或表演强度。
