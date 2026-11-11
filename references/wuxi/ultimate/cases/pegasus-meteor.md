# 天马流星拳 · 完整样板

这一份是把 [../index.md](../index.md)、[../aura.md](../aura.md)、[../palette.md](../palette.md)、[../finisher.md](../finisher.md) 全部落到一个成品上：12 秒、5 镜、含完整 H3 提示词与三张出图提示词。改写其他招式时保持这个骨架，只替换设定卡。

## 设定卡

| 项 | 值 |
| --- | --- |
| 角色（正文用） | 一名身披青蓝色青铜圣衣、护肩带翼纹的少年 |
| 招式 | 天马流星拳 |
| 范式 | 连打型 |
| 主色 | 青蓝 `#4FC3F7` |
| 辅色 | 深蓝 `#1A4C8B` |
| 高光 | 近白蓝 `#EAF7FF` |
| 暖点 | 金 `#F5C542`，只用于命中爆点核心，面积不超过画面 5% |
| 主要光形 | 线状（流星轨迹），全段只用这一种 |
| 法相形态 | 带翼天马，鬃毛与翼羽由密集光点构成，四蹄有拖尾 |
| 法相比例 | 本体身高的 1.3 倍，翼展略宽于本体肩宽 |
| 法相位置 | 本体背后偏上，前缘压到本体肩线之前，后缘落在景深深处 |
| 透明度与相位 | 55% 半透明；动作落后本体 0.1 秒 |
| 时长与镜数 | 12 秒，5 镜（2.4／2.2／2.4／2.6／2.4） |
| 喊招 | 5 字，按 1.2 秒预算 |
| 结束帧 | 对手贴墙、身体前折、胸口仍有金点未熄 |

## 分镜

| 镜 | 时间 | 时长 | 景别 | 机位与运镜 | 本体动作 | 法相层 | 环境层 | 声音 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 起势 | 0:00–0:02.4 | 2.4 | 近景 | 低机位固定 | 双脚开立，重心下沉，双拳收到腰侧、拳面朝下 | 未成形，背后空中只有一团压不住的光斑 | 脚边裂纹向外扩，碎石轻微浮起 | 鞋底摩擦、气流上卷的低频 |
| 2 宣言＋显形 | 0:02.4–0:04.6 | 2.2 | 双人中近景 | 过肩略俯，缓推 | 喊「天马流星拳」，双拳抬到胸前 | 先勾出四蹄与展开双翼的轮廓，再由光点填满躯干；鬃毛粒子化，眼睛先亮 | 石子离地半寸，浮尘被推开 | 喊招 + 低频嗡鸣起 + 碎石离地 |
| 3 可见段 | 0:04.6–0:07.0 | 2.4 | 侧向中近景 | 过肩跟拍 | 三拳：右拳取左肩，左拳扫肋侧，第三拳被抬臂架住 | 双蹄前刨、双翼前压，拳锋落后 0.1 秒压到同一落点 | 每次接触溅出青蓝与金火花，洒到地面 | 连续破空 + 三记点状撞击 |
| 4 成线段 | 0:07.0–0:09.6 | 2.6 | 正面中近景 | 略低角固定，轻微推近 | 只剩肩背与两拳轮廓，拳路连打 | 化成半透明光轨叠在光带上，鬃毛碎成粒子向前流 | 对手双臂交叉连挡，火花沿前臂连成线，脚跟蹭出两道痕 | 一条持续高速破空，叠四记连击 |
| 5 结果段 | 0:09.6–0:12.0 | 2.4 | 双人中近景 | 略俯固定 | 最后一拳打穿交叉的双臂，正中胸口 | 从边缘向内塌缩成一点，碎成青蓝光点向上飘散 | 爆点核心一小片金色暖光，气浪把碎石推成环；对手离地后飞撞墙，墙面凹陷掉落灰 | 闷响 + 低频轰鸣 + 余波耳鸣 |

四段分配：起势 2.4 秒（20%）、宣言 2.2 秒（18%）、爆发 5.0 秒（42%）、收束 2.4 秒（20%）。同节奏连打 4.6 秒后由命中换挡，没有超过 5 秒的单一节奏。

