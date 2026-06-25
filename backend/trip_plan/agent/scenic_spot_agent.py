"""景点推荐 Agent。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from agent import BaseAgent

from trip_plan.agent.models import ScenicSpotsAgentResult, ScenicSpotsResult

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts" / "scenic_spots"


@lru_cache(maxsize=2)
def _load_prompt(filename: str) -> str:
    return (PROMPT_DIR / filename).read_text(encoding="utf-8").strip()


class ScenicSpotAgent(BaseAgent):
    """根据用户需求和选定目的地推荐文化旅行景点。"""

    @property
    def role_prompt(self) -> str:
        """景点专家角色设定。"""

        return _load_prompt("role.md")

    def run(self, user_content: str, **kwargs) -> ScenicSpotsAgentResult:
        """运行景点推荐流程。"""

        task_prompt = _load_prompt("task.md")
        result = self.invoke_structured(
            user_content,
            ScenicSpotsResult,
            task_prompt=task_prompt,
        )
        return ScenicSpotsAgentResult(
            result=result,
            model=self.llm_config.model,
            provider=self.llm_config.provider,
        )