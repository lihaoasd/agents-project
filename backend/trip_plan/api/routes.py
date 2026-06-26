"""行程规划 API 路由。"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from trip_plan.api.schemas import (
    AgentMeta,
    CulturalInterpretationsRequest,
    CulturalInterpretationsResponse,
    PlaceRecommendationRequest,
    PlaceRecommendationResponse,
    RoutePlanRequest,
    RoutePlanResponse,
    ScenicSpotsRequest,
    ScenicSpotsResponse,
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


@router.post(
    "/scenic-spots",
    response_model=ScenicSpotsResponse,
    summary="根据用户需求和选定目的地推荐文化旅行景点",
)
async def recommend_scenic_spots(request: ScenicSpotsRequest) -> ScenicSpotsResponse:
    """根据用户需求+选定目的地生成景点推荐。"""

    try:
        result = await asyncio.to_thread(
            trip_plan_service.recommend_scenic_spots,
            request.requirement,
            request.destinationId,
            request.destinationCity,
            request.destinationProvince,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ScenicSpotsResponse(
        data=result.result,
        meta=AgentMeta(
            provider=result.provider,
            model=result.model,
            fallback=result.fallback,
        ),
    )


@router.post(
    "/cultural-interpretations",
    response_model=CulturalInterpretationsResponse,
    summary="根据用户需求和已选景点生成综合文化解读",
)
async def recommend_cultural_interpretations(
    request: CulturalInterpretationsRequest,
) -> CulturalInterpretationsResponse:
    """根据用户需求、目的地和景点生成历史、风俗、地理综合文化解读。"""

    try:
        result = await asyncio.to_thread(
            trip_plan_service.recommend_cultural_interpretations,
            request.requirement,
            request.destinationId,
            request.destinationCity,
            request.destinationProvince,
            request.spots,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CulturalInterpretationsResponse(
        data=result.result,
        meta=AgentMeta(
            provider=result.provider,
            model=result.model,
            fallback=result.fallback,
        ),
    )


@router.post(
    "/routes",
    response_model=RoutePlanResponse,
    summary="根据推荐目的地和已选景点直接规划地图路线",
)
async def plan_route(request: RoutePlanRequest) -> RoutePlanResponse:
    """根据推荐目的地、景点和行程约束直接规划自驾或公共交通路线。"""

    try:
        result = await trip_plan_service.plan_route(
            request.requirement,
            request.destinationId,
            request.destinationCity,
            request.destinationProvince,
            request.spots,
            request.mode,
            request.origin.model_dump() if request.origin else None,
            request.destination.model_dump() if request.destination else None,
            request.constraints,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RoutePlanResponse(
        data=result.result,
        meta=AgentMeta(
            provider=result.provider,
            model=result.model,
            fallback=result.fallback,
        ),
    )