"""行程规划 API 请求和响应模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from trip_plan.agent.models import (
    CulturalInterpretationsResult,
    PlaceRecommendationResult,
    ScenicSpot,
    ScenicSpotsResult,
)


class PlaceRecommendationRequest(BaseModel):
    """地方推荐请求。"""

    requirement: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户输入的一段文化旅行需求",
    )


class ScenicSpotsRequest(BaseModel):
    """景点推荐请求。"""

    requirement: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户的原始文化旅行需求",
    )
    destinationId: str = Field(
        ...,
        min_length=1,
        description="已选目的地 id",
    )
    destinationCity: str = Field(
        default="",
        description="已选目的地城市",
    )
    destinationProvince: str = Field(
        default="",
        description="已选目的地省份",
    )


class CulturalInterpretationsRequest(BaseModel):
    """综合文化解读请求。"""

    requirement: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户的原始文化旅行需求",
    )
    destinationId: str = Field(
        ...,
        min_length=1,
        description="已选目的地 id",
    )
    destinationCity: str = Field(
        default="",
        description="已选目的地城市",
    )
    destinationProvince: str = Field(
        default="",
        description="已选目的地省份",
    )
    spots: list[ScenicSpot] = Field(
        ...,
        description="已生成的景点列表",
    )


class AgentMeta(BaseModel):
    """Agent 元信息。"""

    provider: str
    model: str
    fallback: bool = False


class PlaceRecommendationResponse(BaseModel):
    """地方推荐响应。"""

    data: PlaceRecommendationResult
    meta: AgentMeta


class ScenicSpotsResponse(BaseModel):
    """景点推荐响应。"""

    data: ScenicSpotsResult
    meta: AgentMeta


class CulturalInterpretationsResponse(BaseModel):
    """综合文化解读响应。"""

    data: CulturalInterpretationsResult
    meta: AgentMeta


class RoutePoint(BaseModel):
    """路线点位。"""

    name: str = Field(..., description="点位名称")
    address: str = Field(default="", description="点位地址")
    lng: float | None = Field(default=None, description="经度")
    lat: float | None = Field(default=None, description="纬度")


class RoutePlanRequest(BaseModel):
    """路线规划请求。"""

    requirement: str = Field(..., min_length=1, max_length=2000, description="用户原始文化旅行需求")
    destinationId: str = Field(..., min_length=1, description="推荐目的地 id")
    destinationCity: str = Field(default="", description="推荐目的地城市")
    destinationProvince: str = Field(default="", description="推荐目的地省份")
    spots: list[ScenicSpot] = Field(..., description="已生成的景点列表")
    mode: str = Field(default="auto", description="出行方式：auto/driving/transit")
    origin: RoutePoint | None = Field(default=None, description="起点")
    destination: RoutePoint | None = Field(default=None, description="终点")
    constraints: dict[str, Any] = Field(default_factory=dict, description="路线约束")


class RoutePlanResponse(BaseModel):
    """路线规划响应。"""

    data: dict[str, Any]
    meta: AgentMeta
