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

    id: str = Field(description="景点标识")
    name: str = Field(description="景点名称")
    address: str = Field(description="景点地址")
    type: str = Field(description="景点类型，如遗址博物馆、综合博物馆、文化景观")
    recommendReason: str = Field(description="推荐理由")
    visitTime: str = Field(description="建议游览时长")
    ticket: str = Field(description="门票信息")
    openingHours: str = Field(description="开放时间")
    cultureTags: list[str] = Field(default_factory=list, description="文化标签")
    imageAlt: str = Field(default="", description="图片替代文字")
    imageUrl: str = Field(default="", description="图片链接")


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


class PlaceRecommendation(BaseModel):
    """前端地方推荐卡片模型。"""

    id: str = Field(description="前端静态数据中的目的地 id")
    province: str = Field(description="省份、直辖市或自治区")
    city: str = Field(description="地市名称")
    matchScore: int = Field(description="匹配度，范围 0-100", ge=0, le=100)
    tags: list[str] = Field(default_factory=list, description="适合前端展示的标签")
    reasons: list[str] = Field(default_factory=list, description="推荐理由列表")
    intro: str = Field(description="目的地简介")


class PlaceRecommendationResult(BaseModel):
    """地方推荐结果。"""

    destinations: list[PlaceRecommendation] = Field(
        default_factory=list,
        description="推荐地方列表，默认 3 个左右",
    )
    notice: str = Field(default="已根据您的需求生成地方推荐。")


class PlaceRecommendationAgentResult(BaseModel):
    """地方推荐 Agent 运行结果包装。"""

    result: PlaceRecommendationResult
    model: str
    provider: str


class ScenicSpotsResult(BaseModel):
    """景点推荐结果。"""

    spots: list[ScenicSpot] = Field(
        default_factory=list,
        description="推荐景点列表，默认 3-5 个",
    )
    notice: str = Field(default="已根据需求生成景点推荐。")


class ScenicSpotsAgentResult(BaseModel):
    """景点推荐 Agent 运行结果包装。"""

    result: ScenicSpotsResult
    model: str
    provider: str
