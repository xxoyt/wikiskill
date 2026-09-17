---
name: skill-evolution
description: Agent 经验沉淀与技能进化框架（三模块合一）。① 经验沉淀——把任务轨迹写入项目 .wiki/，提炼失败模式与成功策略，迭代为可回滚的技能；② 自改进设计——用 RSI 五级自主权与"环境-数据-模型"四步闭环，为项目设计可落地的自改进工作流；③ RSI 判据——提供 HCI 能力余量闭合指数、L1–L5 分级、四大评估追问，判断"什么才算真的变强"。支持 WorkBuddy / CodeBuddy / Claude Code / Codex 四平台与 Windows / Linux / macOS。当用户要求经验复盘、记录轨迹、技能进化、能力评估、自改进闭环设计、自主性分级，或引用 RSI / HCI 相关概念时触发。
version: 1.0.0
agent_created: true
---

# Skill Evolution — Agent 经验沉淀与技能进化框架

不改模型权重，让 Agent 自己维护一本经验 Wiki，把成败提炼为可复用技能，通过验证-回滚机制安全迭代。

本 skill 由三个模块构成，**纵向分工、依次衔接**：

| 模块 | 参考文档 | 回答的问题 | 是否写文件 |
|------|---------|-----------|:---------:|
| ① **RSI 判据** | `references/rsi-framework.md` | 什么才算**真的**变强？该往哪投？ | ❌ 只读 |
| ② **自改进设计** | `references/design-playbook.md` | 怎么把它落成**可运行的闭环**？ | ❌ 只出方案 |
| ③ **经验沉淀** | `references/workflow.md` | 经验**怎么存住**、怎么回滚？ | ✅ 唯一写盘方 |

> 本 skill 由 `wikiskill` + `rsi-knowledge` + `rsi-self-improvement-designer` 三合一而来。
> 只做经验沉淀时看模块③即可；只做能力体检时看模块①②。

---

## ⚠️ 角色隔离约束（最重要，不可放松）

WikiSkill 论文用消融实验证明：**执行任务的 Agent 一旦能访问 wiki，技能开发质量反而下降**（混淆变量）。
因此本框架强制角色隔离：

| 角色 | 何时 | 能读 wiki 吗 | 做什么 |
|------|------|:-----------:|--------|
| **Inference Agent** | 日常任务执行中 | ❌ **不能** | 只干活 + 记录轨迹 |
| **Wiki Maintainer** | 离线周期复盘 | ✅ 能 | 提炼 patterns |
| **Skill Proposer** | 离线周期进化 | ✅ 能 | 提技能改进、走门控 |

**三合一后这条约束依然有效**：即使三个模块现在同属一个 skill，执行任务的 Agent 也**不得**
顺手读 `.wiki/knowledge/` 或 `.wiki/skills/` 来"指导当前任务"。这是设计红线，不是建议。

---

## 模块③：经验沉淀（核心工作流，四步循环）

### 目录结构

```
.wiki/                          # 项目级 Wiki 根目录
├── raw/                        # Raw Layer — 不可变的执行轨迹
│   └── YYYY-MM-DD.md           # 按日期追加
├── knowledge/                  # Wiki Layer — 持久化知识（只增不减）
│   ├── patterns.md             # 失败模式 + 成功策略
│   ├── evolution_log.md        # 技能演化日志
│   └── impact_tracker.md       # 提案验证结果追踪
├── skills/                     # Skill Layer — 可回滚的执行指令
│   └── <skill-name>.md         # 每个技能一个文件
└── meta/
    └── config.md               # Wiki 配置（当前任务域、迭代周期等）
```

### Step 1: 执行并记录（Inference Agent）

执行任务时，在 `.wiki/raw/YYYY-MM-DD.md` 末尾追加轨迹：

```markdown
### [HH:MM] 任务简述
- **域**：[coding/data/research/debug/...]
- **结果**：✅ 成功 / ❌ 失败 / ⚠️ 部分成功
- **轨迹**：
  1. [关键步骤 1] → [结果]
  2. [关键步骤 2] → [结果]
- **关键观察**：[遇到了什么意外、用了什么技巧]
```

**原则**：只记关键决策点和异常，不记流水账。每条轨迹控制在 10 行以内。

