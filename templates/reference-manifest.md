# 参考素材清单模板

用户发来图片、视频或音频时，先填这张表，再写 H3 提示词。**表没填完不动笔**：编号一旦建立就全篇锁定，事后再补会出现「图和人对不上」这种无法验证的错误。

清单放在项目根目录，文件名 `reference-manifest.md`，三张表固定。

## 一、图片表

| 编号 | 类别 | 画面内容 | 用途 | 绑定主体 | 保留关系 |
| --- | --- | --- | --- | --- | --- |
| `<Picture 1>` | character | 深灰长衫中年男子，半身，正面 | 锁外形与服装 | `<Subject 1>` | partially_preserved |
| `<Picture 2>` | character | 黑色短打年轻女子，全身，侧身 | 锁外形与服装 | `<Subject 2>` | partially_preserved |
| `<Picture 3>` | scene | 雨夜窄巷，湿砖墙与铁皮雨棚 | 锁空间、积水与光位 | `<Subject 3>` | partially_preserved |
| `<Picture 4>` | standing | 两人相距两米，男右女左 | 锁左右与朝向 | 站位 | partially_preserved |

- 类别只有五种：`character`（人物）、`scene`（场景）、`prop`（道具）、`standing`（站位）、`reference`（其它参考）。
- **用途写作用，不写内容**：锁外形／锁服装／锁空间／锁站位／当 0.00 秒首帧／当末秒尾帧。
- 保留关系只填四个之一：`fully_preserved`、`partially_preserved`、`attribute_transfer`、`weak_reference`。
- 每行都要能让 `<Picture N>` 和 `<Subject N>` 出现在同一句里，例如「`<Subject 1>` 取 `<Picture 1>` 的外形」。只在表里绑、正文不写，脚本照样拦。

## 二、音频表

| 编号 | 类型 | 内容 | 用途 | 绑定主体 | 保留关系 |
| --- | --- | --- | --- | --- | --- |
| `<Audio 1>` | voice | 低沉稳男声一句台词 | 音色参考 | `<Subject 1>` 的声线 | reference |
| `<Audio 2>` | dialogue | 完整的「站住！」原句 | 对白复用 | 1 号镜头台词 | fully_copy |
| `<Audio 3>` | music | 低频鼓点主题 | 配乐参考 | `non_diegetic_music` | reference |

- 类型：`voice`（音色）、`dialogue`（对白）、`music`（配乐）、`sfx`（音效）、`ambience`（环境声）。
- 保留关系只填四个之一：`fully_copy`、`partially_copy`、`reference`、`weak_reference`。
- 对白复用与音色参考是两件事：只模仿音色时不要声称原句被沿用；整句沿用才写 `fully_copy`。

## 三、视频表

| 编号 | 用途 | 保留关系 | 说明 |
| --- | --- | --- | --- |
| `<Video 1>` | 镜头运动参考 | weak_reference | 只借运镜节奏，不复制画面 |
| `<Video 2>` | 续接源片 | partially_preserved | 从末态继续，不重演已完成动作 |

- 只有被改写的视频用 `video editing`；只有从末态继续才用 `video continuation`；只借节奏或运镜用 `reference generation`。

## 四、路线判定（填完表再勾一个）

| 判断 | 勾选 | 路线 |
| --- | --- | --- |
| 图只锁外形、空间，不占时间轴 | ☐ | Ref2VA 多参考 |
| 一张图是 0.00 秒硬首帧 | ☐ | I2VA |
| 一张图是末秒硬尾帧 | ☐ | L2VA |
| 两张图分别锁定开始与结束 | ☐ | FL2VA |
| 无图无音频，纯文字 | ☐ | T2VA |

路线由素材在时间轴上的作用决定，不由张数决定。图数、角色数、音频数三者可以互不相等：三张图两个角色、两段音频一个角色都是常态。

## 五、交付前自检

```bash
python3 scripts/validate.py --prompt 本段提示词.txt
```

清单里出现过的 `<Picture N>`／`<Audio N>`，正文与保留分析都要有对应行，否则脚本按 P19／P20 拦下。
