#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能进化（知行环）· Skill Evolution — 统一安装器（跨平台 / 跨 AI 工具）

设计原则：项目自包含。

技能进化（知行环）不依赖任何 AI 工具的私有目录。安装时把运行时脚本与参考文档
复制进项目内的 .wiki/，生成的指令文件与 hook 全部使用项目内路径。
因此项目可以整体提交 Git，换机器 clone 后无需重新安装即可工作。

与旧版 install_claude_hook.py 的区别：
    旧版把 hook 指向 ~/.workbuddy/skills/<skill名>/，那是 WorkBuddy 的私有
    目录。纯 Claude Code / Codex 用户机器上该目录不存在，hook 会静默失效。
    本安装器把运行时复制到目标平台自己的位置，或项目内，并校验路径真实存在。

用法:
    python install.py --platform claude                 # 项目级自包含（默认，推荐）
    python install.py --platform codex                  # 同上，生成 AGENTS.md
    python install.py --platform claude --user          # 用户级，脚本装到 ~/.claude/scripts/skill-evolution/
    python install.py --platform claude --target DIR    # 指定项目目录
    python install.py --platform claude --no-hook       # 只生成文件，不装 hook
    python install.py --platform claude --uninstall     # 移除 hook（绝不删除 .wiki/ 数据）

平台与产物:
    claude    -> CLAUDE.md + .claude/settings.json (Stop hook)
    codex     -> AGENTS.md（Codex 无 hook 机制，不生成配置文件）
    workbuddy -> 只准备 .wiki/，指令由 WorkBuddy 的 SKILL.md 提供
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# Windows 下 stdout 默认是 GBK(cp936)，输出中文会抛 UnicodeEncodeError。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# 识别本框架 hook 的特征串。
# 必须包含 "wiki_remind"：项目级安装使用项目内相对路径
# （python ".wiki/scripts/wiki_remind.py"），命令里不含 skill 名，
# 只靠 skill 名匹配会导致去重与卸载双双失效 —— 故以脚本名为主判据。
# 同时保留旧名 "wikiskill"：本 skill 由 wikiskill + rsi-knowledge +
# rsi-self-improvement-designer 三合一而来，保留旧名才能识别并卸载
# 整合之前安装的 hook，避免重复注入。
HOOK_MARKERS = ("skill-evolution", "wikiskill", "wiki_remind")

# 运行时文件（复制到目标位置，保证自包含）
RUNTIME_FILES = ["wiki_init.py", "wiki_init.sh", "wiki_init.ps1",
                 "wiki_remind.py", "wiki_remind.sh"]

# 参考文档（复制进项目 .wiki/references/）
# 前四个是经验沉淀（.wiki 运行时）所必需；后两个是 RSI 判据与自改进设计手册，
# 一并复制以便项目内的联合自改进闭环自包含、不依赖 skill 安装目录。
REFERENCE_FILES = ["workflow.md", "platforms.md", "automation.md", "templates.md",
                   "rsi-framework.md", "design-playbook.md"]

PLATFORM_SPECS = {
    "claude": {
        "instruction": "CLAUDE.md",
        "template": "CLAUDE.template.md",
        "user_dir": ".claude",
        "supports_hook": True,
    },
    "codex": {
        "instruction": "AGENTS.md",
        "template": "AGENTS.template.md",
        "user_dir": ".codex",
        "supports_hook": False,
    },
    "workbuddy": {
        "instruction": None,
        "template": None,
        "user_dir": ".workbuddy",
        "supports_hook": False,
    },
}


def source_dirs() -> tuple:
    """定位本 skill 的 scripts/ 与 references/ 目录（解压到任意位置均可）。"""
    here = Path(__file__).resolve().parent
    skill_root = here.parent
    return skill_root / "scripts", skill_root / "references"


def detect_python() -> str:
    """
    检测可用的 Python 启动命令。

    Windows 上可能只有 py -3 而没有 python；macOS/Linux 上可能只有 python3。
    写死 python 会让 hook 在这类机器上静默失效。
    """
    for cmd in ("python", "python3", "py -3"):
        exe = cmd.split()[0]
        if shutil.which(exe):
            return cmd
    return "python"  # 检测不到则退回最常见写法


