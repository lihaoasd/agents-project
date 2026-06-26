"""路线排序与评分。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trip_plan.agent.models import ScenicSpot


@dataclass
class RouteConstraints:
    """路线规划约束。"""

    mode: str = "auto"
    pace: str = "balanced"
    prefer_transit: bool = False
    avoid_long_walk: bool = False
    total_duration: int | None = None


DESTINATION_PROFILES: dict[str, dict[str, Any]] = {
    "beijing": {
        "default_origin": "北京市中心",
        "default_destination": "北京市中心",
        "default_mode": "transit",
        "culture_themes": ["皇家文化", "中轴线", "胡同文化", "博物馆"],
    },
    "xian": {
        "default_origin": "西安市中心",
        "default_destination": "西安市中心",
        "default_mode": "driving",
        "culture_themes": ["周秦汉唐", "古城墙", "博物馆", "遗址"],
    },
    "hangzhou": {
        "default_origin": "杭州市中心",
        "default_destination": "杭州市中心",
        "default_mode": "transit",
        "culture_themes": ["西湖", "宋韵文化", "茶文化", "运河文化"],
    },
    "nanjing": {
        "default_origin": "南京市中心",
        "default_destination": "南京市中心",
        "default_mode": "transit",
        "culture_themes": ["六朝文化", "明文化", "民国建筑", "博物馆"],
    },
    "chengdu": {
        "default_origin": "成都市中心",
        "default_destination": "成都市中心",
        "default_mode": "transit",
        "culture_themes": ["蜀文化", "街巷文化", "民俗", "名人纪念地"],
    },
    "dunhuang": {
        "default_origin": "敦煌市区",
        "default_destination": "敦煌市区",
        "default_mode": "driving",
        "culture_themes": ["丝路文化", "石窟艺术", "边塞文化"],
    },
}


class RouteOptimizer:
    """根据交通成本和文化匹配度排序景点。"""

    def __init__(self, destination_id: str, constraints: RouteConstraints) -> None:
        self.destination_id = destination_id
        self.constraints = constraints
        self.profile = DESTINATION_PROFILES.get(destination_id, {})
        self.culture_themes = self.profile.get("culture_themes", [])

    def resolve_mode(self, requirement: str = "") -> str:
        """解析最终交通方式。"""

        text = requirement.lower()
        if self.constraints.mode in {"driving", "transit"}:
            return self.constraints.mode
        if any(key in text for key in ["自驾", "开车", "驾车"]):
            return "driving"
        if any(key in text for key in ["公交", "地铁", "公共交通"]):
            return "transit"
        if self.constraints.prefer_transit:
            return "transit"
        return self.profile.get("default_mode", "transit")

    def resolve_origin(self, origin: dict[str, Any] | None) -> dict[str, Any]:
        """解析起点。"""

        if origin and origin.get("name"):
            return origin
        return {"name": self.profile.get("default_origin", "市中心")}

    def resolve_destination(self, destination: dict[str, Any] | None) -> dict[str, Any]:
        """解析终点。"""

        if destination and destination.get("name"):
            return destination
        return {"name": self.profile.get("default_destination", "市中心")}

    def score_spot(self, spot: ScenicSpot) -> float:
        """计算景点文化匹配分。"""

        text = " ".join(
            [
                spot.name,
                spot.type,
                " ".join(spot.cultureTags or []),
                spot.recommendReason,
            ]
        )
        score = 0.5
        for theme in self.culture_themes:
            if theme in text:
                score += 0.15
        return min(score, 1.0)

    def optimize_order(
        self,
        spots: list[ScenicSpot],
        origin: dict[str, Any],
        destination: dict[str, Any],
        distance_matrix: dict[str, Any] | None = None,
    ) -> list[ScenicSpot]:
        """使用贪心算法生成景点顺序。"""

        if len(spots) <= 1:
            return spots

        remaining = list(spots)
        ordered: list[ScenicSpot] = []
        current = origin

        while remaining:
            next_spot = max(
                remaining,
                key=lambda spot: self._next_score(current, spot, destination, distance_matrix),
            )
            ordered.append(next_spot)
            remaining.remove(next_spot)
            current = {
                "name": next_spot.name,
                "lng": getattr(next_spot, "lng", None),
                "lat": getattr(next_spot, "lat", None),
            }

        return ordered

    def _next_score(
        self,
        current: dict[str, Any],
        spot: ScenicSpot,
        destination: dict[str, Any],
        distance_matrix: dict[str, Any] | None,
    ) -> float:
        culture_score = self.score_spot(spot)
        travel_penalty = self._estimate_travel_penalty(current, spot, distance_matrix)
        end_penalty = self._estimate_end_penalty(spot, destination, distance_matrix)
        pace_bonus = self._pace_bonus(spot)

        if self.constraints.pace == "relaxed":
            return culture_score * 0.45 - travel_penalty * 0.35 - end_penalty * 0.10 + pace_bonus
        if self.constraints.pace == "intensive":
            return culture_score * 0.35 - travel_penalty * 0.25 - end_penalty * 0.10 + pace_bonus
        return culture_score * 0.40 - travel_penalty * 0.30 - end_penalty * 0.10 + pace_bonus

    @staticmethod
    def _estimate_travel_penalty(
        current: dict[str, Any],
        spot: ScenicSpot,
        distance_matrix: dict[str, Any] | None,
    ) -> float:
        if not distance_matrix:
            return 0.0
        return 0.0

    @staticmethod
    def _estimate_end_penalty(
        spot: ScenicSpot,
        destination: dict[str, Any],
        distance_matrix: dict[str, Any] | None,
    ) -> float:
        if not distance_matrix:
            return 0.0
        return 0.0

    @staticmethod
    def _pace_bonus(spot: ScenicSpot) -> float:
        visit_text = spot.visitTime or ""
        if any(key in visit_text for key in ["1", "1.5", "半日"]):
            return 0.05
        return 0.0
