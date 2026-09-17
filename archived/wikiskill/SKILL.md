---
name: wikiskill
description: 将 Google WikiSkill 框架（arXiv:2608.27454）落地为可执行的本地化经验积累系统。让 Agent 在每次任务执行后自动记录轨迹、提炼失败模式与成功策略、迭代改进可复用技能。支持 WorkBuddy、CodeBuddy、Claude Code、Codex 四平台。当用户需要 Agent 从历史任务中学习、避免重复犯错、积累最佳实践、或执行"经验复盘/技能进化/wiki 维护"时触发。
agent_created: true
---

# WikiSkill — Agent 经验积累与技能进化框架

将 Google Research WikiSkill 论文的三层架构（Raw → Wiki → Skill）落地为文件系统级别的实践方案。核心思路：**不改模型权重，让 Agent 自己维护一本经验 Wiki，把成败提炼为可复用技能，通过验证-回滚机制安全迭代**。

## 目录结构

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

## 核心工作流（四步循环）

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

## 快速命令

用户可通过以下触发词启动对应流程：

| 触发词 | 动作 |
|--------|------|
| "记录轨迹" / "wiki log" | 执行 Step 1，追加当前任务轨迹到 raw |
| "复盘" / "wiki maintain" | 执行 Step 2，提炼 patterns |
| "进化技能" / "wiki evolve" | 执行 Step 3+4，提出并验证技能改进 |
| "wiki 状态" / "wiki status" | 展示当前 Wiki 统计（轨迹数、模式数、技能数） |
| "初始化 wiki" / "wiki init" | 创建 `.wiki/` 目录结构（优先用 `scripts/wiki_init.py`，全平台通用） |

## 跨平台使用

本 skill 的核心是 `.wiki/` 目录结构和 markdown 文件格式，与平台无关。

- **WorkBuddy / CodeBuddy**：直接按本 SKILL.md 执行
- **Claude Code**：将 `references/CLAUDE.example.md` 复制到项目根目录为 `CLAUDE.md`
- **Codex**：将 `references/AGENTS.example.md` 复制到项目根目录为 `AGENTS.md`

所有平台共享同一个 `.wiki/` 目录，经验可跨平台迁移。详见 `references/platforms.md`。

## 自动化运行

自动化的可行度分四层，不要试图全自动：

| 层次 | 能否自动 | 方案 |
|------|---------|------|
| L1 指令常驻 | 能 | CLAUDE.md / AGENTS.md 全量加载 |
| L2 自动记录轨迹 | 能 | Claude Code Stop hook / git hook |
| L3 周期复盘进化 | 能 | WorkBuddy 定时 automation |
| L4 门控验证 | 不能 | 需人判断，设计如此 |

**核心原则**：论文里 Wiki 维护是离线批量做的，Inference Agent 执行时不读 Wiki。对应到实践——在线（每次任务）只做 L2 记录，离线（周期性）做 L3 复盘进化。别在每次任务里跑完整四步循环。

**三种自动化方案**：

1. **WorkBuddy / CodeBuddy 定时复盘**（推荐）：创建定时任务周期性跑 Step 2/3/4。prompt 模板见 `references/automation.md`。
2. **Claude Code Hook**：会话结束时自动提醒记录轨迹。安装：
   ```bash
   # 项目级（推荐）：hook 用相对路径，项目自包含，可提交 Git
   python <skill目录>/scripts/install.py --platform claude --target <项目目录>

   # 用户级：运行时装到 ~/.claude/scripts/wikiskill/，对所有项目生效
   python <skill目录>/scripts/install.py --platform claude --user
   ```
   安装器会合并而非覆盖已有配置（保留 permissions、其他 hooks），重复安装自动跳过，
   `--uninstall` 可精确移除（不删除 `.wiki/` 数据）。

   **不要用 `install_claude_hook.py`**（已弃用）：它把 hook 指向
   `~/.workbuddy/skills/wikiskill/`，那是 WorkBuddy 私有目录。未安装 WorkBuddy 的
   机器上该路径不存在，hook 会静默失效。统一安装器不依赖任何 AI 工具的私有目录。
3. **Git Hook**（跨平台通用）：`post-commit` 里加提醒，任何工具链都能用。

**注意**：L4 门控验证不建议自动化。判断"技能改进是否真的有用"需要人看实际效果；强行自动化会导致无效技能污染技能库。

详见 `references/automation.md`。

## 关键原则

1. **Wiki 永不重置**：即使技能回滚，知识层只增不减
2. **原子化改进**：每轮只改一个技能，便于归因
3. **失败也是知识**：被拒绝的提案记录原因，成为下一轮输入
4. **轻量记录**：轨迹不记流水账，只记决策点和异常
5. **验证后才采纳**：所有技能变更必须经过门控

## 参考资源

- 详细工作流与角色说明：`references/workflow.md`
- 各平台适配模板：`references/platforms.md`
- **自动化运行方案**：`references/automation.md`
- Markdown 模板集合：`references/templates.md`

### 脚本

| 脚本 | 用途 | 适用 shell |
|------|------|-----------|
| `scripts/install.py` | **统一安装器**（项目自包含，推荐入口） | 全平台 |
| `scripts/wiki_init.py` | 初始化 `.wiki/` | Windows CMD / PowerShell、Linux、macOS |
| `scripts/wiki_init.sh` | 初始化 `.wiki/` | Linux / macOS / **Git Bash** / WSL |
| `scripts/wiki_init.ps1` | 初始化 `.wiki/` | Windows PowerShell 原生 |
| `scripts/wiki_remind.py` | Stop hook 提醒脚本 | 全平台（Windows 必用） |
| `scripts/wiki_remind.sh` | Stop hook 提醒脚本 | Unix |
| `scripts/install_claude_hook.py` | 已弃用，保留仅为兼容旧文档 | — |

**Windows 路径陷阱（必读）**：CMD/PowerShell 原生环境没有 bash，`.sh` 跑不了；
反过来，**在 Git Bash 里不能用 `python "$HOME/..."`**——Git Bash 的 `$HOME` 是
POSIX 格式（`/c/Users/xxx`），Windows 原生 Python 会解析成 `C:\c\Users\xxx`。

按 shell 选命令（`SKILL_DIR` = 本 skill 所在目录）：

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
bash "$SKILL_DIR/scripts/wiki_init.sh"
```

**更省事的写法**——若项目已用 `install.py` 安装过，直接跑项目内脚本，
这条命令在所有 shell 下都成立（不含任何 `$HOME` 变量）：

```bash
python .wiki/scripts/wiki_init.py
```

Git Bash 里若要引用 skill 目录，改用 `python "$USERPROFILE\..."` 或
`python "$(cygpath -w "$HOME")/..."`。

Claude Code 在 Windows 上执行 hook 走 cmd.exe/PowerShell（**不走 Git Bash**），
因此提醒脚本必须用 `.py` 版本——安装器会自动处理，还会探测
`python` / `python3` / `py -3`，避免机器上没有 `python` 命令时静默失效。

> **不要用 `~/.workbuddy/skills/wikiskill/` 作为路径**。那是 WorkBuddy 的私有目录，
> Claude Code / Codex 用户机器上不存在。坚持用项目内路径或 `install.py`。
