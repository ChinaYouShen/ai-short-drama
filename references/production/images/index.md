# 图片提示词索引

图片提示词与视频提示词分开生成。用户可以只做图片提示词，也可以跳过图片直接进入 H3；当前只读取选定的图片模块。

| 目标 | 模块 |
| --- | --- |
| 角色三视图与面部特写 | [character.md](character.md) |
| 角色面部、三视图与局部细节 | [character-detail.md](character-detail.md) |
| 道具设定图 | [prop.md](prop.md) |
| 场景主图、四向视图或平面图 | [scene.md](scene.md) |
| 站位主图 | [standing.md](standing.md) |
| 角色空间占位润色、多角度场景润色 | [polish.md](polish.md) |
| 分镜静帧 | [frame.md](frame.md) |
| 外部图片生成任务 | [runner.md](runner.md) |

用户可选择中文、英文或跟随输入。只输出图片提示词时不写视频字段、时间轴或运镜过程。所有参考图编号、资产名称和用途沿用用户提供的清单。