## H3 提示词（多参考路线，英文字段名 + 中文正文）

假设用户提供了 `<Subject 1>` 的角色设定图作为 `<Picture 1>`，没有音频参考。正文里不写角色姓名，姓名只出现在台词原文。

```text
subject_definitions:
<Subject 1>：一名身披青蓝色青铜圣衣、护肩带翼纹的少年格斗者，取 <Picture 1> 的外形与服装。其背后显形的法相是一只半透明的带翼天马，通体青蓝色，鬃毛与翼羽由密集光点构成，比例约为该少年的 1.3 倍身高。另有一名身着暗色护具的对手，作为受击方，无独立参考。

summary:
reference generation：少年在原地发动天马流星拳，背后天马法相显形并与其拳路同步，连续出拳后一拳将对手击飞撞墙。

retention_analysis:
<Subject 1> — fully_preserved：出现在全部 5 个镜头，身高、体型、圣衣造型与配色不变。<Picture 1> 只提供身份与服装依据，不承担硬首帧。法相为新增视觉元素，其配色与母体同源，不改变主体外观。

detailed_description:
整体为冷调写实动画质感，光源以青蓝色为主，环境偏暗，只有命中爆点核心出现一小片金色暖光。

[Shot 1] 起势：一名身披青蓝圣衣的少年双脚开立，重心下沉，双拳收到腰侧、拳面朝下；其脚边地面出现细裂纹并向外扩散，碎石子微微浮起；能量从脚底沿小腿向上汇聚成一道青蓝光带，拳套边缘亮起一线近白冷光；其背后空中只有一团压不住的光斑，尚未成形。低机位固定近景，镜头随其下沉轻微下压。声音为鞋底摩擦与气流的低频。

[Shot 2] At 00:02.400, the camera cuts to 双人中近景，过肩略俯缓推：少年双拳抬至胸前并开口，<d>[Chinese] 天马流星拳</d>；其背后空间中先勾出一匹天马的四蹄与展开的双翼轮廓，随后由密集青蓝光点填满躯干与头颈，鬃毛与翼羽呈粒子状，法相双眼先亮；法相约为少年 1.3 倍身高，前缘压到少年肩线之前，后缘落在景深深处，胸腹处保持通透、不遮挡少年面部；地面石子离地半寸，浮尘被向外推开。声音为喊招、低频嗡鸣渐起与碎石离地的细响。

[Shot 3] At 00:04.600, the camera cuts to 侧向中近景、过肩跟拍：少年连出三拳，右拳直取其对手左肩，左拳横扫肋侧，第三拳被对手抬臂架住；每拳在空气中留下 3 至 5 个错位残影；背后天马的双蹄前刨、双翼前压，其拳锋落后少年约 0.1 秒压到同一落点；三次接触各溅出一小簇青蓝与金色火花，火花洒到地面。声音为连续破空与三记点状撞击。

[Shot 4] At 00:07.000, the camera cuts to 正面中近景、略低角、轻微推近：拳路连成两条贯穿画面的青蓝光带，自腰际拉向对手胸前；少年只余肩背与两拳的轮廓；天马法相化成半透明光轨叠在光带上，鬃毛碎成粒子向前流；对手双臂交叉连挡，火花沿前臂连成一条线，脚跟在地面蹭出两道浅痕。声音为一条持续的高速破空叠四记连击。

[Shot 5] At 00:09.600, the camera cuts to 双人中近景、略俯固定：最后一拳打穿对手交叉的双臂正中胸口；爆点核心出现一小片金色暖光，气浪把地面碎石向外推成一圈；对手双脚离地向后飞出，后背撞上墙面，墙面凹陷并落下灰土；天马法相自边缘向内塌缩成一点，碎成青蓝光点向上飘散。镜头停在对手贴墙、身体前折、胸口仍有金点未熄的那一帧。

overall_soundscape:
持续的空气流动低频，远处碎石落地的零星声响，逐渐衰减的耳鸣底噪。

non_diegetic_music:
低沉的鼓点随出拳密度加快，命中后骤然停止并留一段无配乐的空档。
```

