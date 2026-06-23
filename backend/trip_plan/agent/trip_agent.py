from __future__ import annotations

from typing import Any

from service.trip_service import TripService


class TripAgent:
    """旅行需求理解与结果编排。

    当前 MVP 使用本地规则模板降级运行；后续可在 generate_plan 中接入 LLM / MCP。
    """

    def __init__(self) -> None:
        self.service = TripService()

    def generate_plan(self, request: dict[str, Any]) -> dict[str, Any]:
        requirement = (request.get("requirement") or "").strip()
        days = int(request.get("days") or 2)
        budget = (request.get("budget") or "中等").strip() or "中等"
        interests = request.get("interests") or []
        language = (request.get("language") or "zh-CN").strip() or "zh-CN"

        cities = self.service.select_cities(
            requirement=requirement,
            interests=interests,
            days=days,
            budget=budget,
        )
        primary_city = cities[0] if cities else {"id": "xian", "city": "西安市", "province": "陕西省"}

        spots = self.service.get_scenic_spots(
            city_id=primary_city["id"],
            query=requirement,
            limit=min(6, max(3, days + 2)),
        )
        spot_ids = [spot["id"] for spot in spots]

        details = []
        for spot_id in spot_ids:
            detail = self.service.get_spot_detail(spot_id)
            if detail:
                details.append(detail)

        route = self.service.build_route(
            spot_ids=spot_ids,
            city_id=primary_city["id"],
            days=days,
        )
        recommendations = self.service.get_recommendations(
            requirement=requirement,
            city_id=primary_city["id"],
            spot_ids=spot_ids,
        )

        return {
            "request_id": "plan_" + str(abs(hash((requirement, days, budget, language))) % 1000000),
            "requirement": requirement,
            "days": days,
            "budget": budget,
            "language": language,
            "cities": cities,
            "spots": spots,
            "spot_details": details,
            "route": route,
            "recommendations": recommendations,
            "disclaimer": "文化介绍、开放时间、票价和路线可能变化，出行前请以景区、博物馆和地图平台实时信息为准。",
            "source": "local_rule_template",
        }
