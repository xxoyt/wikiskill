# WikiSkill 自动化运行指南

## 自动化的四个层次

| 层次 | 能否自动 | 可行方案 | 成熟度 |
|------|---------|---------|--------|
| L1 指令常驻 | ✅ 能 | CLAUDE.md / AGENTS.md 全量加载 | 已实现 |
| L2 自动记录轨迹 | ✅ 能 | Claude Code Stop hook / git hook | 可配置 |
| L3 周期复盘进化 | ✅ 能 | WorkBuddy 定时 automation / cron | 可配置 |
| L4 门控验证 | ❌ 不能 | 需人判断"技能是否真的变好" | 设计如此 |

**核心原则**：论文里 Wiki 维护是**离线批量**做的，Inference Agent 执行时不读 Wiki。对应到实践——
- **在线**（每次任务）：只做 L2 记录，轻到无感
- **离线**（周期性）：做 L3 复盘和进化，批量处理

别试图在每次任务里跑完整四步循环，那是论文的训练流程，不是日常用法。

---

## 方案一：WorkBuddy / CodeBuddy 定时自动化（推荐主方案）

用 WorkBuddy 的定时任务，周期性跑 Step 2/3/4。这是最省心的方案。

**创建方式**：直接对 WorkBuddy 说：

> 创建一个每周定时任务：每周日晚上 9 点，对我的项目执行 WikiSkill 复盘

**任务 prompt 模板**（自包含，可直接复制）：

```
执行 WikiSkill 复盘流程（Google WikiSkill 框架的离线维护阶段）：

1. 读取当前项目 .wiki/raw/ 下最近 7 天的执行轨迹
2. 识别模式：
   - 失败模式（FM-xxx）：同类错误出现 ≥2 次
   - 成功策略（SS-xxx）：有效技巧在多个任务中验证
3. 追加到 .wiki/knowledge/patterns.md（只增不减，绝不覆盖已有内容）
4. 在 .wiki/knowledge/evolution_log.md 追加本次维护记录
5. 若识别出值得固化的模式，提出一个原子化技能改进，写入 .wiki/skills/
6. 在 .wiki/knowledge/impact_tracker.md 记录提案，状态标记为"待验证"

约束：
- Wiki 层只增不减，即使某条结论后来被推翻也保留原文
- 每次只提一个技能改进（原子化，便于归因）
- 若 .wiki/ 不存在则跳过并说明，不要自动创建
- 若近期无新轨迹，输出"无需维护"即可，不要凑内容
```

**建议频率**：每周一次（高频开发可改为每 2-3 天）。

---

## 方案二：Claude Code Hook（自动记录轨迹）

Claude Code 支持 hooks，可在会话结束时自动提醒记录轨迹。

### 安装

用统一安装器（全平台同一条命令，无需按 shell 区分）：

```bash
python <skill目录>/scripts/install.py --platform claude --target <项目目录>            # 项目级，推荐
python <skill目录>/scripts/install.py --platform claude --user                          # 用户级
python <skill目录>/scripts/install.py --platform claude --target <项目目录> --no-hook   # 只生成文件
python <skill目录>/scripts/install.py --platform claude --target <项目目录> --uninstall # 卸载
python <skill目录>/scripts/install.py --platform claude --user --uninstall
```

> **为什么不用 `~/.workbuddy/skills/wikiskill/...`**
> `.workbuddy/` 是 WorkBuddy 的私有目录，纯 Claude Code 用户机器上并不存在。
> 旧版安装器把 hook 指向那里，结果是**静默失效**——不报错、不提醒。
> 统一安装器改为：项目级用项目内相对路径，用户级把运行时放到
> **Claude Code 自己的目录** `~/.claude/scripts/wikiskill/`，不依赖任何第三方工具。

安装器会**合并**而非覆盖已有配置：已有的 `permissions`、`PostToolUse`、其他 `Stop` hook 全部保留，重复安装自动跳过，卸载只移除 wiki hook 且**绝不删除 `.wiki/` 数据**。

**平台自适应**：安装器检测 `os.name` 选择提醒脚本，并探测 `python` / `python3` / `py -3`：

| 场景 | 生成的命令 | 说明 |
|------|-----------|------|
| 项目级 · Windows | `python ".wiki/scripts/wiki_remind.py"` | 相对路径，项目可移动/可 clone |
| 项目级 · Unix | `bash ".wiki/scripts/wiki_remind.sh"` | 同上 |
| 用户级 · Windows | `python "C:\Users\x\.claude\scripts\wikiskill\wiki_remind.py"` | 绝对路径，服务所有项目 |
| 用户级 · Unix | `bash "$HOME/.claude/scripts/wikiskill/wiki_remind.sh"` | 用 `$HOME`，配置可迁移 |

或手动：按平台选一个模板，把其中的 `hooks` 字段合并进 `.claude/settings.json`。
两个模板都用**项目内相对路径**，无需替换用户名：

| 平台 | 模板文件 |
|------|---------|
| macOS / Linux | `assets/hooks/claude-code-settings.json` |
| Windows | `assets/hooks/claude-code-settings.windows.json` |

> 相对路径要求 `.wiki/scripts/` 已存在（先跑 `install.py` 或手动复制）。
> 用户级配置若要用绝对路径，需把命令里的脚本路径改为
> `~/.claude/scripts/wikiskill/wiki_remind.*`（用 `install.py --user` 会自动装好）。

### 配置内容

