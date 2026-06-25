"""综合文化解读 Agent。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from agent import BaseAgent

from trip_plan.agent.models import CulturalInterpretationsAgentResult

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts" / "cultural_interpretations"


@lru_cache(maxsize=2)
def _load_prompt(filename: str) -> str:
    return (PROMPT_DIR / filename).read_text(encoding="utf-8").strip()


class CulturalInterpretationAgent(BaseAgent):
    """根据目的地和景点生成历史、风俗、地理综合文化解读。"""

    @property
    def role_prompt(self) -> str:
        """文化解读专家角色设定。"""

        return _load_prompt("role.md")

    def run(self, user_content: str, **kwargs) -> CulturalInterpretationsAgentResult:
        """运行综合文化解读流程。"""

        task_prompt = _load_prompt("task.md")
        result = self.invoke_structured(
            user_content,
            CulturalInterpretationsAgentResult,
            task_prompt=task_prompt,
        )
        return result
