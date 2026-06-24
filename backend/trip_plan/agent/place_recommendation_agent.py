"""地方推荐 Agent。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from agent import BaseAgent

from trip_plan.agent.models import (
    PlaceRecommendationAgentResult,
    PlaceRecommendationResult,
)

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts" / "place_recommendation"


@lru_cache(maxsize=2)
def _load_prompt(filename: str) -> str:
    return (PROMPT_DIR / filename).read_text(encoding="utf-8").strip()


class PlaceRecommendationAgent(BaseAgent):
    """根据用户一句话推荐文化旅行地方。"""

    @property
    def role_prompt(self) -> str:
        """旅游博主角色设定。"""

        return _load_prompt("role.md")

    def run(self, user_content: str, **kwargs) -> PlaceRecommendationAgentResult:
        """运行地方推荐流程。"""

        task_prompt = _load_prompt("task.md")
        result = self.invoke_structured(
            user_content,
            PlaceRecommendationResult,
            task_prompt=task_prompt,
        )
        return PlaceRecommendationAgentResult(
            result=result,
            model=self.llm_config.model,
            provider=self.llm_config.provider,
        )
