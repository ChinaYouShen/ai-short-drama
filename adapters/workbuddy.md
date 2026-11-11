# WorkBuddy 入口

WorkBuddy（腾讯企业智能体 / 桌面端工作台）的 Skill 也是「一个带 SKILL.md 的文件夹」，读取本包时按下面的方式接入。

## 一、导入

三种方式任选：

- **从文件夹导入**（推荐）：技能中心 → 我的技能 → `+ 导入技能` → 选中本包的 `SKILL.md` 或整个 `ai-short-drama` 目录 → 确认。
- **从 URL 导入**：填仓库地址 `https://github.com/ChinaYouShen/ai-short-drama`。
- **手动放入**：复制到 `~/.workbuddy/skills/ai-short-drama/`，重启客户端。

导入后要在「我的技能」里把开关切到**已启用**，否则对话里 @ 不出来。

## 二、目录与命名

- 目录名与 `SKILL.md` 的 `name` 保持一致（`ai-short-drama`）。WorkBuddy 靠 `name` 与 `description` 识别技能。
- 保留完整目录结构：`SKILL.md`、`references/`、`templates/`、`scripts/`、`adapters/`、`agents/` 必须同层。只复制 `SKILL.md` 会导致按需读取的模块全部缺失。
- `scripts/validate.py` 需要本地 Python 3，零依赖；没有 Python 时按 `references/wuxi/validation.md` 的人工核对清单逐项过。

## 三、怎么唤起

WorkBuddy 用 **@技能名** 唤起，不是斜杠命令：

```text
@ai-short-drama /武戏 新建，多参考生成，12 秒，雨夜废墟遭遇，中文
```

加载后先读本文件，再读上一级 `SKILL.md`，之后按需读取：

- 文戏 → `references/wenxi.md` 与 `references/wenxi/index.md`
- 武戏 → `references/wuxi.md` 与 `references/wuxi/index.md`
- 必杀技 → `references/wuxi/ultimate/index.md`
- 体系选择 → `references/wuxi/catalog/index.md`
- H3 格式与素材绑定 → `references/h3-format.md`
- 小说改编 → `references/production/adapt.md`

`/选题`、`/大纲`、`/人物`、`/道具`、`/场景`、`/站位`、`/剧本`、`/分镜`、`/图片`、`/漫剧`、`/文戏`、`/武戏`、`/必杀技`、`/武戏体系`、`/H3` 这些斜杠前缀按**首段文本**识别，不依赖客户端命令注册。

## 四、和别的平台不一样的地方

- **没有斜杠命令**：`/武戏` 只是正文里的一个标记词，别指望 @ 菜单里点出来。
- **@ 一次只加载一个技能**：同一次对话里同时要文戏和武戏，直接在追问里说，不要开两路。
- **多轮沿用**：WorkBuddy 会保留本技能在会话中的加载状态，后续追问不必重新 @。
- **素材是附件**：图片、音频走 WorkBuddy 的附件上传，之后按 `references/h3-format.md` 的「用户发来素材时怎么用」三步清点、判路线、绑定；`templates/reference-manifest.md` 可直接填。

## 五、交付

输出当前请求的产物，不自动往下做下一阶段。用户说跳过、只检查、从任意阶段继续时按指定路径执行，不为流程完整追问。没有用户真实输入的台词、人物、素材和成片结果时不补写、不声称已验证。