### Step 2: 知识提炼（Wiki Maintainer）

每完成 3-5 个任务后，或用户说"复盘/维护 wiki/提炼经验"时：

1. 读取 `.wiki/raw/` 最近的轨迹
2. 识别重复出现的模式（错误 ≥2 次即为模式）
3. 更新 `.wiki/knowledge/patterns.md`：

```markdown
## 失败模式

### FM-[编号]: [简短名称]
- **触发条件**：[什么情况下出现]
- **表现**：[具体症状]
- **根因**：[为什么]
- **解决方案**：[如何避免/修复]
- **发现日期**：YYYY-MM-DD | **出现次数**：N

## 成功策略

### SS-[编号]: [简短名称]
- **适用场景**：[什么情况下有效]
- **具体做法**：[步骤]
- **验证案例**：[日期]
```

4. 在 `evolution_log.md` 追加一条维护记录

### Step 3: 技能提案（Skill Proposer）

当 patterns 中积累了足够洞察（或用户说"进化技能/更新技能"）时：

1. 读取 `patterns.md` + `impact_tracker.md`
2. 提出**一个原子化改进**，写入 `.wiki/skills/` 或修改现有技能文件：

```markdown
---
name: [技能名]
version: 1.x
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
source_patterns: [FM-001, SS-002]
---
# [技能名]
## 适用场景
## 执行步骤
## 注意事项
## 变更历史
```

> `source_patterns` 字段等价于论文中 `PURPOSE.md` 的作用——把技能映射回启发它的 Wiki 模式。

3. 在 `impact_tracker.md` 记录提案：

```markdown
### PROP-[编号] | [日期]
- **目标**：[改了什么]
- **依据**：[引用 patterns]
- **验证任务**：[用哪些任务测试]
- **结果**：待验证 / ✅ 采纳 / ❌ 回滚
- **效果**：[量化或定性对比]
```

### Step 4: 门控验证

在后续 2-3 个类似任务中测试新技能：
- **通过**：更新 impact_tracker 为"采纳"，技能保留
- **失败**：回滚技能文件到上一版本（从变更历史恢复），但 **Wiki 不动**——失败原因写入 patterns，成为下一轮提案的输入

---

## 模块②：自改进设计（设计时必须对齐）

完整五步工作流见 `references/design-playbook.md`。

### 五级自主权（人类退出 / AI 接管 的梯度）

| 级别 | 名称 | 人类负责 | AI 闭环接管 |
|---|---|---|---|
| L1 | 执行自主 | 设计任务、环境、更新策略 | 执行任务、更新 |
| L2 | 策略自主 | 设计任务、环境 | 设计更新策略（策略持久化） |
| L3 | 经验获取自主 | 设计环境 | 规划经验获取、执行、设计更新策略（经验设计持久化） |
| L4 | 环境适应自主 | 设定边界 | 与环境交互、设计更新策略（环境适应持久化） |
| L5 | 递归继承自主 | 设定边界 | 改进"改进系统本身"（系统设计持久化） |

### 环境-数据-模型四步闭环

1. **重构环境**：把原始工作区还原成可供 Agent 训练/评估的环境
2. **暴露缺口**：借新环境发现真实能力缺口，生成训练数据
3. **再训练/沉淀**：用生成数据训练任务模型；经验沉淀复用模块③的 `.wiki/`（Raw→Wiki→Skill，带验证-回滚）
4. **迭代环境**：用更强模型推动下一轮环境迭代

### 四大评估追问（避免"一次性刷榜"式伪改进）

- **可衡量**：独立评估下能否复现？
- **可保持**：改进能否持久不退化？
- **可迁移**：能否跨任务/领域复用？
- **可回滚**：失效时能否安全撤回？

> 这正是本 skill 模块③「门控验证」的理论依据。

### 设计工作流（五步）

1. **定位现状**：对照 L1–L5 判定当前级别，定下一步目标
2. **选落地切口**：按"反馈成本 / 可验证性 / 部署约束"三维选最优任务
3. **设计闭环**：套四步闭环，落到具体工程动作
4. **定义验收**：用四大追问为每个改进设独立验证与回滚
5. **输出方案**：按模板产出结构化文档

