# AI 生成短剧技能包（ai-short-drama）

<p align="center">
  <img src="https://img.shields.io/github/stars/ChinaYouShen/ai-short-drama?style=for-the-badge&logo=github&color=E8C45A" alt="Stars" />
  <img src="https://img.shields.io/badge/%E7%89%88%E6%9C%AC-v1.9.0-8A2BE2?style=for-the-badge" alt="版本" />
  <img src="https://img.shields.io/badge/License-GPL--3.0-blue?style=for-the-badge" alt="License" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Language-Chinese-E8C45A?style=for-the-badge" alt="Language" />
  <img src="https://img.shields.io/badge/%E6%8B%9B%E5%BC%8F-221-F48D73?style=for-the-badge" alt="招式" />
  <img src="https://img.shields.io/badge/%E8%BF%90%E9%95%8F-70-4C9AFF?style=for-the-badge" alt="运镜" />
  <img src="https://img.shields.io/github/last-commit/ChinaYouShen/ai-short-drama?style=for-the-badge&color=blueviolet" alt="最近提交" />
</p>

给会读文件的 AI 用的一套短剧规矩。它不装软件、不调接口，只负责把你想要的东西写成能直接用的文字和提示词。

如果这个包帮你省了时间，点个 Star 就行，不用别的。

- 许可证：**GPL-3.0**，可商用，改后分发同样开源
- 语言：简体中文
- 可用：豆包、Cursor、Codex、WorkBuddy、文心一言、DeepSeek Harness

## 它能做什么

选题 → 大纲 → 人物 → 资产 → 剧本 → 对白 → 钩子 → 审稿 → 分镜 → 提示词 → 武戏 → 预算，任意一环都能单独进入，不必从头跑。

提示词同时覆盖 MiniMax H3 的六段字段和 Seedance 2.5 的四段时间轴：素材绑定、一句话概述、整数秒时间轴、全局约束，换模型时按单改结构，不硬搬。开工前用 `templates/brief.md` 把交付物、模型、平台、素材一次问清；交付前用 `scripts/consistency.py` 把分镜和剧本、资产逐条对账。

镜头这一块也不靠模板堆：`references/yunjing.md` 收了 70 条运镜，按人物出场、对话视角、开场展开、转场慢镜、近战、爆发、心理戏、物件氛围等十四组排，每条给起幅、运动、落幅、用途和禁用边界；另配一张场景选型表，以及「一镜一主运镜、人物入画不用航拍」四条硬规则。

武戏是这套包的特色：**每一招都要有一个能画出来的特效主体**（一条金龙、三道爪痕、一面冰墙），规矩写进参数表和检查脚本。现收 221 招：金庸 71、古龙 13、梁羽生 12、温瑞安 7、圣斗士 100、降龙 18。

## 三步用起来

1. 解压到一个固定文件夹，整个文件夹保留完整
2. 把文件夹交给你的 AI，让它读 `SKILL.md`；平台入口在 `adapters/`
3. 直接说你要什么，例如「写第 3 集剧本，60 秒，留个钩子」

简写：`/剧本` `/对白` `/钩子` `/审稿` `/分镜` `/运镜` `/武戏` `/必杀技`

## 文件只有这几个入口

| 你要什么 | 读哪个 |
| --- | --- |
| 选题、大纲、人物、剧本、对白、钩子、节奏 | `references/story.md` |
| 这一镜怎么动、运镜能不能叠加 | `references/yunjing.md` |
| 小说改编、漫剧、反拆参考片、分批验收 | `references/adapt.md` |
| 挑毛病、打分、诊断一处 | `references/review.md` |
| 分镜、镜头九问、承接、图片提示词 | `references/board.md` |
| H3 与 Seedance 2.5 提示词、模型对照、多段拼接 | `references/prompt.md` |
| 文戏细则 | `references/wenxi/rules.md` |
| 武戏、特效、选招、参数表 | `references/wuxi/` |
| 花费、交付关卡、平台口径 | `references/cost.md` |
| 能力边界 | `references/map.md` |

## 六条硬规矩

1. 特效必须是能画出来的主体，只写亮度不通过
2. 打中才写伤，挡住只写火花与位移
3. 台词按 4.1 字/秒算，一镜一句
4. 单镜 2～5 秒，一镜一个主要动作
5. 不编原作招名
6. 写提示词前先答一镜九问

## 检查

```bash
python3 scripts/check.py
```

一条命令跑完自检、样例、221 招体检与文档断链，零依赖。

## 用了就留一句

这套包没有埋点、不采集数据。想知道它在什么场景里真的能用，靠的是使用者自愿留一句：

- 点个 Star，让后来的人知道有人用过
- 或留一条[使用回执](https://github.com/ChinaYouShen/ai-short-drama/issues/new?template=usage.yml)：一句话说你拿它做了什么，卡住的地方也写上

## 作者

酉神（B 站：酉神已退休）

## 配套

- 在线目录与安装说明：[短剧提示词技能包](https://www.fzgcwl.com/short-drama-skill.html)
- 五个环节各写了一篇，按需看：
  [选题与大纲](https://www.fzgcwl.com/guide-short-drama-topic.html) ·
  [分镜提示词](https://www.fzgcwl.com/guide-short-drama-storyboard.html) ·
  [武戏](https://www.fzgcwl.com/guide-short-drama-wuxi.html) ·
  [必杀技](https://www.fzgcwl.com/guide-short-drama-ultimate.html) ·
  [H3 格式](https://www.fzgcwl.com/guide-h3-prompt.html)
