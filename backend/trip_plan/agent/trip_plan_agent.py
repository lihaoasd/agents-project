"""行程规划专用 Agent。

注意：此 Agent 使用旧版 TravelPlan / TravelDestination / ScenicSpot 模型，
与 PlaceRecommendationAgent / ScenicSpotAgent 分属不同功能模块，暂不调整。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from agent import BaseAgent
from config import LLMConfig
from trip_plan.agent.models import TravelPlan, TravelPlanResult
from trip_plan.config import TripPlanConfig

PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompt" / "trip"


def _read_prompt(name: str) -> str:
    prompt_path = PROMPT_DIR / f"{name}.md"
    try:
        return prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise RuntimeError(f"缺少提示词文件：{prompt_path}") from exc


@lru_cache(maxsize=1)
def _load_role_prompt() -> str:
    return _read_prompt("role")


@lru_cache(maxsize=1)
def _load_task_prompt() -> str:
    return _read_prompt("task")


class TripPlanAgent(BaseAgent):
    """文化旅行行程规划 Agent。

    注意：此 Agent 使用旧版 TravelPlan / TravelDestination 模型，
    与 PlaceRecommendationAgent / ScenicSpotAgent 分属不同功能模块，暂不调整。
    """

    @property
    def role_prompt(self) -> str:
        return _load_role_prompt()

    def __init__(
        self,
        llm_config: LLMConfig | None = None,
        trip_plan_config: TripPlanConfig | None = None,
    ) -> None:
        super().__init__(llm_config=llm_config)
        self.trip_plan_config = trip_plan_config or TripPlanConfig()

    def run(self, user_content: str, **kwargs: Any) -> TravelPlanResult:
        """根据用户旅游要求生成行程规划。"""

        days = kwargs.get("days") or self.trip_plan_config.default_days
        budget = kwargs.get("budget") or self.trip_plan_config.default_budget
        interests = kwargs.get("interests") or []
        language = kwargs.get("language") or "zh-CN"

        plan = self.generate_travel_plan(
            requirement=user_content,
            days=days,
            budget=budget,
            interests=interests,
            language=language,
        )
        return TravelPlanResult(
            plan=plan,
            model=self.llm_config.model,
            provider=self.llm_config.provider,
        )

    def generate_travel_plan(
        self,
        requirement: str,
        days: int,
        budget: str,
        interests: list[str],
        language: str,
    ) -> TravelPlan:
        """调用 LangChain 结构化输出生成旅行计划。"""

        user_prompt = self._build_user_prompt(requirement, days, budget, interests, language)
        task_prompt = self._build_task_prompt()
        return self.invoke_structured(user_prompt, TravelPlan, task_prompt)

    def _build_task_prompt(self) -> str:
        return _load_task_prompt()

    def _build_user_prompt(
        self,
        requirement: str,
        days: int,
        budget: str,
        interests: list[str],
        language: str,
    ) -> str:
        interests_text = "、".join(interests) if interests else "历史、文化、美食"
        return f"""用户旅游要求：{requirement}
计划天数：{days}
预算水平：{budget}
兴趣偏好：{interests_text}
输出语言：{language}

请生成完整行程规划，字段必须覆盖：
- 推荐省份、地市和理由
- 3 到 {self.trip_plan_config.max_spot_recommendations} 个景点，每个景点包含 id、地址、推荐理由和文化标签
- 景点之间的路线分段
- 书籍、短视频、文章等内容推荐
- 免责声明：{self.trip_plan_config.disclaimer}"""