---

## 模块①：RSI 判据速查

完整概念、公式、产业数据与四大追问见 `references/rsi-framework.md`。

### HCI 能力余量闭合指数

```
HCI = 100 × (共识得分 − 基准前沿) ÷ (100 − 基准前沿)
```

- **基准前沿** = 该基准**进入数据集首年的第 90 百分位模型分**
- **共识得分** = 按数据源加权，以抑制自报结果偏差
- 尺度：0 = 与基准年持平，100 = 追平满分

### 最具操作性的实测结论

| 能力域 | HCI | 含义 |
|--------|----:|------|
| 网络安全 Agent | 91.9 | 已接近饱和 |
| 前沿数学 | 86.4 | 标准化考试类，红利见顶 |
| 研究生级科学 | 85.8 | 同上 |
| **软件工程** | **52.6** | **缺口大 = RSI 红利最高** |
| **工具调用 Agent** | **39.9** | **缺口最大，与网络安全 Agent 相差 52.0 点** |

结论：**真实任务执行类能力缺口远大于标准化考试类**。软件工程与工具型 Agent 之所以成为各家发力第一站，
是因为**反馈廉价、验证明确、部署链路短**，RSI 循环最容易闭合——这也是本框架推荐的首选落地领域。

---

## 快速命令（触发词）

| 触发词 | 动作 | 所属模块 |
|--------|------|:--------:|
| "记录轨迹" / "wiki log" | 执行 Step 1，追加当前任务轨迹到 raw | ③ |
| "复盘" / "wiki maintain" | 执行 Step 2，提炼 patterns | ③ |
| "进化技能" / "wiki evolve" | 执行 Step 3+4，提出并验证技能改进 | ③ |
| "wiki 状态" / "wiki status" | 展示当前 Wiki 统计（轨迹数、模式数、技能数） | ③ |
| "初始化 wiki" / "wiki init" | 创建 `.wiki/` 目录结构（用 `scripts/wiki_init.py`，全平台通用） | ③ |
| "自改进设计" / "闭环设计" | 走模块②的五步工作流，产出原子化自改进方案 | ② |
| "RSI 体检" / "能力评估" | 按模块①的 L1–L5 与四大追问做诊断 | ① |

---

## 跨平台使用

本 skill 的核心是 `.wiki/` 目录结构与 Markdown 格式，与平台无关。

| 平台 | 自动调用机制 | Windows | Linux | macOS |
|------|-------------|:------:|:-----:|:-----:|
| WorkBuddy | 定时 automation（持久，已验证）；触发词自动识别 | ✅ | ✅ | ✅ |
| CodeBuddy | **IDE / 插件无定时任务**；CodeBuddy Code（CLI）的定时为**会话级**（退出即清除、3 天过期、中断不补跑），持久周期需 **headless + 外部调度器** | ✅ | ✅ | ✅ |
| Claude Code | `CLAUDE.md` 常驻指令（用 `references/CLAUDE.md.template`）+ Stop hook 提醒 | ✅ | ✅ | ✅ |
| Codex | `AGENTS.md` 常驻指令（用 `references/AGENTS.md.template`）+ git `post-commit` 提醒 | ✅* | ✅ | ✅ |

\* Codex 在 Windows 上依赖 Git for Windows 自带的 bash 运行 git hook。

所有平台共享同一个 `.wiki/` 目录，经验可跨平台迁移。详见 `references/platforms.md`。

---

## 从旧版迁移

**触发信号**（出现任一条即需迁移）：

- 用户提到自己装过 `wikiskill` / `rsi-knowledge` / `rsi-self-improvement-designer`；
- `~/.workbuddy/skills/` 下仍存在上述任一目录；
- `~/.claude/settings.json` 的 `hooks.Stop` 命令指向 `scripts/wikiskill/` 或包含旧 skill 名；
- 项目内 `CLAUDE.md` / `AGENTS.md` 引用了 `~/.workbuddy/skills/wikiskill/...` 之类的旧路径。

**四步动作**：

