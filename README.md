# Agent 自改进 Skill 集合

一组围绕 **AI 自我改进（RSI / Recursive Self-Improvement）** 与 **Agent 经验积累** 的 Skill 合集。
目标：让 AI 不再靠人类一遍遍手把手调参，而是形成「试错 → 验证 → 沉淀经验 → 改进自己」的闭环，
并在 **不同电脑、不同 agent（WorkBuddy / CodeBuddy / Claude Code / Codex）** 下都能复用。

本仓库是 Skill 的**组织与分发**集合；实际使用时把对应 skill 文件夹安装/复制到 agent 的 skills 目录即可。

---

## 目录

- [三个 Skill 的定位与关系](#三个-skill-的定位与关系)
- [Skill 索引](#skill-索引)
- [目录结构](#目录结构)
- [跨平台 / 跨 agent 说明](#跨平台--跨-agent-说明)
- [路径关系说明（是否要调整）](#路径关系说明是否要调整)
- [如何开始](#如何开始)

---

## 三个 Skill 的定位与关系

三者**层级不同、不冲突、强互补**，构成一条引用链：

```
认知 (rsi-knowledge)  ──►  设计 (rsi-self-improvement-designer)  ──►  实现 (wikiskill)
  RSI 是什么？定级         给项目画自改进闭环            闭环里「沉淀经验」这步
  L 几？HCI 缺口？               ↓ 引用                 直接套 .wiki/ 三层架构
                         复用 wikiskill 落地
```

| 层级 | Skill | 解决「什么」 | 抽象层级 |
|---|---|---|---|
| 认知 | `rsi-knowledge` | RSI 是什么、怎么度量、大厂到 L 几 | 知识/标尺层 |
| 设计 | `rsi-self-improvement-designer` | 拿框架给真实项目套出自改进方案 | 方法层 |
| 实现 | `wikiskill` | 把「经验沉淀」落成一个可跑的 `.wiki/` 系统 | 机制/工具层 |

> **关键洞察**：`wikiskill` 的「门控验证 + 失败回滚」机制，正是 RSI「四大追问」（可衡量/可保持/可迁移/可回滚）在 Agent 自身技能进化上的工程化身。
> 三者逻辑串成链、物理各独立——这样既不重复造轮子，又保持跨平台可迁移。

---

## Skill 索引

### 1. `rsi-knowledge` — RSI 知识与方法论库
- **是什么**：RSI 概念、HCI 能力余量闭合指数、L1–L5 自主权框架、大厂进度、产业实测数据的可查询知识底座。
- **何时用**：解释 RSI 定义、引用 HCI/L1–L5/四大追问、引用产业数据。
- **详细说明**：[rsi-knowledge/README.md](./rsi-knowledge/README.md) ｜ Agent 入口：[rsi-knowledge/SKILL.md](./rsi-knowledge/SKILL.md)

### 2. `rsi-self-improvement-designer` — RSI 自改进工作流设计器
- **是什么**：套 RSI 框架 + 环境-数据-模型四步闭环，为任意项目设计可运行的自改进方案。
- **何时用**：想给代码库/AI 工具加「自改进闭环」、评估自主权成熟度（L1–L5）。
- **详细说明**：[rsi-self-improvement-designer/README.md](./rsi-self-improvement-designer/README.md) ｜ Agent 入口：[rsi-self-improvement-designer/SKILL.md](./rsi-self-improvement-designer/SKILL.md)

### 3. `wikiskill` — Agent 经验积累与技能进化框架
- **是什么**：把 Google WikiSkill 论文落地为 `.wiki/` 三层架构（Raw→Wiki→Skill），带验证-回滚，跨平台通用。
- **何时用**：让 Agent 从历史任务学习、避免重复踩坑、沉淀可复用技能。
- **详细说明**：[wikiskill/README.md](./wikiskill/README.md) ｜ Agent 入口：[wikiskill/SKILL.md](./wikiskill/SKILL.md)

---

## 目录结构

```
2026-08-31-10-22-01/                # 本集合仓库
├── README.md                       # 本文件（集合索引，解释全部 Skill）
├── rsi-knowledge/                  # Skill 1（一个文件夹）
│   ├── SKILL.md                    # Agent 读的主文档
│   ├── README.md                   # 人类可读说明
│   └── references/
│       └── rsi-reference.md        # 完整参考（概念→度量→框架→产业→四大追问→四步闭环）
├── rsi-self-improvement-designer/  # Skill 2（一个文件夹）
│   ├── SKILL.md
│   ├── README.md
│   └── references/
│       └── design-playbook.md      # 设计手册（五步详解 + 模板 + 跨平台约束）
├── wikiskill/                      # Skill 3（一个文件夹）
│   ├── SKILL.md
│   ├── README.md
│   ├── scripts/                    # 安装器与初始化/hook 脚本（跨平台）
│   ├── references/                 # 模板、平台指南、自动化方案
│   └── assets/hooks/               # hook 手动配置模板
├── wikiskill.zip                   # wikiskill 分发压缩包（同上结构）
├── rsi-knowledge.zip               # rsi-knowledge 分发压缩包（新增）
├── rsi-self-improvement-designer.zip  # rsi-self-improvement-designer 分发压缩包（新增）
├── skill_state/                    # wikiskill 配套的状态机 Python 实现
├── test_integration_smoke.py       # 集成冒烟测试
└── test_triage_state.py            # 状态机测试
```

> 每个 Skill 一个文件夹，内部 `SKILL.md` 给 Agent 读、`README.md` 给人读、`references/` 放详版资料。
> 分发时直接压缩对应文件夹即可（见 `*.zip`）。

---

## 跨平台 / 跨 agent 说明

本集合刻意保持**平台中立**，不锁定单一 agent：

| Skill | WorkBuddy / CodeBuddy | Claude Code | Codex |
|---|---|---|---|
| `rsi-knowledge` | SKILL.md 按需触发 | 复制 SKILL.md 到 `~/.claude/skills/` | 复制 SKILL.md 到 agent skills 目录 |
| `rsi-self-improvement-designer` | SKILL.md 按需触发 | 同上 | 同上 |
| `wikiskill` | 零配置可用 | 用 `scripts/install.py --platform claude` | 用 `scripts/install.py --platform codex` |

- `rsi-knowledge` 与 `rsi-self-improvement-designer` 是纯知识/方法 skill，**无任何私有目录依赖**，跨 agent 直接复制 `SKILL.md` + `references/` 即可。
- `wikiskill` 的 `.wiki/` 目录与运行时脚本**项目自包含、可提交 Git**，换电脑 clone 后无需重装；经验沉淀跨 agent 共享。
- `rsi-self-improvement-designer` 在「沉淀经验」步骤直接复用 `wikiskill` 的 `.wiki/`，避免另造轮子、不硬编码 `~/.workbuddy/` 等私有路径。

---

## 路径关系说明（是否要调整）

**结论：无需调整路径关系，原结构可直接并入集合。**

- 两个 RSI skill 内部只用**相对路径**（如 `references/rsi-reference.md`、`references/design-playbook.md`），复制到本集合子文件夹后相对结构完好，不会断链。
- 跨 skill 引用（designer 引用 `rsi-knowledge`、`wikiskill`）均按 **skill 名称** 在运行时解析，不写死绝对路径，因此无论 skill 装在 `~/.workbuddy/skills/`、`~/.claude/skills/` 还是项目内，都能正确解析。
- 唯一注意点：本集合内的 `SKILL.md` 是「源/分发副本」，与你机器上 `~/.workbuddy/skills/` 里**实际生效**的那份是两份独立文件。修改后若需两边一致，请同步更新（或只改生效那份、重新打包）。

---

## 如何开始

1. **只想了解 RSI**：读 [rsi-knowledge/README.md](./rsi-knowledge/README.md)。
2. **想给某项目设计自改进闭环**：读 [rsi-self-improvement-designer/README.md](./rsi-self-improvement-designer/README.md)，按五步流程产出方案。
3. **想落地「经验沉淀」**：用 [wikiskill/README.md](./wikiskill/README.md) 的「60 秒快速开始」初始化项目的 `.wiki/`。
4. **分发/备份**：直接取对应 `*.zip`，或 `git` 提交整个仓库。

---

## 知识来源

- Theseus Labs《The Last AI Built by Humans》RSI 行业分析报告（2026-09），arXiv:2609.11873
- Google Research WikiSkill 论文 arXiv:2608.27454（wikiskill 部分）
