"""辩论 Prompt 管理 — 角色 prompt 加载。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PROMPTS_DIR = Path(__file__).resolve().parent


def _resolve_path(slug: str) -> Path:
    """将 'roles/debater/confucius' 解析为 .md 文件路径。"""
    # 支持带 .md 后缀的调用，也支持不带后缀的
    file_path = _PROMPTS_DIR / f"{slug}.md" if not slug.endswith(".md") else _PROMPTS_DIR / slug
    if file_path.exists():
        return file_path
    raise FileNotFoundError(f"Prompt 文件不存在: {file_path}")


def load_prompt(slug: str) -> str:
    """加载指定 slug 的角色 prompt 内容。

    Args:
        slug: Prompt 路径 slug，例如 "roles/debater/confucius" 或 "roles/debater/confucius.md"

    Returns:
        完整的 markdown 文本内容

    Raises:
        FileNotFoundError: prompt 文件不存在
    """
    path = _resolve_path(slug)
    return path.read_text(encoding="utf-8")


def load_index(slug: str) -> list[dict[str, Any]]:
    """加载指定目录的角色 index.json。

    Args:
        slug: 索引目录，例如 "roles/debater" 或 "roles/judge"

    Returns:
        角色列表，每个元素包含 id、name、description 等字段
    """
    index_path = _PROMPTS_DIR / slug / "index.json"
    if not index_path.exists():
        raise FileNotFoundError(f"Index 文件不存在: {index_path}")
    return json.loads(index_path.read_text(encoding="utf-8"))


__all__ = ["load_prompt", "load_index"]