项目级安装生成（相对路径，推荐）：
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \".wiki/scripts/wiki_remind.py\""
          }
        ]
      }
    ]
  }
}
```

Windows 用户级安装生成（注意是 `.py` 且为绝对路径）：
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:\\\\Users\\\\<你>\\\\.claude\\\\scripts\\\\wikiskill\\\\wiki_remind.py\""
          }
        ]
      }
    ]
  }
}
```

**为什么 Windows 用绝对路径而非 `%USERPROFILE%`**：环境变量语法在不同 shell 下不通用——
cmd 用 `%USERPROFILE%`，PowerShell 用 `$env:USERPROFILE`，sh 用 `$HOME`。Claude Code
在 Windows 上走 cmd.exe/PowerShell，写死哪种语法都可能失效，故改用绝对路径。
代价是配置不可跨机器复制，换机器重跑一次安装器即可。

**作用**：每次 Agent 完成响应时，若项目存在 `.wiki/`，输出一条提醒，让 Agent 自行判断是否值得记录。

**注意**：hook 执行的是 shell 命令，不能替 Agent 写内容——它只是把"该记录了"这个信号注入上下文。真正的判断仍由 Agent 做。

### 作用域

| 位置 | 作用范围 |
|------|---------|
| `~/.claude/settings.json` | 所有项目（推荐，一次配置永久生效） |
| `<项目>/.claude/settings.json` | 仅当前项目 |

### 故障排查

**hook 装了但没看到提醒？** 按顺序排查：

1. **项目没有 `.wiki/` 目录** — 提醒脚本只在 `.wiki/` 存在时输出，这是设计行为（避免干扰无关项目）。先初始化：

   ```bash
   # 项目已安装过运行时（推荐，所有 shell 通用）
   python .wiki/scripts/wiki_init.py
   ```
   ```powershell
   # Windows PowerShell（未安装运行时时）
   python "<skill目录>\scripts\wiki_init.py"
   ```
   ```bash
   # Linux / macOS / Git Bash
   bash "<skill目录>/scripts/wiki_init.sh"
   ```

2. **没重启会话** — Claude Code 在会话启动时读取配置，装完需重开会话才生效。

3. **hook 指向的路径不存在** — 这是最常见也最隐蔽的原因。检查
   `.claude/settings.json` 里的命令：若指向 `~/.workbuddy/skills/wikiskill/...`
   而你没装 WorkBuddy，该路径不存在，hook **静默失败**（不阻断会话、无任何报错）。
   用统一安装器重装：

   ```bash
   python <skill目录>/scripts/install.py --platform claude --target <项目目录> --uninstall
   python <skill目录>/scripts/install.py --platform claude --target <项目目录>
   ```

4. **Windows 上用了 `.sh`** — 若配置里是 `bash ... wiki_remind.sh`，在 Windows 会失败
   且无任何报错。安装器已按平台自动选择（Windows 用 `.py`），重装即可。

5. **机器上没有 `python` 命令** — 确认 `python --version` 有输出。安装器会自动探测
   `python` / `python3` / `py -3`；老配置若写死了 `python`，需手动编辑 `settings.json`。

6. **手动测试方式不对** — 在项目根目录直接运行即可，脚本会自行定位项目：

   ```bash
   python .wiki/scripts/wiki_remind.py
   ```

   若用用户级安装的全局脚本，才需要指定项目目录：

   ```bash
   # Unix
   CLAUDE_PROJECT_DIR=/path/to/project bash ~/.claude/scripts/wikiskill/wiki_remind.sh

   # Windows (PowerShell)
   $env:CLAUDE_PROJECT_DIR="C:\path\to\project"; python "$env:USERPROFILE\.claude\scripts\wikiskill\wiki_remind.py"
   ```

   在真实 Claude Code 下该变量由平台自动注入，无需手动设置。

   > 脚本定位项目用三级 fallback：`CLAUDE_PROJECT_DIR` → 当前工作目录 → **脚本自身位置**。
   > 第三级让它在 cron、沙箱、任何异常 cwd 下都能工作。

---

## 方案三：Codex

Codex 目前**没有 hooks 机制**。可选方案：

1. **AGENTS.md 常驻指令**（已实现）：靠全量加载提醒 Agent，需主动提触发词
2. **Shell wrapper**：包一层启动脚本，退出时执行提醒（较 hack，不推荐）
3. **Git hook**：见方案四

---

## 方案四：Git Hook（跨平台通用）

最通用的方案，任何工具链都能用。在 `.git/hooks/post-commit` 加入：

```bash
#!/bin/bash
# 提交后提醒记录轨迹
if [ -d ".wiki" ]; then
  echo "[WikiSkill] 本次提交若有值得记录的踩坑或技巧，请追加到 .wiki/raw/$(date +%Y-%m-%d).md"
fi
```

记得 `chmod +x .git/hooks/post-commit`。

---

## 什么不该自动化

**门控验证（L4）不建议自动化**。判断"这个技能改进到底有没有用"需要人看实际效果。强行自动化会导致：
- 无效技能被自动采纳，污染技能库
- 论文里的自动门控依赖 held-out 验证集，个人开发没有这个条件

**实践建议**：让 automation 跑 Step 2/3（复盘和提案），把提案标为"待验证"，你在下次遇到类似任务时自然检验，有效就留下，无效就回滚。这个人工环节反而是质量保障。

---

## 组合建议

| 场景 | 推荐组合 |
|------|---------|
| 主用 WorkBuddy | 定时 automation（周复盘）+ 手动提"记录轨迹" |
| 主用 Claude Code | Stop hook（自动提醒）+ 定时手动复盘 |
| 多工具混用 | Git hook（通用提醒）+ WorkBuddy automation（集中复盘） |
| 想立刻见效 | 不做自动化，直接手动把已知坑写进 patterns.md |
