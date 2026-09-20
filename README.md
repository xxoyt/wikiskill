# Agent 自改进 Skill

一个围绕 **AI 自我改进（RSI / Recursive Self-Improvement）** 与 **Agent 经验积累** 的 Skill。

目标：让 AI 不再靠人类一遍遍手把手调参，而是形成「试错 → 验证 → 沉淀经验 → 改进自己」的闭环，
并在 **不同电脑、不同 agent（WorkBuddy / CodeBuddy / Claude Code / Codex）** 下都能复用。

本仓库是 Skill 的**组织与分发**集合；实际使用时把 `skill-evolution/` 安装或复制到 agent 的 skills 目录即可。

> **2026-09-17 更新 —— 三个 skill 已三合一；随后按两篇论文重构成单一闭环（v2.0）。**
> 原先独立的 `rsi-knowledge` + `rsi-self-improvement-designer` + `wikiskill` 已合并为单一 skill
> **`skill-evolution`**。三合一只是「放进同一个 skill」，v2.0 又进一步按
> **WikiSkill ↔ RSI 的缺口互补关系**把它们重组成一条七步闭环——不再是三个并列模块。
> **旧版本完整保留在 [`archived/`](./archived/)，可随时回溯。**

---

## 目录

- [两篇论文合成的一条闭环](#两篇论文合成的一条闭环)
- [环节索引](#环节索引)
- [目录结构](#目录结构)
- [跨平台 / 跨 agent 说明](#跨平台--跨-agent-说明)
- [从旧版迁移](#从旧版迁移)
- [如何开始](#如何开始)
- [知识来源](#知识来源)

---

## 两篇论文合成的一条闭环

本 skill **不是「三个模块的集合」，而是两篇论文的合成体**。两篇各缺一半，缺口正好互补：

| | [WikiSkill](https://arxiv.org/abs/2608.27454) | [RSI 路线图](https://arxiv.org/abs/2609.11873) |
|---|---|---|
| 回答 | 经验**怎么存、怎么迭代** | 改进**算不算真的、能自动到哪** |
| 核心 | 三层记忆 Raw→Wiki→Skill；角色隔离；门控弧 | HCI 能力余量指数；L1–L5 自主权；四大评估追问 |
| **缺口** | 门控**只有一条阈值**，缺「什么样的改进才算数」的判据 | 判据齐备，却**没有可持续存储与回滚的载体** |

**结合方式**：RSI 的四大追问**成为** WikiSkill 门控的评分卡；WikiSkill 的三层**成为** RSI 闭环的沉淀载体。

```
① 选域 ──── RSI / HCI：挑缺口最大的域
   │
② 执行记录 ── Raw 层：只记轨迹，不读 wiki（角色隔离红线）
   │
③ 提炼 ──── Wiki 层：同类失败 ≥2 次即立为模式
   │
④ 原子化提议 ─ Skill 层：一轮只改一个技能
   │
⑤ 门控 ──── ★ 融合点：四大追问评分卡 + WikiSkill 阈值
   │
⑥ 采纳 / 回滚 ─ 技能可回滚；Wiki 永不回滚（失败原因写回 patterns）
   │
⑦ 自主权升阶 ─ RSI / L1–L5：判定下轮能把哪些环节交给 AI
   └──────────────────────────→ 回到 ①
```

**⑤ 是融合点**——WikiSkill 的门控只会问「新版比旧版强吗」，RSI 的四问补上「这个改进到底算不算数」：

| # | 追问 | 证据要求 | 不通过 |
|:-:|------|---------|--------|
| 1 | 可衡量 | ≥2 个同域任务、同判据独立复测 | 退回观察（**自评分不算**） |
| 2 | 可保持 | 间隔一个复盘周期后仍成立 | 降级为「未验证」 |
| 3 | 可迁移 | ≥1 个不同任务域或另一平台成功 | 降为项目局部技能 |
| 4 | 可回滚 | 有「变更历史」可恢复上一版 | **一票否决** |

**核心红线**：执行任务的 Agent **不得读 `.wiki/`**。
WikiSkill 论文的消融实验证明，执行代理一旦能访问知识库，技能开发质量反而下降。
整条闭环都遵守这条约束。

---

## 环节索引

### ① 选域 / ⑦ 升阶 —— RSI 那一半
- **是什么**：HCI 能力余量闭合指数、L1–L5 自主权分级、四大评估追问、产业实测数据的可查询底座。
- **何时用**：判断某能力域值不值得投自改进；评估项目自主权成熟度（当前 L 几、目标 L 几）。
- **触发词**：`选域` / `RSI 体检` / `能力评估`
- **详版**：[skill-evolution/references/rsi-framework.md](./skill-evolution/references/rsi-framework.md)

### 全链设计 —— 把 RSI 落到具体项目
- **是什么**：按 HCI 定域 + 三因素（反馈成本 / 可验证性 / 部署约束）选切口 + 四步闭环 + 四问验收。
- **何时用**：想给代码库 / AI 工具加「自改进闭环」。
- **触发词**：`自改进设计` / `闭环设计`
- **详版**：[skill-evolution/references/design-playbook.md](./skill-evolution/references/design-playbook.md)

### ②③④⑤⑥ 经验沉淀 —— WikiSkill 那一半
- **是什么**：`.wiki/` 三层架构（Raw → Wiki → Skill）+ 四问门控 + 双轨回滚，跨平台通用。
- **何时用**：让 Agent 从历史任务学习、避免重复踩坑、沉淀可复用技能。
- **触发词**：`记录轨迹` / `复盘` / `进化技能` / `wiki 状态` / `初始化 wiki`
- **详版**：[skill-evolution/README.md](./skill-evolution/README.md)

Agent 入口：[skill-evolution/SKILL.md](./skill-evolution/SKILL.md)

---

## 目录结构

```
2026-08-31-10-22-01/                # 本集合仓库
├── README.md                       # 本文件（集合索引）
├── skill-evolution/                # 唯一在用的 Skill（一个文件夹）
│   ├── SKILL.md                    # Agent 读的主文档（七步闭环 + 四问评分卡 + 角色隔离）
│   ├── README.md                   # 人类可读说明（含迁移指引与操作手册）
│   ├── scripts/                    # 统一安装器 + 初始化 / hook 脚本（跨平台）
│   │   ├── install.py              # 项目自包含安装（claude / codex / workbuddy）
│   │   ├── wiki_init.{py,sh,ps1}   # 初始化 .wiki/
│   │   └── wiki_remind.{py,sh}     # Stop hook 提醒
│   ├── references/                 # 详版资料与指令模板
│   │   ├── rsi-framework.md        # ① 选域 / ⑦ 升阶（HCI、L1–L5）
│   │   ├── design-playbook.md      # ② 自改进设计
│   │   ├── workflow.md             # ③ 经验沉淀三角色职责
│   │   ├── platforms.md            # 跨平台适配
│   │   ├── automation.md           # 自动化方案 + prompt 模板（含全链联合编排）
│   │   ├── templates.md            # Markdown 模板集合
│   │   └── CLAUDE.md.template / AGENTS.md.template
│   └── assets/hooks/               # hook 手动配置模板
├── skill-evolution.zip             # 分发压缩包（同上结构）
├── archived/                       # 三合一之前的旧 skill（保留追溯，不再维护）
│   ├── wikiskill/  + wikiskill.zip
│   ├── rsi-knowledge/  + rsi-knowledge.zip
│   └── rsi-self-improvement-designer/  + rsi-self-improvement-designer.zip
├── skill_state/                    # σt 状态机 Python 实现（独立项目配套，与 skill 无关）
├── test_integration_smoke.py       # 集成冒烟测试
└── test_triage_state.py            # 状态机测试
```

> `SKILL.md` 给 Agent 读，`README.md` 给人读，`references/` 放详版资料。
> 分发时直接压缩对应文件夹即可（见 `*.zip`）。

---

## 跨平台 / 跨 agent 说明

本集合刻意保持**平台中立**，不锁定单一 agent：

| 平台 | 用法 | Windows | Linux | macOS |
|---|---|---|---|:---:|
| WorkBuddy / CodeBuddy | 放到 skills 目录即零配置可用，触发词自动识别 | ✅ | ✅ | ✅ |
| Claude Code | `python skill-evolution/scripts/install.py --platform claude --target <项目>` | ✅ | ✅ | ✅ |
| Codex | `python skill-evolution/scripts/install.py --platform codex --target <项目>` | ✅ | ✅ | ✅ |

- **零私有目录依赖**：安装器不写死 `~/.workbuddy/` 等路径，用户级安装时运行时复制到
  `~/.claude/scripts/skill-evolution/` 或 `~/.codex/scripts/skill-evolution/`，
  项目级安装则完全自包含——`.wiki/` 与运行时都在项目内，可整体提交 Git，换机器 clone 后无需重装。
- **经验跨平台共享**：`.wiki/` 是纯 Markdown + 固定目录名，同一份数据可被四个 agent 共用。
- **`.wiki/` 与脚本名是契约**：目录名 `.wiki/`、脚本名 `wiki_init.py` / `wiki_remind.py`
  属于跨项目数据格式与运行时契约，**不可改名**，否则所有已初始化的项目与已装的 hook 都会失效。

CodeBuddy 注记：其 **IDE / 插件无定时任务**；CodeBuddy Code（CLI）的定时为**会话级**
（退出即清除、3 天过期、中断不补跑）。需要持久周期任务时改用 headless + 外部调度器。

---

## 从旧版迁移

如果你之前装的是三个独立 skill，README 里有一整节迁移指引，**核心结论是：经验数据不用迁移**。

`.wiki/` 是**项目级**的，不在 skill 包里，且目录名与文件格式从旧版到新版一个都没改——
`skill-evolution` 直接读写同一份 `.wiki/`，轨迹、模式、已进化的技能原样续用，**零迁移成本**。
需要做的只是刷新项目内那份旧运行时快照：

```bash
python skill-evolution/scripts/install.py --platform claude --target <项目目录> --no-hook
```

`--no-hook` 保留项目已有的 hook 配置（例如其他插件注入的 `SessionStart`），
只刷运行时、不动配置；`raw/`、`knowledge/`、`skills/` 完全不碰。

完整的迁移操作手册（含可直接粘贴给 AI 的迁移指令、分平台步骤、自检清单、回滚方式）见
[skill-evolution/README.md 的「从旧版迁移」](./skill-evolution/README.md#从旧版迁移已装过-3-个旧-skill)。

---

## 如何开始

1. **只想了解 RSI**：读 [references/rsi-framework.md](./skill-evolution/references/rsi-framework.md)。
2. **想给某项目设计自改进闭环**：读 [references/design-playbook.md](./skill-evolution/references/design-playbook.md)，按五步流程产出方案。
3. **想落地「经验沉淀」**：用 [skill-evolution/README.md](./skill-evolution/README.md) 的「60 秒快速开始」初始化项目的 `.wiki/`。
4. **分发 / 备份**：直接取 `skill-evolution.zip`，或 `git` 提交整个仓库。
5. **需要旧版**：到 [`archived/`](./archived/) 取三合一之前的独立 skill（不再维护）。

---

## 知识来源

- Google Research, *Compiling Agent Experience into Persistent Knowledge for Skill Evolution*（2026-08），arXiv:2608.27454 —— 模块③的理论基础
- Theseus Labs 等, *The Last AI Built by Humans: Toward Genuine Recursive Self-Improvement*（2026-09），arXiv:2609.11873 —— 模块①②的理论基础