def create_wiki_skeleton(target: Path) -> bool:
    """创建 .wiki/ 骨架。已存在则原样保留（绝不覆盖用户数据）。"""
    created = not (target / ".wiki").exists()
    for sub in ("raw", "knowledge", "skills", "meta", "scripts", "references"):
        (target / ".wiki" / sub).mkdir(parents=True, exist_ok=True)

    if created:
        files = {
            "knowledge/patterns.md": "# 模式库\n\n## 失败模式\n\n（暂无记录）\n\n## 成功策略\n\n（暂无记录）\n",
            "knowledge/evolution_log.md": "# 技能演化日志\n\n（暂无记录）\n",
            "knowledge/impact_tracker.md": "# 提案影响追踪\n\n（暂无记录）\n",
            "meta/config.md": "# Wiki 配置\n\n- **创建日期**：%s\n- **维护周期**：每 3-5 个任务后执行一次 Wiki Maintainer\n"
                             % __import__("datetime").date.today().isoformat(),
        }
        for rel, content in files.items():
            p = target / ".wiki" / rel
            if not p.exists():
                p.write_text(content, encoding="utf-8")
    return created


def copy_runtime(target: Path, scripts_src: Path, refs_src: Path) -> list:
    """复制运行时脚本与参考文档进项目，返回复制的文件清单。"""
    copied = []
    for name in RUNTIME_FILES:
        src = scripts_src / name
        if src.exists():
            shutil.copy2(src, target / ".wiki" / "scripts" / name)
            copied.append("scripts/" + name)
    for name in REFERENCE_FILES:
        src = refs_src / name
        if src.exists():
            shutil.copy2(src, target / ".wiki" / "references" / name)
            copied.append("references/" + name)
    return copied


SELF_CONTAINED_INIT = """如果 `.wiki/` 不存在，任选一种方式创建：

**方式 A — 用项目内脚本**（已随项目存在，无需任何外部依赖）：

```bash
# Windows PowerShell / macOS / Linux / Git Bash
python .wiki/scripts/wiki_init.py
```
```cmd
:: Windows CMD
python .wiki\\scripts\\wiki_init.py
```
```powershell
# Windows PowerShell（无 Python 时的备选）
powershell -ExecutionPolicy Bypass -File .wiki\\scripts\\wiki_init.ps1
```

> 本项目已自包含「技能进化（知行环）」运行时，`.wiki/scripts/` 下的脚本可直接执行。
> 不依赖 WorkBuddy / Claude Code / Codex 的任何全局目录。

**方式 B — 手动创建**（脚本不可用时直接执行）：
```bash
mkdir -p .wiki/raw .wiki/knowledge .wiki/skills .wiki/meta
printf '# 模式库\\n\\n## 失败模式\\n\\n（暂无记录）\\n\\n## 成功策略\\n\\n（暂无记录）\\n' > .wiki/knowledge/patterns.md
printf '# 技能演化日志\\n\\n（暂无记录）\\n' > .wiki/knowledge/evolution_log.md
printf '# 提案影响追踪\\n\\n（暂无记录）\\n' > .wiki/knowledge/impact_tracker.md
```"""

SELF_CONTAINED_REF = """- 闭环全图与四问评分卡（权威源）：`.wiki/references/workflow.md`
- ① 选域 / ⑦ 升阶（HCI、L1–L5）：`.wiki/references/rsi-framework.md`
- 全链自改进设计五步：`.wiki/references/design-playbook.md`
- 平台适配：`.wiki/references/platforms.md`
- 自动化方案：`.wiki/references/automation.md`
- 模板集合：`.wiki/references/templates.md`
- 原论文：WikiSkill, arXiv:2608.27454（经验怎么存、怎么迭代）；RSI 路线图, arXiv:2609.11873（改进算不算数、能自动到哪）"""