| 步骤 | 做什么 |
|------|--------|
| 1. 归档 | 把三个旧 skill 目录整体移入 `~/.workbuddy/skills_archived/<日期>_merged_into_skill-evolution/`（已存在则跳过，不删除） |
| 2. 换 hook | `python <skill目录>/scripts/install.py --platform claude --user`（自动替换旧命令，保留其余配置） |
| 3. 改引用 | 项目内 `CLAUDE.md` / `AGENTS.md` 里的旧 skill 路径 → 项目内 `.wiki/references/`；定时任务 prompt 里的旧 skill 名 → `skill-evolution` |
| 4. 自检 | 见下表 |

**项目内已有 `.wiki/` 时：数据不用迁移。** `.wiki/` 是项目级的，且目录名与文件格式
从旧版到新版从未改变，新 skill 直接读写同一份、无缝续用。只需刷新项目内那份运行时快照：

```bash
python <skill目录>/scripts/install.py --platform claude --target <项目目录> --no-hook
```

`raw/`、`knowledge/`、`skills/` 完全不碰；`scripts/` 与 `references/` 刷新为新版；
已有的 `CLAUDE.md` / `AGENTS.md` 跳过不覆盖。加 `--no-hook` 是为了保留项目里已有的
hook 配置（例如其他插件注入的 `SessionStart`），只刷运行时、不动配置。

**硬红线**：不删除、不重命名 `.wiki/` 目录，不改动 `.wiki/scripts/` 与 `.wiki/knowledge/`
下的文件名——目录名 `.wiki/`、脚本名 `wiki_init.py` / `wiki_remind.py` 是**跨项目的运行时契约**，
改名会让所有已初始化的项目失效。

迁移后自检：`~/.workbuddy/skills/` 只剩 `skill-evolution`；hook 指向 `scripts/skill-evolution/wiki_remind.py`；
旧项目 `.wiki/` 内容一字未变；说「记录轨迹」「复盘」能正常触发。

> 完整操作手册（含可直接粘贴给 AI 的迁移指令、分平台步骤、回滚方式）见 `README.md` 的「从旧版迁移」。

---

## 自动化运行

自动化的可行度分四层，不要试图全自动：

| 层次 | 能否自动 | 方案 |
|------|---------|------|
| L1 指令常驻 | ✅ 能 | CLAUDE.md / AGENTS.md 全量加载 |
| L2 自动记录轨迹 | ✅ 能 | Claude Code Stop hook / git hook |
| L3 周期复盘进化 | ✅ 能 | WorkBuddy 定时 automation（CodeBuddy 需 headless + 外部调度器，见下注） |
| L4 门控验证 | ❌ **不能** | 需人判断，设计如此 |

**核心原则**：论文里 Wiki 维护是离线批量做的，Inference Agent 执行时不读 Wiki。对应到实践——
**在线**（每次任务）只做 L2 记录，**离线**（周期性）做 L3 复盘进化。别在每次任务里跑完整四步循环。

**三种自动化方案**：

1. **WorkBuddy 定时复盘**（推荐）：创建定时任务周期性跑 Step 2/3/4，或跑三模块联合编排。prompt 模板见 `references/automation.md`。**CodeBuddy 不能直接套用**：其定时任务仅存在于 CodeBuddy Code（CLI），且为会话级；若要在 CodeBuddy 上做持久周期，改用 headless 模式 `codebuddy -p -y "<prompt>"` + 外部调度器（Windows 计划任务 / cron / GitHub Actions），或退回 Git Hook + 手动触发词兜底。
2. **Claude Code Hook**：会话结束时自动提醒记录轨迹。安装：
   ```bash
   # 项目级（推荐）：hook 用相对路径，项目自包含，可提交 Git
   python <skill目录>/scripts/install.py --platform claude --target <项目目录>

   # 用户级：运行时装到 ~/.claude/scripts/skill-evolution/，对所有项目生效
   python <skill目录>/scripts/install.py --platform claude --user
   ```
   安装器会**合并**而非覆盖已有配置（保留 permissions、其他 hooks）；若已存在**命令相同**的
   hook 则跳过，若存在**指向旧目录**（如 `scripts/wikiskill/`）的 hook 则**自动替换**为当前命令。
   `--uninstall` 可精确移除（不删除 `.wiki/` 数据）。它还会探测 `python` / `python3` / `py -3`，
   避免机器上没装 `python` 命令时静默失效。
