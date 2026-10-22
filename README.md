# 护理科研陪跑助手

给临床护士和护理研究生用的一套 AI 提示词，覆盖从「临床上注意到一个现象」到「写成论文、回复审稿」的整个过程。在 Kimi、DeepSeek 这类对话式 AI 里复制粘贴就能用，不需要编程。

它的用法是：AI 一次问你一个问题，尽量给出几个选项让你挑，你凭临床经验做判断就行。统计方法、样本量、结果解读这些环节，卡片里写好了检查规则，减少常见的统计错误。

这套工具最早是为系列课《AI 赋能护理科研实战：从一个临床现象到一篇论文》准备的，没听过课也可以直接用。

## 能做什么

一共 9 张提示词卡，按研究的先后顺序排：

| 卡片 | 什么时候用 | 你会得到什么 |
|------|-----------|-------------|
| [00 总提示词](prompts/00-总提示词.md) | 不知道从哪开始 | AI 先判断你在哪一步，再一步步带着走 |
| [01 项目画像](prompts/01-项目画像.md) | 想做科研，还没有方向 | 几个可做的方向，标好难度 |
| [07 科学假说向导](prompts/07-科学假说向导.md) | 只有一句大白话的临床现象 | 假说卡：H1/H0、PICO、立题逻辑链 |
| [02 选题凝练](prompts/02-选题凝练.md) | 想法比较清楚了，或者要读文献 | 选题卡、文献矩阵、单篇文献精读笔记 |
| [03 研究设计](prompts/03-研究设计.md) | 选研究设计、防偏倚 | 设计类型、偏倚清单、变量表 |
| [08 干预方案构建](prompts/08-干预方案构建.md) | 做「基于 XX 理论的方案构建」类课题 | 理论对应表、逻辑模型、德尔菲和预实验方案 |
| [04 统计方案](prompts/04-统计方案.md) | 选统计方法、算样本量 | 统计方法、样本量，以及写开题报告用的统计段落初稿 |
| [05 结果解读](prompts/05-结果解读.md) | 看不懂 SPSS 输出 | 先复述数字再解读，给出规范的结果句和基线表 |
| [06 论文写作](prompts/06-论文写作.md) | 写作、润色、投稿、回复审稿 | 结构建议、中英修改对照表、AI 使用声明 |

文件编号大体等于阶段号加 1（「阶段 3 统计方案」是 `04`）。`07` 和 `08` 是后来补的两张，所以编号靠后。

## 用法一：复制粘贴（推荐大多数人用这个）

1. 点上面表格里的卡片名，打开要用的卡。
2. 复制卡片里灰色代码框中的全部文字，代码框外面的说明不用复制。有的卡有好几个代码框（比如 02 卡），每个框是一种单独的用法，看小标题选一个就行。
3. 在 Kimi（或 DeepSeek 等）新建一个对话，粘贴，发送。
4. AI 出选择题时，回复字母就行。看不懂可以说「说简单点」。
5. 每一段结束，AI 会给一张小结卡。把它复制存好，下次接着做时一起贴回去。

## 用法二：作为 Skill 安装

Skill 是一种「装进 AI 工具里的能力包」：装好以后不用每次粘贴提示词，直接说「帮我做护理科研」，AI 就会按这套流程带你走。目前在 Claude Code 上测试过；Kimi Work、proma 等支持 Skill 的工具，按平台的说明导入同一个文件夹即可，我们还没有逐一测试。

和复制粘贴版相比，Skill 版多了三件事：能读你电脑里的文献 PDF 和数据文件，统计会写代码真的算一遍，进度会存进项目档案 `护理科研项目档案.md`（放在你当前打开的工作文件夹里），下次打开接着做。

**第一步：下载。** 不会用 git 的话，在本页顶部点绿色的「Code」按钮，选「Download ZIP」，解压。会用 git 的话：

```bash
git clone https://github.com/chenpg2/nursing-research-companion.git
```

**第二步：把 `skills/nursing-research-companion` 这个文件夹放到 Skill 目录里。** 以 Claude Code 为例：

- macOS / Linux：`~/.claude/skills/`（`~` 是你的用户文件夹）
- Windows：`C:\Users\你的用户名\.claude\skills\`

用命令复制（macOS / Linux，在下载好的仓库文件夹里运行）：

```bash
cp -r skills/nursing-research-companion ~/.claude/skills/
```

**第三步：检查。** 新开一个会话，说「帮我做护理科研」。AI 先做自我介绍、再给出一道选择题问你在哪个阶段，就说明装好了。

## 用之前请知道

- AI 给出的所有方案都是草稿。正式用于开题、标书或论文之前，请交给导师或统计老师审一遍。
- 不要把真实患者的信息贴给任何 AI。姓名、病历号、身份证号、手机号、家属信息都要先删掉。
- AI 给出的参考文献，要逐条在知网或 PubMed 上查到原文再用。
- 这套工具帮助做科研，不提供临床诊疗建议。

## 仓库里有什么

```
prompts/            9 张提示词卡（复制粘贴版）
skills/             Skill 版（SKILL.md + references/ + assets/）
course/demo-data/   练习用的模拟数据：重复测量方差分析的 SPSS 风格输出、基线表、生成脚本
```

`course/demo-data/` 里的数据全部是模拟的，可以拿来练习 05 卡（结果解读），用法见那个文件夹里的说明。

## 设计参考

- 双钻石导航和 08 卡的方案构建流程，参考了 Sevillano-Garayoa L, Martín-Martín J, Olano-Lizarraga M. Co-designing a family-centered intervention to support home-based caregiving in advanced chronic illness: a double diamond framework-guided process. *International Journal of Nursing Studies*, 2026, 183: 105639. doi:10.1016/j.ijnurstu.2026.105639
- 复杂干预的研制框架：Skivington K, et al. A new framework for developing and evaluating complex interventions: update of Medical Research Council guidance. *BMJ*, 2021, 374: n2061.

统计部分的判断标准（卡方的使用条件、量表效度指标、德尔菲指标等）采用国内医学统计教材和护理研究里的常用口径，不同教材的数值可能略有出入，以你的目标期刊和导师的要求为准。预实验样本量这类有争议的地方，卡里写了具体出处。

## 版本与反馈

修订记录见 [CHANGELOG.md](CHANGELOG.md)。用的时候发现问题，或者有改进建议，欢迎在本页顶部的「Issues」里提（需要先注册一个 GitHub 账号）。

## 许可

采用 [CC BY-NC-SA 4.0](LICENSE) 许可：可以免费使用、转发和改编，转发或改编时请注明出处，不得用于商业用途，改编后的版本也要用同样的许可公开。

Copyright © 2026 Peigen Chen
