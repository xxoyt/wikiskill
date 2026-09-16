# WikiSkill

让 AI Agent 从自己的历史任务中学习，**不再重复踩同一个坑**。

不改模型权重，也不用重新训练——在你的项目里维护一个 `.wiki/` 目录，把每次任务的成败沉淀成结构化经验，再迭代成可复用的技能文档。

源自 Google Research 论文 [arXiv:2608.27454](https://arxiv.org/abs/2608.27454)。论文报告 Gemini-3.5-Flash 从 49.5% 提升到 68.1%；更值得关注的是，**9B 小模型 + WikiSkill（47.4%）超过了 27B 裸模型（39.4%）**。

---

## 目录

- [它解决什么问题](#它解决什么问题)
- [60 秒快速开始](#60-秒快速开始)
- [按平台安装](#按平台安装)
- [日常怎么用](#日常怎么用)
- [`.wiki/` 目录说明](#wiki-目录说明)
- [设置自动化（可选）](#设置自动化可选)
- [故障排查](#故障排查)
- [常见问题](#常见问题)
- [文件清单](#文件清单)

---

## 它解决什么问题

你的 Agent 每次会话都从零开始。上周踩过的坑——某个库的 API 陷阱、某个接口的参数顺序、某种报错的真实根因——这周它会原样再踩一遍，你还得再解释一次。

WikiSkill 把这些经验写到项目里的 `.wiki/` 目录，让它们**活过会话边界**：

| 没有 WikiSkill | 有了 WikiSkill |
|---------------|---------------|
| 同一个坑反复踩 | 踩一次，记一次，之后自动规避 |
| 经验散落在对话历史里 | 沉淀在项目文件中，可 grep、可 review |
| 换工具就失忆（Claude Code ↔ Codex ↔ WorkBuddy） | `.wiki/` 是纯 Markdown，跨平台通用 |
| 靠你每次手动提醒 | 周期性复盘自动提炼模式 |

**它不是什么**：不是记忆插件，不是向量数据库，不需要联网，不调任何云服务。就是一堆 Markdown 文件 + 一套让 Agent 遵守的读写规范。

---

## 60 秒快速开始

最快路径（WorkBuddy / CodeBuddy 用户，什么都不用装）：

```
你：初始化 wiki
```

Agent 会创建 `.wiki/` 目录结构。然后正常干活，任务结束后说：

```
你：记录轨迹
```

积累 3–5 条轨迹后：

```
你：复盘
```

Agent 会把轨迹里的重复模式提炼进 `.wiki/knowledge/patterns.md`。**到这一步就已经有用了**——哪怕从不进行后续步骤，光是这个 patterns 文件就值回票价。

### 手动初始化（Claude Code / Codex，或想自己控制）

**推荐用统一安装器**，它会把运行时复制进项目，之后项目就完全自包含：

```bash
# 在 wikiskill 解压目录下执行，<项目目录> 换成你的项目路径
python scripts/install.py --platform claude --target <项目目录>
python scripts/install.py --platform codex  --target <项目目录>
```

只想初始化、不动其他东西时，按你实际用的 shell 选一行：

| 你的环境 | 命令 |
|---------|------|
| Windows PowerShell | `python "解压目录\scripts\wiki_init.py"` |
| Windows CMD | `python "解压目录\scripts\wiki_init.py"` |
| Git Bash / WSL / Linux / macOS | `bash "解压目录/scripts/wiki_init.sh"` |
| 无 Python 的 Windows | `powershell -ExecutionPolicy Bypass -File "解压目录\scripts\wiki_init.ps1"` |

三个脚本产出完全相同，只是运行环境不同。

> **为什么不写 `~/.workbuddy/skills/wikiskill/...`**
> `.workbuddy/` 是 **WorkBuddy 的私有目录**，Claude Code / Codex 用户机器上并不存在。
> 早期版本把初始化与 hook 都指向那里，结果在纯 Claude Code 环境下**静默失效**——
> 不报错、不提醒。本版本已改为项目自包含：运行时复制进 `.wiki/scripts/`，
> 生成的文件全部使用项目内路径，项目可整体提交 Git，换机器 clone 后无需重装。

---

## 按平台安装

### WorkBuddy / CodeBuddy

**零配置。** 本 skill 已安装即可用，触发词自动识别。

### Claude Code

**一条命令搞定**（在 wikiskill 解压目录下执行）：

```bash
python scripts/install.py --platform claude --target <你的项目目录>
```

它会自动完成：创建 `.wiki/` 骨架 → 把运行时与文档复制进 `.wiki/` → 生成自包含的 `CLAUDE.md` → 安装 Stop hook（相对路径）。

想装到全局而非单个项目：

```bash
python scripts/install.py --platform claude --user
```

> 用户级安装会把运行时放到 **Claude Code 自己的目录** `~/.claude/scripts/wikiskill/`，
> 而不是 WorkBuddy 的目录，因此不装 WorkBuddy 也能用。
> 注意：它会修改 `~/.claude/settings.json`（该文件可能含 API token 等配置，
> 安装器只追加 hooks 字段，其余内容原样保留）。

手动方式（不用安装器，或想精细控制）：

1. 复制指令模板到项目根目录：

   ```bash
   # Windows (PowerShell)
   Copy-Item "解压目录\references\CLAUDE.example.md" CLAUDE.md

   # Unix
   cp "解压目录/references/CLAUDE.example.md" CLAUDE.md
   ```

2. 初始化 Wiki（按你的 shell 选一行）：

   ```powershell
   # Windows PowerShell
   python "解压目录\scripts\wiki_init.py"
   ```

   ```cmd
   :: Windows CMD
   python "解压目录\scripts\wiki_init.py"
   ```

   ```bash
   # Linux / macOS / Git Bash
   bash "解压目录/scripts/wiki_init.sh"
   ```

3. 编辑 `CLAUDE.md`，把项目名称和描述改成你自己的。

> `CLAUDE.md` 是**全量常驻**加载的——每次会话都会读。它比 WorkBuddy 的按需加载更稳定（Agent 始终知道 wiki 存在），代价是占用一些上下文。
>
> 手动复制的模板里，初始化命令仍指向 `~/.workbuddy/`。如果你没装 WorkBuddy，
> 用模板里的**方式 B**（内联 `mkdir` + `printf`，无任何外部依赖）即可，
> 或改用上面的安装器得到完全自包含的版本。

### Codex (OpenAI)

```bash
python scripts/install.py --platform codex --target <你的项目目录>
```

Codex 没有 hook 机制，因此只生成 `AGENTS.md` 和 `.wiki/`，不写任何配置文件。

手动方式同上，把 `AGENTS.example.md` 复制为项目根目录的 `AGENTS.md`：

```powershell
# Windows PowerShell
Copy-Item "解压目录\references\AGENTS.example.md" AGENTS.md
python "解压目录\scripts\wiki_init.py"
```

```bash
# Linux / macOS / Git Bash
cp "解压目录/references/AGENTS.example.md" AGENTS.md
bash "解压目录/scripts/wiki_init.sh"
```

### 各平台体验差异

| 平台 | 指令文件 | 加载方式 | 自动触发 |
|------|---------|---------|---------|
| WorkBuddy | `SKILL.md` | 按需（匹配触发词才读全文） | 是 |
| CodeBuddy | `SKILL.md` | 按需 | 是 |
| Claude Code | `CLAUDE.md` | 全量常驻 | 否，需你主动提 |
| Codex | `AGENTS.md` | 全量常驻 | 否，需你主动提 |

---

## 日常怎么用

### 触发词

| 你说 | Agent 做什么 |
|------|-------------|
| `记录轨迹` / `wiki log` | 把当前任务的轨迹追加到 `.wiki/raw/今天.md` |
| `复盘` / `wiki maintain` | 读近期轨迹，提炼失败模式与成功策略 |
| `进化技能` / `wiki evolve` | 提出一个技能改进并验证 |
| `wiki 状态` / `wiki status` | 显示统计：多少条轨迹、多少个模式、多少个技能 |
| `初始化 wiki` / `wiki init` | 创建 `.wiki/` 目录结构 |

### 核心原则：在线只记录，离线才复盘

这是**最容易用错**的地方，值得单独强调。

论文里 Inference Agent 执行任务时**不读 Wiki**（避免混淆变量），Wiki 维护是离线批量做的。对应到日常：

```
日常任务中  ──→  只做「记录轨迹」（轻量，几秒钟）
                    ↓
每 3-5 个任务  ──→  做一次「复盘」（离线，批量提炼）
                    ↓
每 5-10 个任务 ──→  做一次「进化技能」（提出改进）
```

**别在每次任务里跑完整四步循环。** 那是论文的训练流程，不是日常用法——会拖慢你，而且在线阶段读 Wiki 反而可能干扰 Agent 判断。

### 记录什么，不记录什么

一条轨迹控制在 **10 行以内**。只记：

- 关键决策点（为什么选 A 不选 B）
- 意外（报错的真实根因、文档没写的坑）
- 有效技巧（哪条命令一次就对）

不记流水账（"我打开了 X 文件，然后修改了 Y 函数"——这种没价值）。

---

## `.wiki/` 目录说明

```
.wiki/
├── raw/                      # 原始执行轨迹（按日期追加，不可变）
│   └── 2026-08-31.md
├── knowledge/                # 提炼后的知识（只增不减，永不重置）
│   ├── patterns.md           # 失败模式 FM-xxx + 成功策略 SS-xxx
│   ├── evolution_log.md      # 每次维护的记录
│   └── impact_tracker.md     # 技能提案的验证结果
├── skills/                   # 可执行技能（可回滚）
│   └── <skill-name>.md
└── meta/
    └── config.md             # 配置（创建日期、维护周期等）
```

**三层的区别很关键**：

| 层 | 可否修改 | 说明 |
|----|---------|------|
| `raw/` | 只追加，不修改 | 原始素材，作为追溯依据 |
| `knowledge/` | 只增不减，**永不重置** | 即使技能回滚，知识仍在——这是整个系统的核心价值 |
| `skills/` | 可回滚 | 技能改坏了就退回上一版本 |

**为什么"永不重置"重要**：论文的关键设计是——失败的提案不会丢失。技能可以回滚，但"尝试过什么、为什么失败"会永久留在 Wiki 里，成为下一轮提案的输入。

### 建议纳入 Git

`.wiki/` 是纯文本，建议提交到仓库。这样：

- 团队共享同一份经验
- 换机器 / 换工具都在
- 可 review（"这个模式提炼得对不对"）

> `raw/` 和 `knowledge/` 通常只追加，冲突少；`skills/` 可能并发修改，需人工合并。

---

## 设置自动化（可选）

自动化分四层，**不要试图全自动**：

| 层次 | 能否自动 | 方案 | 推荐度 |
|------|---------|------|--------|
| L1 指令常驻 | 能 | `CLAUDE.md` / `AGENTS.md` | 建议做 |
| L2 自动记录轨迹 | 能 | Claude Code Stop hook | 建议做 |
| L3 周期复盘 | 能 | WorkBuddy 定时任务 | 建议做 |
| L4 门控验证 | **不能** | 需人判断 | **设计如此** |

### L2：Claude Code 会话结束自动提醒

用统一安装器（**不依赖 WorkBuddy**，Claude Code 单独使用也正常）：

```bash
# 项目级 —— hook 用相对路径，项目移动或 clone 后依然有效（推荐）
python scripts/install.py --platform claude --target <项目目录>

# 用户级 —— 运行时装到 ~/.claude/scripts/wikiskill/，对所有项目生效
python scripts/install.py --platform claude --user

# 卸载（只移除 wiki hook，不删 .wiki/ 数据）
python scripts/install.py --platform claude --target <项目目录> --uninstall
python scripts/install.py --platform claude --user --uninstall

# 只想生成文件、不装 hook
python scripts/install.py --platform claude --target <项目目录> --no-hook
```

安装器**合并而非覆盖**已有配置——你的 `permissions`、其他 hooks 全部保留，重复安装自动跳过，卸载只移除 wiki hook。

平台自适应：Windows 用 `python ... wiki_remind.py`，Unix 用 `bash ... wiki_remind.sh`；
还会自动探测 `python` / `python3` / `py -3`，避免机器上根本没有 `python` 命令时静默失效。
装完**重启会话**才生效。

> **旧脚本 `install_claude_hook.py` 已弃用。** 它把 hook 指向 `~/.workbuddy/skills/wikiskill/`，
> 那是 WorkBuddy 私有目录——没装 WorkBuddy 的机器上该路径不存在，hook 会静默失效。
> 现在它会先校验路径，不存在就拒绝安装并提示改用 `install.py`，而不是写入死链。

### L3：WorkBuddy 定时复盘

直接对 WorkBuddy 说：

> 创建定时任务：每周日 21:00，对 mchmp 项目执行一次 WikiSkill 复盘

完整 prompt 模板见 `references/automation.md`。

### 为什么 L4 不建议自动化

判断"这个技能改进到底有没有用"需要人看实际效果。论文能自动门控是因为有 held-out 验证集；个人开发没这条件，强行自动化只会让无效技能污染技能库。

**这是质量保障，不是缺陷。**

---

## 故障排查

### Windows 相关

**`.sh` 脚本跑不了**

正常——CMD / PowerShell 原生环境没有 bash。三种解法：

| 环境 | 用什么 |
|------|-------|
| Git Bash / WSL | `.sh` 可用 |
| CMD / PowerShell | 用 `.py`（推荐）或 `.ps1` |
| Claude Code hook | **必须** `.py`（hook 走 cmd.exe，不走 Git Bash） |

**Claude Code hook 装了没反应**

按这三个原因依次排查，它们都会**静默失败**（hook 失败不阻断会话，也没有任何报错）：

| 原因 | 排查 | 解法 |
|------|------|------|
| 命令用了 `.sh`（Windows） | 看配置里是否有 `bash ... wiki_remind.sh` | 用 `install.py` 重装，它会自动选 `.py` |
| 脚本路径指向不存在的位置 | 配置里是 `~/.workbuddy/skills/wikiskill/...` 但你没装 WorkBuddy | 用 `install.py --platform claude` 重装 |
| 机器上没有 `python` 命令 | 终端执行 `python --version` | 安装器会自动探测 `python3` / `py -3`；老配置需手动改 |

重装：

```bash
python scripts/install.py --platform claude --target <项目目录> --uninstall
python scripts/install.py --platform claude --target <项目目录>
```

手动验证 hook 本身能不能跑（需在项目根目录执行）：

```bash
python .wiki/scripts/wiki_remind.py
```

**PowerShell 脚本中文乱码**

`wiki_init.ps1` 必须以 **UTF-8 with BOM** 保存（PowerShell 5.1 默认按系统 ANSI 解析无 BOM 的脚本）。本仓库已正确处理，但如果你手动编辑过它，注意保存时保留 BOM。

### 通用

**Git Bash 里 `python $HOME` 找不到文件**

这是 Windows 上**最容易踩的坑**。Git Bash 的 `$HOME` 是 POSIX 格式，Windows 原生 Python 不认：

```
Git Bash 认为:   $HOME = /c/Users/Administrator
Windows Python:  /c/Users/Administrator/.workbuddy/...  →  C:\c\Users\Administrator\...  ❌
```

报错长这样：

```
can't open file 'C:\c\Users\Administrator\.workbuddy\skills\wikiskill\scripts\wiki_init.py'
```

三种解法，任选：

| 解法 | 命令 |
|------|------|
| Git Bash 里改用 `.sh` | `bash "解压目录/scripts/wiki_init.sh"` |
| 用 Windows 格式的变量 | `python "$USERPROFILE\解压目录\scripts\wiki_init.py"` |
| 让 `cygpath` 转换 | `python "$(cygpath -w "解压目录")/scripts/wiki_init.py"` |

**最省事的解法：用项目内脚本的相对路径**（安装器生成的项目就是如此）：

```bash
python .wiki/scripts/wiki_init.py
```

这条命令在 Git Bash、PowerShell、CMD、WSL 下都成立，因为它不含任何 `$HOME` 变量。

同理，给 Python 脚本**传路径参数**时也要先转换成 Windows 格式：

```bash
python .wiki/scripts/wiki_init.py "$(pwd -W)"
```

不转换的话，脚本会打印"初始化完成"，但 `find .wiki` 找不到目录——文件被写到了 `C:\tmp\...` 这种不存在的地方。

**hook 完全没输出**

按顺序排查：

1. 项目里没有 `.wiki/` 目录 → 提醒脚本只在 `.wiki/` 存在时输出，这是设计行为（避免干扰无关项目）。先初始化。
2. 没重启会话 → Claude Code 在会话启动时读配置。
3. 配置里的脚本路径不存在 → 见上文「Claude Code hook 装了没反应」。

**手动测试提醒脚本**

在项目根目录直接执行（推荐，无需任何环境变量）：

```bash
python .wiki/scripts/wiki_remind.py     # 项目级安装
```

若要用全局安装的那个（用户级安装场景），才需要指定项目目录：

```bash
# Unix
CLAUDE_PROJECT_DIR=/path/to/project bash ~/.claude/scripts/wikiskill/wiki_remind.sh

# Windows (PowerShell)
$env:CLAUDE_PROJECT_DIR="C:\path\to\project"
python "$env:USERPROFILE\.claude\scripts\wikiskill\wiki_remind.py"
```

真实 Claude Code 下该变量由平台自动注入，无需手动设置。

> **脚本如何定位项目**：三级 fallback —— `CLAUDE_PROJECT_DIR` → 当前工作目录 → **脚本自身位置**。
> 第三级是关键：项目级安装时脚本位于 `<项目>/.wiki/scripts/`，上溯两级即项目根。
> 某些沙箱化 shell 在启动子进程时会 `cd` 回工作区，导致前两级同时失效，
> 第三级保证脚本在任何环境下都能找到自己的项目。

---

## 常见问题

**会拖慢 Agent 吗？**

记录轨迹每次只写几行文本，开销可忽略。复盘是离线周期性做的，不影响日常任务。

**多久复盘一次？**

论文建议：每 3–5 个任务做一次 Wiki 维护，每 5–10 个任务做一次技能提案。个人开发不必严格——攒几天做一次就行，别让它变成负担。

**能跨项目共享经验吗？**

可以。`.wiki/` 是项目级的，但你可以手动把通用性强的 `skills/*.md` 复制到其他项目的 `.wiki/skills/` 下。项目特有的坑（比如某个省平台接口字段）留在本项目。

**第一步该做什么？**

**别等自动流程跑起来。** 直接把你已经知道的坑手动写进 `.wiki/knowledge/patterns.md`——你现在就能想到几个（某个库的怪癖、某个 API 的参数陷阱、某次 debug 了很久的根因）。立刻可用，比等四步循环现实得多。

**和 CLAUDE.md / 项目记忆有什么区别？**

CLAUDE.md 是**静态的、人工维护的**项目说明。WikiSkill 多两样东西：一是**执行轨迹**（记录了"当时到底发生了什么"，而不只是结论），二是**失败提案的历史**（记录"试过什么、为什么不行"）。这第二点是论文的关键发现——失败经验同样有价值。

**必须用四步循环吗？**

不用。只用 Step 1 + Step 2（记录 + 复盘）就能获得大部分价值。Step 3/4（技能进化 + 门控）是进阶用法，需要你投入判断力。

---

## 文件清单

```
wikiskill/
├── SKILL.md                      # Agent 读的主文档（三层架构 + 四步循环）
├── README.md                     # 本文件
├── scripts/
│   ├── install.py                # 统一安装器（推荐入口，项目自包含）
│   ├── wiki_init.py              # 初始化 .wiki/（全平台，推荐）
│   ├── wiki_init.sh              # 初始化 .wiki/（Unix）
│   ├── wiki_init.ps1             # 初始化 .wiki/（Windows PowerShell）
│   ├── wiki_remind.py            # Stop hook 提醒（全平台，Windows 必用）
│   ├── wiki_remind.sh            # Stop hook 提醒（Unix）
│   └── install_claude_hook.py    # 已弃用，保留仅为兼容旧文档
├── references/
│   ├── workflow.md               # 三角色详细职责
│   ├── platforms.md              # 跨平台适配指南
│   ├── automation.md             # 自动化方案 + prompt 模板
│   ├── templates.md              # Markdown 模板集合
│   ├── CLAUDE.example.md        # Claude Code 配置模板
│   └── AGENTS.example.md        # Codex 配置模板
└── assets/hooks/
    ├── claude-code-settings.json          # hook 手动配置模板（Unix）
    └── claude-code-settings.windows.json  # hook 手动配置模板（Windows）
```

`SKILL.md` 给 Agent 读，`README.md` 给人读。

---

## 论文

Google Research, 2026-08-27. *WikiSkill: Accumulating Experience in Persistent Knowledge Libraries for AI Agents*. Tang et al. [arXiv:2608.27454](https://arxiv.org/abs/2608.27454)

思想来源是 Andrej Karpathy 提出的 "LLM Wiki" 概念。
