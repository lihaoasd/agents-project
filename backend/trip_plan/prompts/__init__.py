"""行程规划 Prompt 模板包。

目录结构::

    prompts/
    ├── config/
    │   ├── zh/          # 中文 prompt
    │   │   └── route_plan_system.txt
    │   └── en/          # 英文 prompt
    │       └── route_plan_system.txt
    ├── cultural_interpretations/
    │   ├── role.md
    │   └── task.md
    ├── place_recommendation/
    │   ├── role.md
    │   └── task.md
    └── scenic_spots/
        ├── role.md
        └── task.md
"""

from __future__ import annotations

from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent


def load_prompt(name: str, lang: str = "zh") -> str:
    """加载 prompt 模板文件。

    优先从 config/{lang}/ 目录加载，不存在则回退到根目录。

    Args:
        name: 文件名，例如 "route_plan_system.txt"。
        lang: 语言代码，默认 "zh"。

    Returns:
        模板内容字符串。

    Raises:
        FileNotFoundError: 文件不存在时抛出。
    """
    # 优先从 config/{lang}/ 查找
    lang_path = _PROMPTS_DIR / "config" / lang / name
    if lang_path.is_file():
        return lang_path.read_text(encoding="utf-8").strip()

    # 回退到根目录
    root_path = _PROMPTS_DIR / name
    if root_path.is_file():
        return root_path.read_text(encoding="utf-8").strip()

    raise FileNotFoundError(
        f"Prompt 文件不存在: {lang_path} 或 {root_path}"
    )


__all__ = ["load_prompt"]