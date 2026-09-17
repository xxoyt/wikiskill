#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Evolution — 初始化 .wiki 目录结构（跨平台版）

用法:
    python wiki_init.py [项目根目录]

支持: Windows (CMD/PowerShell) / macOS / Linux —— 只要装了 Python 3.6+
这是跨平台首选入口；bash 用户也可用 scripts/wiki_init.sh。
"""

import os
import sys
from datetime import date

TEMPLATES = {
    "knowledge/patterns.md": """# Wiki Knowledge — 模式库

> 本文件由 Wiki Maintainer 维护，记录从执行轨迹中提炼的失败模式与成功策略。
> 只增不减，永不重置。

## 失败模式

（暂无记录）

## 成功策略

（暂无记录）
""",
    "knowledge/evolution_log.md": """# 技能演化日志

> 记录每次 Wiki 维护和技能变更的历史。

（暂无记录）
""",
    "knowledge/impact_tracker.md": """# 提案影响追踪

> 记录每个技能提案的验证结果。

（暂无记录）
""",
    "meta/config.md": """# Wiki 配置

- **创建日期**：{date}
- **维护周期**：每 3-5 个任务后执行一次 Wiki Maintainer
- **进化周期**：每 5-10 个任务后执行一次 Skill Proposer
- **轨迹格式**：精简模式（每条 ≤10 行）
""",
}

# 需要创建的空目录（raw 存轨迹，skills 存可回滚技能）
EMPTY_DIRS = ["raw", "skills"]


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    wiki = os.path.join(root, ".wiki")

    if os.path.isdir(wiki):
        print("[Skill Evolution] .wiki 目录已存在: %s" % wiki)
        return 0

    for d in EMPTY_DIRS:
        os.makedirs(os.path.join(wiki, d), exist_ok=True)

    # encoding 必须显式指定 utf-8：
    # Windows 默认使用 GBK(cp936)，不指定会导致中文写入乱码或 UnicodeEncodeError
    for rel, content in TEMPLATES.items():
        path = os.path.join(wiki, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content.format(date=date.today().isoformat()))

    print("[Skill Evolution] 初始化完成: %s" % wiki)
    print("   raw/        - 执行轨迹（按日期追加）")
    print("   knowledge/  - 持久化知识（patterns + evolution_log + impact_tracker）")
    print("   skills/     - 可复用技能（可回滚）")
    print("   meta/       - Wiki 配置")
    return 0


if __name__ == "__main__":
    sys.exit(main())