## 出图提示词

三张图各有分工：一张锁法相形态与配色，一张锁成线段的关键帧，一张锁命中帧。

### 1. 法相设定图（用来固定形态与配色，后续所有法相都照这张）

```text
A full-body design sheet of a translucent winged pegasus phantom standing in three-quarter view against a dark neutral background; its body is built from dense cyan-blue light particles (#4FC3F7), the mane and wing feathers are streamed strands of finer particles, the rim of every contour is a near-white cyan highlight (#EAF7FF), the shadowed interior fades into deep blue (#1A4C8B); the eyes are the brightest points; the legs end in drifting particle trails instead of hooves touching the ground; no text, no watermark, no borders — a single clean full-bleed figure on a plain dark field.
```

### 2. 成线段关键帧（分镜用，正面略低角）

```text
A single cinematic frame, front view slightly below eye level: two continuous cyan-blue light bands stretch horizontally across the frame from the waist of a young fighter in a cyan-bronze armor toward the chest of an opponent in dark armor; only the fighter's shoulders, back and both fists remain readable, the rest dissolving into speed; overlapping round afterimages of fists sit along the bands; sparks line the opponent's crossed forearms; a translucent winged pegasus phantom is flattened into a light trail layered above the bands, its mane streaming forward as particles; floor dust and small stones pushed outward in a ring; cold cyan light is the dominant color, the background nearly black; no text, no watermark, no borders — a single clean full-bleed frame.
```

### 3. 命中帧（收尾用，双人中近景）

```text
A single cinematic frame, slightly high angle, two figures: the final punch has broken through the opponent's crossed arms and landed on the chest; a small golden spark core (#F5C542) glows at the contact point, the only warm color in the frame; the opponent is lifted off the ground and bent forward against a cracked wall with falling plaster; a ring of pushed-out debris surrounds them; behind the attacker the translucent pegasus phantom is collapsing inward into a single point, its edges already breaking into cyan particles drifting upward; the attacker stays readable from shoulders up, face not covered; no text, no watermark, no borders — a single clean full-bleed frame.
```

## 自检

| 检查项 | 结果 |
| --- | --- |
| 范式 | 连打型，5 镜落在 4～6 镜区间 |
| 四段时长 | 2.4＋2.2＋5.0＋2.4＝12 秒 |
| 单镜时长 | 2.2～2.6 秒，全部落在 2～5 秒 |
| 喊招预算 | 5 字 ÷ 1.2 秒 ≈ 4.2 字/秒，在 4.1～4.5 区间 |
| 身体层 | 删掉特效后仍能读出「三拳被架住，最后一拳打穿」 |
| 法相同步 | 落点写明同一处，相位写明落后 0.1 秒，比例锁 1.3 倍 |
| 色彩 | 一个主色、一个暖点色、一种光形 |
| 命中反馈 | 位移、墙面凹陷、火花线、气浪推碎石，共四项 |
| 收尾 | 停在贴墙前折那帧；法相已塌缩消散 |
| 不可生成写法 | 没有「无数拳」「漫天拳影」「天崩地裂」 |
| 姓名规则 | 正文用「少年」「对手」，姓名只在 `<d>` 台词里 |
| 同人边界 | 仅文字提示词、参考图自建、发布标同人非官方、不商用 |

## 四种常见改法的落点

- **想更重**：加长镜 5 到 3.2 秒，把墙面凹陷和灰落写细，低频轰鸣拉长；不要加拳。
- **想更快**：把镜 3 的可见拳减到 2 拳，镜 4 的光带拉到跨满屏，残影提到 5 个。
- **想更亮**：只提高光覆盖率，别抬整体亮度；爆点核心保持 100%，周围迅速回落主色。
- **想让法相更有存在感**：把镜 2 的显形拉长到 2.8 秒，加「眼睛先亮」和「鬃毛第一缕粒子向前飘」，比例仍锁 1.3 倍。