def replace_section(text: str, start_marker: str, end_marker: str, new_body: str) -> str:
    """按 HTML 注释标记替换片段；找不到标记则原样返回。"""
    s = text.find(start_marker)
    e = text.find(end_marker)
    if s == -1 or e == -1 or e < s:
        return text
    # 保留起始标记所在行之前的内容，替换两标记之间的正文
    head = text[:s + len(start_marker)]
    tail = text[e:]
    return head + "\n" + new_body + "\n" + tail


def render_instruction(template_path: Path) -> str:
    """把模板渲染为自包含版本（去掉对 ~/.workbuddy 的依赖）。"""
    text = template_path.read_text(encoding="utf-8")
    text = replace_section(text, "<!-- INIT_SECTION_START -->",
                           "<!-- INIT_SECTION_END -->", SELF_CONTAINED_INIT)
    text = replace_section(text, "<!-- REF_SECTION_START -->",
                           "<!-- REF_SECTION_END -->", SELF_CONTAINED_REF)
    return text


def remind_command(project_level: bool, project_root: Path, user_script: Path = None) -> str:
    """
    构造 hook 命令。

    项目级用相对路径 —— 项目移动或 clone 到别处仍有效。
    用户级用绝对路径 —— 用户级配置会应用到所有项目，相对路径会指向错误目录。
    Windows 用 wiki_remind.py（cmd/PowerShell 无 bash），Unix 用 .sh。
    """
    if project_level:
        rel = ".wiki/scripts/wiki_remind.py" if os.name == "nt" else ".wiki/scripts/wiki_remind.sh"
        return '%s "%s"' % (detect_python() if os.name == "nt" else "bash", rel)
    script = user_script
    if os.name == "nt":
        return '%s "%s"' % (detect_python(), script)
    return 'bash "%s"' % script


def is_skill_evolution_command(command: str) -> bool:
    """判断一条 hook 命令是否属于技能进化（知行环）。"""
    low = command.lower()
    return any(m in low for m in HOOK_MARKERS)


def collect_skill_hooks(settings: dict) -> list:
    """
    收集所有属于本框架的 hook 命令。

    返回 [(group_index, hook_index, command), ...]。
    之所以要拿到命令原文而不只是布尔值：整合前的用户级安装会把 hook 指向
    ~/.claude/scripts/wikiskill/wiki_remind.py，若只判断"存在同类 hook"
    就跳过，旧路径会被永久保留，运行时再也升不上去。
    """
    found = []
    for gi, group in enumerate(settings.get("hooks", {}).get("Stop", [])):
        if not isinstance(group, dict):
            continue
        for hi, h in enumerate(group.get("hooks", [])):
            if not isinstance(h, dict):
                continue
            cmd = h.get("command", "")
            if is_skill_evolution_command(cmd):
                found.append((gi, hi, cmd))
    return found


def strip_skill_hooks(settings: dict) -> None:
    """移除所有属于本框架的 hook 项，同组内的其他 hook 原样保留。"""
    stop = settings.get("hooks", {}).get("Stop", [])
    kept = []
    for group in stop:
        if not isinstance(group, dict):
            kept.append(group)
            continue
        inner = [h for h in group.get("hooks", [])
                 if not (isinstance(h, dict)
                         and is_skill_evolution_command(h.get("command", "")))]
        if inner:
            group["hooks"] = inner
            kept.append(group)

    if kept:
        settings["hooks"]["Stop"] = kept
    else:
        settings["hooks"].pop("Stop", None)
        if not settings["hooks"]:
            settings.pop("hooks", None)


