"""行程规划 API 请求和响应模型。"""

from __future__ import annotations

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
