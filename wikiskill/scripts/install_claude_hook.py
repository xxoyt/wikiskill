#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WikiSkill — Claude Code Hook 安装器（已弃用，请改用 install.py）

[弃用说明]
本脚本把 hook 指向 ~/.workbuddy/skills/wikiskill/ —— 那是 WorkBuddy 的私有目录。
纯 Claude Code / Codex 用户机器上该目录不存在，hook 会静默失效（不报错、不提醒）。

请改用统一安装器 install.py，它把运行时复制进项目或目标平台自己的目录：

    python install.py --platform claude            # 项目级自包含（推荐）
    python install.py --platform claude --user     # 用户级 -> ~/.claude/scripts/wikiskill/

保留本脚本仅为兼容旧文档引用。它现在会校验目标路径是否存在，
不存在时拒绝安装并给出指引，而不是写入一条死链。

用法:
    python install_claude_hook.py              # 安装到用户级 ~/.claude/settings.json
    python install_claude_hook.py --project    # 安装到项目级 .claude/settings.json
    python install_claude_hook.py --uninstall  # 移除 WikiSkill hook
"""

import json
import os
import sys
from pathlib import Path

HOOK_MARKER = "wikiskill"


def get_remind_command(skill_home: Path) -> str:
    """
    构造与平台匹配的 hook 命令。

    Windows 与 Unix 必须分开处理，原因有两条：
    1. Claude Code 在 Windows 上通过 cmd.exe / PowerShell 执行 hook，
       系统默认没有 bash，调用 .sh 会静默失败。必须用 wiki_remind.py。
    2. 环境变量语法不通用 —— cmd 用 %USERPROFILE%，PowerShell 用
       $env:USERPROFILE，sh 用 $HOME。Windows 下改用绝对路径最可靠，
       代价是配置不可跨机器复制（可重跑本安装器重新生成）。
    Unix 下仍用 $HOME，保证配置可迁移。
    """
    if os.name == "nt":
        script = skill_home / "scripts" / "wiki_remind.py"
        return f'python "{script}"'
    return 'bash "$HOME/.workbuddy/skills/wikiskill/scripts/wiki_remind.sh"'


def get_skill_home() -> Path:
    return Path.home() / ".workbuddy" / "skills" / "wikiskill"


def make_hook_entry(skill_home: Path) -> dict:
    """构造单个 Stop hook 条目。"""
    return {
        "hooks": [
            {
                "type": "command",
                "command": get_remind_command(skill_home),
            }
        ]
    }


def hook_already_installed(settings: dict) -> bool:
    """检查是否已安装，避免重复添加。"""
    stop_hooks = settings.get("hooks", {}).get("Stop", [])
    for group in stop_hooks:
        if not isinstance(group, dict):
            continue
        for h in group.get("hooks", []):
            if HOOK_MARKER in h.get("command", "").lower():
                return True
    return False


def target_path(project_level: bool) -> Path:
    if project_level:
        return Path.cwd() / ".claude" / "settings.json"
    return Path.home() / ".claude" / "settings.json"


def load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"[错误] {path} 不是合法 JSON，已中止以免损坏配置。")
        print("       请手动修复该文件或删除后重试。")
        sys.exit(1)


def install(project_level: bool) -> int:
    path = target_path(project_level)
    settings = load_settings(path)

    if hook_already_installed(settings):
        print(f"[跳过] WikiSkill hook 已存在于 {path}")
        return 0

    skill_home = get_skill_home()
    script_name = "wiki_remind.py" if os.name == "nt" else "wiki_remind.sh"
    script = skill_home / "scripts" / script_name

    # 关键校验：路径不存在时拒绝安装。
    # 旧版本会直接写入一条指向不存在文件的命令，导致 hook 静默失效。
    if not script.exists():
        print(f"[中止] 找不到提醒脚本：{script}")
        print()
        print("       本安装器依赖 ~/.workbuddy/skills/wikiskill/，那是 WorkBuddy 的")
        print("       私有目录。若你未安装 WorkBuddy，该路径自然不存在。")
        print()
        print("       请改用不依赖 WorkBuddy 的统一安装器：")
        print("         python scripts/install.py --platform claude            # 项目级自包含")
        print("         python scripts/install.py --platform claude --user     # 用户级")
        return 1

    settings.setdefault("hooks", {}).setdefault("Stop", []).append(make_hook_entry(skill_home))
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")

    scope = "项目级" if project_level else "用户级"
    print(f"[完成] 已安装 WikiSkill Stop hook（{scope}）")
    print(f"       配置文件: {path}")
    print(f"       提醒脚本: {skill_home / 'scripts' / script_name}")
    if os.name == "nt":
        print("       平台: Windows — 使用 Python 版提醒脚本")
        print("       （cmd.exe/PowerShell 无 bash，.sh 版本会静默失效）")
    print()
    print("生效条件：重启 Claude Code 会话后，每次响应结束时若项目存在 .wiki/ 会输出记录提醒。")
    return 0


def uninstall(project_level: bool) -> int:
    path = target_path(project_level)
    if not path.exists():
        print(f"[跳过] 配置文件不存在: {path}")
        return 0

    settings = load_settings(path)
    stop_hooks = settings.get("hooks", {}).get("Stop", [])

    kept = [
        g for g in stop_hooks
        if not any(HOOK_MARKER in h.get("command", "").lower()
                   for h in (g.get("hooks", []) if isinstance(g, dict) else []))
    ]

    if len(kept) == len(stop_hooks):
        print(f"[跳过] 未找到 WikiSkill hook: {path}")
        return 0

    settings["hooks"]["Stop"] = kept
    # 若 Stop 数组已空，清理空的 hooks 结构
    if not kept:
        settings["hooks"].pop("Stop", None)
        if not settings["hooks"]:
            settings.pop("hooks", None)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"[完成] 已移除 WikiSkill hook，其余 hooks 保持不变: {path}")
    return 0


def main() -> int:
    args = set(sys.argv[1:])
    project_level = "--project" in args
    do_uninstall = "--uninstall" in args

    if do_uninstall:
        return uninstall(project_level)
    return install(project_level)


if __name__ == "__main__":
    sys.exit(main())