def merge_hook(settings_path: Path, command: str) -> str:
    """
    合并而非覆盖：保留已有 permissions / 其他 hooks。

    已存在同类 hook 时不再无条件跳过。命令不一致（典型情形：整合前用户级
    安装留下的 wikiskill 路径）说明这是升级前的旧 hook，必须替换成新命令，
    否则 hook 会一直调用旧目录里的运行时快照。
    """
    settings = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return "错误：%s 不是合法 JSON，已中止以免损坏配置。" % settings_path

    existing = collect_skill_hooks(settings)
    if existing and all(cmd == command for _, _, cmd in existing):
        return "跳过：%s 中已存在相同命令的 hook。" % settings_path

    old = [cmd for _, _, cmd in existing]
    if old:
        strip_skill_hooks(settings)

    settings.setdefault("hooks", {}).setdefault("Stop", []).append(
        {"hooks": [{"type": "command", "command": command}]})
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if old:
        return ("已升级 hook（替换旧命令，其余配置保留）：%s\n  旧：%s\n  新：%s"
                % (settings_path, "；".join(old), command))
    return "已安装 hook：%s\n  命令：%s" % (settings_path, command)


def remove_hook(settings_path: Path) -> str:
    if not settings_path.exists():
        return "跳过：配置文件不存在 %s" % settings_path
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "错误：%s 不是合法 JSON，已中止。" % settings_path

    existing = collect_skill_hooks(settings)
    if not existing:
        return "跳过：未找到技能进化（知行环）的 hook %s" % settings_path

    # 复用 strip_skill_hooks，而非按组删除：一个 Stop 组里可能同时含有本框架的
    # hook 和用户自己的 hook（例如手工把两者放在一起）。按组删除会把用户自己的
    # hook 一起干掉，且与升级路径（merge_hook）的行为不一致。
    strip_skill_hooks(settings)
    settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ("已移除 %d 条技能进化（知行环）hook（同组其他 hook 与其余配置保持不变）：%s"
            % (len(existing), settings_path))


def install_user_level(platform: str, scripts_src: Path, want_hook: bool) -> int:
    """
    用户级安装：运行时复制到平台自己的目录，不依赖 WorkBuddy。

    claude -> ~/.claude/scripts/skill-evolution/
    codex  -> ~/.codex/scripts/skill-evolution/
    """
    spec = PLATFORM_SPECS[platform]
    dest = Path.home() / spec["user_dir"] / "scripts" / "skill-evolution"
    dest.mkdir(parents=True, exist_ok=True)

    missing = []
    for name in RUNTIME_FILES:
        src = scripts_src / name
        if src.exists():
            shutil.copy2(src, dest / name)
        else:
            missing.append(name)

    print("[用户级] 运行时已复制到：%s" % dest)
    if missing:
        print("        缺失源文件（可忽略）：%s" % ", ".join(missing))

    # 整合前的用户级安装会把运行时放在 <平台目录>/scripts/wikiskill/。
    # 新 hook 指向新目录，旧目录不再被引用，但不会自动删除 —— 明确提示，
    # 避免用户以为两个目录里哪份在生效。
    legacy = Path.home() / spec["user_dir"] / "scripts" / "wikiskill"
    if legacy.exists():
        print("        检测到整合前的旧运行时：%s" % legacy)
        print("        新 hook 不再引用它，确认提醒正常后即可删除该目录。")

    if not want_hook or not spec["supports_hook"]:
        if not spec["supports_hook"]:
            print("        平台 %s 无 hook 机制，跳过 hook 安装。" % platform)
        return 0

    settings_path = Path.home() / spec["user_dir"] / "settings.json"
    script = dest / ("wiki_remind.py" if os.name == "nt" else "wiki_remind.sh")

    # 用户级配置可能含 API token 等敏感信息，写入前明确告知
    if settings_path.exists():
        print("        注意：将修改已有配置 %s（其余内容保留）" % settings_path)
    print(merge_hook(settings_path, remind_command(False, None, script)))
    print("        生效条件：重启会话后，项目存在 .wiki/ 时输出记录提醒。")
    return 0


