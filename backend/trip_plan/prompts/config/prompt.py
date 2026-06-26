"""Prompt 配置模块。

管理所有 Agent 的 prompt 模板文件路径和加载逻辑。
目录结构::

    config/
    ├── prompt.py          # 本文件
    ├── zh/                # 中文 prompt
    │   └── route_plan_system.txt
    └── en/                # 英文 prompt
        └── route_plan_system.txt
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from trip_plan.prompts import load_prompt


@dataclass(frozen=True)
class PromptConfig:
    """Prompt 模板配置。"""

    # 路线规划系统提示词
    ROUTE_PLAN_SYSTEM: ClassVar[str] = "route_plan_system.txt"

    @staticmethod
    def load(name: str, lang: str = "zh") -> str:
        """加载 prompt 模板。

        Args:
            name: 文件名，使用 PromptConfig 常量。
            lang: 语言代码，默认 "zh"。

        Returns:
            模板内容字符串。
        """
        return load_prompt(name, lang=lang)