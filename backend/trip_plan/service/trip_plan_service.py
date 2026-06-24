"""行程规划业务服务。"""

from __future__ import annotations

from dataclasses import dataclass

from agent import AgentError
from logging_config import get_logger

from trip_plan.agent.models import (
    PlaceRecommendation,
    PlaceRecommendationResult,
)
from trip_plan.agent.place_recommendation_agent import PlaceRecommendationAgent

FALLBACK_DESTINATIONS = [
    PlaceRecommendation(
        id="xian",
        province="陕西省",
        city="西安市",
        matchScore=96,
        tags=["唐代文化", "博物馆", "历史遗址", "美食"],
        reasons=[
            "适合围绕周秦汉唐文化展开研学旅行。",
            "博物馆和历史遗址密集，适合亲子或深度文化游。",
            "城市交通便利，可串联城墙、博物院和遗址公园。",
        ],
        intro="西安是十三朝古都，唐代文化、城墙格局、陵墓遗址和博物馆资源都非常丰富，适合作为历史文化旅行的核心目的地。",
    ),
    PlaceRecommendation(
        id="hangzhou",
        province="浙江省",
        city="杭州市",
        matchScore=88,
        tags=["宋韵文化", "西湖", "茶文化", "运河"],
        reasons=[
            "适合体验西湖景观、宋韵审美和江南城市生活。",
            "茶文化、运河文化和博物馆资源容易形成轻松的文化路线。",
            "适合预算中等、节奏舒缓的文化旅行。",
        ],
        intro="杭州以西湖、宋韵文化、茶文化和运河文化见长，适合把自然景观和城市人文结合起来。",
    ),
    PlaceRecommendation(
        id="beijing",
        province="北京市",
        city="北京市",
        matchScore=86,
        tags=["皇家文化", "故宫", "长城", "中轴线"],
        reasons=[
            "适合了解皇家建筑、宫廷文化和北京中轴线。",
            "故宫、天坛、长城等资源知名度高，适合首次文化旅行。",
            "博物馆和历史文化街区丰富，适合多日深度游览。",
        ],
        intro="北京拥有故宫、天坛、长城、胡同和中轴线等代表性文化资源，适合皇家文化和古都城市主题旅行。",
    ),
]


@dataclass
class PlaceRecommendationServiceResult:
    """地方推荐服务结果。"""

    result: PlaceRecommendationResult
    provider: str
    model: str
    fallback: bool = False


logger = get_logger("trip_plan.service")


class TripPlanService:
    """行程规划统一服务入口。"""

    def __init__(self, agent: PlaceRecommendationAgent | None = None) -> None:
        self.agent = agent or PlaceRecommendationAgent()

    def recommend_places(self, requirement: str) -> PlaceRecommendationServiceResult:
        """根据用户一句话生成地方推荐。"""

        requirement = requirement.strip()
        if not requirement:
            logger.warning("地方推荐请求缺少 requirement")
            raise ValueError("requirement 不能为空")

        logger.info("开始生成地方推荐 requirement_length=%s", len(requirement))

        try:
            agent_result = self.agent.run(requirement)
            destinations = self._normalize_destinations(agent_result.result.destinations)
            if not destinations:
                logger.warning("地方推荐 Agent 返回空结果，启用静态兜底")
                return self._fallback_result(agent_result.result.notice)
            logger.info(
                "地方推荐完成 count=%s provider=%s model=%s",
                len(destinations),
                agent_result.provider,
                agent_result.model,
            )
            return PlaceRecommendationServiceResult(
                result=PlaceRecommendationResult(
                    destinations=destinations,
                    notice=agent_result.result.notice,
                ),
                provider=agent_result.provider,
                model=agent_result.model,
            )
        except AgentError as exc:
            logger.warning("地方推荐 Agent 调用失败，启用静态兜底: %s", exc)
            return self._fallback_result("智能推荐暂时不可用，已为你展示通用文化旅行推荐。")

    def _normalize_destinations(
        self,
        destinations: list[PlaceRecommendation],
    ) -> list[PlaceRecommendation]:
        normalized: list[PlaceRecommendation] = []
        seen_ids: set[str] = set()
        for destination in destinations[:3]:
            dest_id = destination.id.strip().lower()
            if not dest_id:
                continue
            if dest_id in seen_ids:
                continue
            seen_ids.add(dest_id)
            normalized.append(
                PlaceRecommendation(
                    id=dest_id,
                    province=destination.province.strip(),
                    city=destination.city.strip(),
                    matchScore=max(0, min(100, destination.matchScore)),
                    tags=destination.tags or ["文化旅行"],
                    reasons=destination.reasons or ["适合文化旅行体验。"],
                    intro=destination.intro.strip(),
                )
            )
        return normalized

    def _fallback_result(self, notice: str) -> PlaceRecommendationServiceResult:
        logger.info("地方推荐静态兜底 count=%s", len(FALLBACK_DESTINATIONS))
        return PlaceRecommendationServiceResult(
            result=PlaceRecommendationResult(
                destinations=FALLBACK_DESTINATIONS,
                notice=notice,
            ),
            provider="fallback",
            model="static",
            fallback=True,
        )
