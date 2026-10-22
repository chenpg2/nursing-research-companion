# 安装说明（写给 AI 助手看的）

> 如果你是人：不用读下去。把这整份文字复制，粘贴给你的 AI 助手（Claude Code、Kimi Code，或其他能操作你电脑文件、支持 Skill 的 AI 工具），它会照着装好。

---

你是用户的 AI 助手。用户想安装「护理科研陪跑助手」Skill（名称 `nursing-research-companion`），来源是公开仓库 https://github.com/chenpg2/nursing-research-companion 。用户多半是临床护士，不懂编程。请按下面的步骤操作。

## 规则

1. 全程用简体中文、大白话和用户说话，不要贴大段命令输出给用户看。
2. 第 1 步只看不改。第 1 步做完，先用两三句话把整个计划告诉用户（装到哪里、临时文件放哪里、有旧版本怎么处理），用户同意后再动手。之后照计划做就行，不用每步再问；实际情况和计划不一样时，停下来再问。
3. 只复制仓库里的 `skills/nursing-research-companion` 文件夹。不要运行仓库里的任何脚本，不要用 sudo 或管理员权限，不要改动其他文件或配置。
4. 你不确定的事（比如你所在平台的 Skill 目录在哪），先查你所在平台的官方文档，查不到就问用户，不要自己猜一个路径写进去。
5. 如果你只能聊天、不能读写用户电脑上的文件，直接告诉用户：「这个工具装不了 Skill，请改用 https://github.com/chenpg2/nursing-research-companion 首页说明里的复制粘贴版」，然后停止。

## 第 1 步：确定安装位置（只看不改）

按你自己是哪个工具来选 Skill 目录（`~` 指用户主目录，Windows 上是 `C:\Users\<用户名>`）：

| 你是 | Skill 目录 |
|------|-----------|
| Claude Code | `~/.claude/skills/` |
| Kimi Code | `~/.kimi-code/skills/`（设置了 `KIMI_CODE_HOME` 时是 `$KIMI_CODE_HOME/skills/`） |
| 其他支持 `SKILL.md` 格式的工具 | 你所在平台规定的 Skill 目录。查不到就问用户；用户也不清楚时，可以建议用 `~/.agents/skills/`（不少工具会读这个目录），并说明这是通用位置，装完叫不出来就改用第 4 步的打包做法 |
| 只能通过界面上传或导入 Skill 的平台 | 不需要目录，第 3 步改用第 4 步的打包做法 |

然后看一下 Skill 目录里是否已经有 `nursing-research-companion` 文件夹（说明以前装过）。

装好以后的结构是 `<Skill 目录>/nursing-research-companion/SKILL.md`。文件夹名就用 `nursing-research-companion`，和 `SKILL.md` 里的 `name` 一致（有的工具要求这样）。

## 第 2 步：下载到临时文件夹

在系统临时目录（macOS / Linux 是 `/tmp`，Windows 是 `%TEMP%`）里新建一个文件夹 `ncr-download`，下载到这里，不要下载到用户的工作文件夹。这个文件夹已经存在（多半是上次没装完留下的）时，先删掉它再下载。Windows 上把下面命令里的路径换成 `%TEMP%\ncr-download\repo`：

```bash
git clone --depth 1 https://github.com/chenpg2/nursing-research-companion.git /tmp/ncr-download/repo
```

没有 git 时，把下面的压缩包下载到同一个临时文件夹再解压：

```
https://github.com/chenpg2/nursing-research-companion/archive/refs/heads/main.zip
```

两种都失败（国内网络访问 GitHub 有时不稳定）：请用户在浏览器打开 https://github.com/chenpg2/nursing-research-companion ，点绿色的「Code」按钮，选「Download ZIP」，下载后告诉你文件放在哪里。

## 第 3 步：复制到 Skill 目录

1. Skill 目录不存在时，先建好它（包括上级文件夹）。
2. 以前装过时，把旧的 `nursing-research-companion` 文件夹移出 Skill 目录，放到 Skill 目录的上一级，改名为 `nursing-research-companion-backup-<年月日时分>`（例如 `~/.claude/nursing-research-companion-backup-202611041530`）。不要把备份留在 Skill 目录里，否则工具可能读到两份同名的 Skill。
3. 把下载内容里的 `skills/nursing-research-companion` 整个文件夹复制到 Skill 目录下。只复制这一个文件夹。

## 第 4 步：检查和收尾

逐项确认，有一项不对就修好或告诉用户：

- `<Skill 目录>/nursing-research-companion/SKILL.md` 存在，开头的 `name:` 是 `nursing-research-companion`
- `references/` 里有 6 个文件：`hypothesis-wizard.md`、`intervention-development.md`、`literature-reading.md`、`results.md`、`stages.md`、`statistics.md`
- `assets/` 里有 `project-record-template.md`
- Skill 目录里没有别的文件夹也叫这个名字或带着同名的 `SKILL.md`

**打包做法**（只适用于要在界面上传 Skill 的平台）：把 `skills/nursing-research-companion` 文件夹压缩成 `nursing-research-companion.zip`，压缩包打开后第一层就是 `nursing-research-companion` 文件夹。把它放在用户的「下载」文件夹里，告诉用户文件位置，并请用户在平台的 Skill 或技能设置里导入它。不同平台的入口不一样，你不确定入口时就让用户看平台的帮助说明，不要编造菜单名称。

最后只删除你在第 2 步建的临时文件夹（`ncr-download`）。用户自己下载的 ZIP 不要删。

## 第 5 步：告诉用户怎么用

用几句话告诉用户：

1. 装在了哪里；如果备份了旧版本，备份在哪里。
2. 需要新开一个对话（或重启工具），Skill 才会生效。
3. 新对话里说「帮我做护理科研」。看到 AI 先自我介绍、再出一道选择题问在哪个阶段，就说明装好了。Kimi Code 里也可以输入 `/skill:nursing-research-companion` 直接调用。
4. 进度会存进当前工作文件夹里的 `护理科研项目档案.md`，下次在同一个文件夹打开就能接着做。
