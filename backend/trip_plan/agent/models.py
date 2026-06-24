"""行程规划 Agent 输出模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TravelDestination(BaseModel):
    """推荐目的地。"""

    province: str = Field(description="推荐省份或自治区")
    city: str = Field(description="推荐地市")
    reason: str = Field(description="推荐理由")


class ScenicSpot(BaseModel):
    """推荐景点。"""

    name: str
    address: str = Field(description="景点地址")
    reason: str = Field(description="推荐理由")
    tags: list[str] = Field(default_factory=list, description="文化标签，例如 历史、博物馆、非遗")


class RouteSegment(BaseModel):
    """路线分段。"""

    from_spot: str = Field(description="起点")
    to_spot: str = Field(description="终点")
    transport: str = Field(description="推荐交通方式")
    duration: str = Field(description="预计耗时")
    description: str = Field(description="路线说明")


class ContentRecommendation(BaseModel):
    """书籍、短视频或文章推荐。"""

    title: str
    type: str = Field(description="内容类型：书籍、短视频、文章")
    reason: str = Field(description="推荐理由")


class TravelPlan(BaseModel):
    """行程规划完整结果。"""

    requirement: str = Field(description="用户原始需求摘要")
    destination: TravelDestination
    spots: list[ScenicSpot] = Field(default_factory=list)
    route: list[RouteSegment] = Field(default_factory=list)
    content_recommendations: list[ContentRecommendation] = Field(default_factory=list)
    disclaimer: str


class TravelPlanResult(BaseModel):
    """Agent 运行结果包装。"""

    plan: TravelPlan
    model: str
    provider: str
