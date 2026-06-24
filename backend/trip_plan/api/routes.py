"""行程规划 API 路由。"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from trip_plan.api.schemas import (
    AgentMeta,
    PlaceRecommendationRequest,
    PlaceRecommendationResponse,
)
from trip_plan.service.trip_plan_service import TripPlanService

router = APIRouter(prefix="/api/trip-plan", tags=["trip-plan"])
trip_plan_service = TripPlanService()


@router.post(
    "/place-recommendations",
    response_model=PlaceRecommendationResponse,
    summary="根据用户一句话生成文化旅行地方推荐",
)
async def recommend_places(request: PlaceRecommendationRequest) -> PlaceRecommendationResponse:
    """根据用户文化旅行需求生成地方推荐。"""

    try:
        result = await asyncio.to_thread(
            trip_plan_service.recommend_places,
            request.requirement,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PlaceRecommendationResponse(
        data=result.result,
        meta=AgentMeta(
            provider=result.provider,
            model=result.model,
            fallback=result.fallback,
        ),
    )