def install(args) -> int:
    spec = PLATFORM_SPECS[args.platform]
    scripts_src, refs_src = source_dirs()

    if not scripts_src.exists():
        print("[错误] 找不到 scripts/ 目录：%s" % scripts_src)
        print("       请确认 install.py 仍在 skill-evolution 包内的 scripts/ 下。")
        return 1

    if args.user:
        return install_user_level(args.platform, scripts_src, not args.no_hook)

    # ---- 项目级：自包含 ----
    target = Path(args.target).resolve() if args.target else Path.cwd()
    if not target.exists():
        print("[错误] 目标目录不存在：%s" % target)
        return 1

    print("=== 技能进化（知行环）安装（项目级 · 自包含）===")
    print("目标项目：%s" % target)
    print()

    fresh = create_wiki_skeleton(target)
    print("[1/4] .wiki/ 骨架：%s" % ("已创建" if fresh else "已存在，原样保留"))

    copied = copy_runtime(target, scripts_src, refs_src)
    print("[2/4] 运行时复制：%d 个文件 -> .wiki/scripts/ 与 .wiki/references/" % len(copied))

    if spec["instruction"]:
        tpl = refs_src / spec["template"]
        if tpl.exists():
            out = target / spec["instruction"]
            if out.exists():
                print("[3/4] %s 已存在，跳过以免覆盖你的修改（需更新请手动删除后重跑）"
                      % spec["instruction"])
            else:
                out.write_text(render_instruction(tpl), encoding="utf-8")
                print("[3/4] 已生成 %s（自包含，路径均指向项目内）" % spec["instruction"])
        else:
            print("[3/4] 跳过：模板不存在 %s" % tpl)
    else:
        print("[3/4] 跳过：%s 平台不需要额外指令文件（指令由该平台的 SKILL.md 提供）"
              % args.platform)

    if args.no_hook or not spec["supports_hook"]:
        reason = "已用 --no-hook 指定" if args.no_hook else "平台无 hook 机制"
        print("[4/4] 跳过 hook 安装（%s）" % reason)
    else:
        settings_path = target / spec["user_dir"] / "settings.json"
        print("[4/4] " + merge_hook(settings_path, remind_command(True, target)))

    print()
    print("完成。项目现已自包含，可整体提交 Git，换机器 clone 后无需重装。")
    print()
    print("下一步：")
    if spec["instruction"]:
        print("  1. 在编辑器里打开 %s，把项目名称/描述改成你自己的" % spec["instruction"])
    else:
        print("  1. 本平台不生成指令文件（指令由 %s 的 SKILL.md 提供），无需额外配置"
              % args.platform)
    print("  2. 别等自动流程 —— 直接把已知的坑手动写进 .wiki/knowledge/patterns.md")
    return 0


def uninstall(args) -> int:
    spec = PLATFORM_SPECS[args.platform]
    print("=== 技能进化（知行环）卸载 ===")

    if args.user:
        settings_path = Path.home() / spec["user_dir"] / "settings.json"
        print(remove_hook(settings_path))
        dest = Path.home() / spec["user_dir"] / "scripts" / "skill-evolution"
        if dest.exists():
            print("运行时目录仍保留：%s（如需彻底删除请手动移除）" % dest)
    else:
        target = Path(args.target).resolve() if args.target else Path.cwd()
        settings_path = target / spec["user_dir"] / "settings.json"
        print(remove_hook(settings_path))
        print("已保留 .wiki/ 与 %s —— 经验数据不自动删除。" % (spec["instruction"] or "指令文件"))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="技能进化（知行环）统一安装器（项目自包含，不依赖 WorkBuddy）")
    p.add_argument("--platform", choices=sorted(PLATFORM_SPECS), default="claude",
                   help="目标 AI 工具，默认 claude")
    p.add_argument("--target", help="项目目录，默认当前目录")
    p.add_argument("--user", action="store_true",
                   help="用户级安装（脚本装到 ~/.claude/scripts/skill-evolution/），默认项目级")
    p.add_argument("--no-hook", action="store_true", help="只生成文件，不安装 hook")
    p.add_argument("--uninstall", action="store_true", help="移除 hook（不删除 .wiki/ 数据）")

    args = p.parse_args()
    if args.user and args.target:
        print("[错误] --user 与 --target 不可同时使用（用户级不针对单个项目）。")
        return 1
    return uninstall(args) if args.uninstall else install(args)


if __name__ == "__main__":
    sys.exit(main())