3. **Git Hook**（跨平台通用）：`post-commit` 里加提醒，任何工具链都能用。

**注意**：L4 门控验证不建议自动化。判断"技能改进是否真的有用"需要人看实际效果；强行自动化会导致无效技能污染技能库。

### 三模块联合自动化

`references/automation.md` 提供三种粒度的自包含 prompt：**联合编排**（①②③全跑）、**仅 RSI 体检**、**仅自改进设计**。
三合一本 skill 后，它们都在同一份文档里，可直接粘进任意平台的周期任务。
整条链只有模块③写文件，因此可被定时任务安全驱动；唯一的人工介入点是最后的门控验证。

---

## 关键原则

1. **角色隔离**：执行任务的 Agent 不读 Wiki（论文消融实证，见上文红线）
2. **Wiki 永不重置**：即使技能回滚，知识层只增不减
3. **原子化改进**：每轮只改一个技能，便于归因
4. **失败也是知识**：被拒绝的提案记录原因，成为下一轮输入
5. **轻量记录**：轨迹不记流水账，只记决策点和异常
6. **验证后才采纳**：所有技能变更必须经过门控
7. **只靠自评分宣称进步无效**：必须在独立评估下确认

---

## 参考资源

| 文档 | 内容 |
|------|------|
| `references/rsi-framework.md` | 模块①：RSI 概念 / HCI 度量 / L1–L5 / 产业实践数据 |
| `references/design-playbook.md` | 模块②：自改进设计五步工作流与方案模板 |
| `references/workflow.md` | 模块③：三角色详细职责 |
| `references/automation.md` | 自动化方案 + 三种粒度的 prompt 模板 |
| `references/platforms.md` | 跨平台适配指南（跨 OS 路径陷阱的唯一权威源） |
| `references/templates.md` | Markdown 模板集合 |
| `README.md` | **给人读**的操作手册（哪些自动 / 哪些手动 / 什么时候做 / 具体怎么做） |

### 脚本

| 脚本 | 用途 | 适用 shell |
|------|------|-----------|
| `scripts/install.py` | **统一安装器**（项目自包含，推荐入口） | 全平台 |
| `scripts/wiki_init.py` | 初始化 `.wiki/` | Windows CMD / PowerShell、Linux、macOS |
| `scripts/wiki_init.sh` | 初始化 `.wiki/` | Linux / macOS / **Git Bash** / WSL |
| `scripts/wiki_init.ps1` | 初始化 `.wiki/` | Windows PowerShell 原生 |
| `scripts/wiki_remind.py` | Stop hook 提醒脚本 | 全平台（Windows 必用） |
| `scripts/wiki_remind.sh` | Stop hook 提醒脚本 | Unix |

**Windows 路径陷阱（必读）**：CMD/PowerShell 原生环境没有 bash，`.sh` 跑不了；
反过来，**在 Git Bash 里不能用 `python "$HOME/..."`**——Git Bash 的 `$HOME` 是
POSIX 格式（`/c/Users/xxx`），Windows 原生 Python 会解析成 `C:\c\Users\xxx`。

按 shell 选命令（下文的 `SKILL_DIR` = 本 skill 所在目录，换成实际路径即可）：

```powershell
# Windows PowerShell
python "$SKILL_DIR\scripts\wiki_init.py"
```
```cmd
:: Windows CMD
python "%SKILL_DIR%\scripts\wiki_init.py"
```
```bash
# Linux / macOS / Git Bash / WSL
bash "<skill目录>/scripts/wiki_init.sh"
```

**更省事的写法**——若项目已用 `install.py` 安装过，直接跑项目内脚本，
这条命令在所有 shell 下都成立（不含任何 `$HOME` 变量）：

```bash
python .wiki/scripts/wiki_init.py
```

Claude Code 在 Windows 上执行 hook 走 cmd.exe/PowerShell（**不走 Git Bash**），
因此提醒脚本必须用 `.py` 版本——安装器会自动处理。

> **不要用 `~/.workbuddy/skills/<skill名>/` 作为路径**。那是 WorkBuddy 的私有目录，
> Claude Code / Codex 用户机器上不存在。坚持用项目内路径或 `install.py`。
