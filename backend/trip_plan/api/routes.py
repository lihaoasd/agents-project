from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from agent.trip_agent import TripAgent


router = APIRouter()
trip_agent = TripAgent()


class TravelPlanRequest(BaseModel):
    requirement: str = Field(..., description="用户旅游要求，例如：想带孩子了解唐代文化，3天，预算中等")
    days: int = Field(2, ge=1, le=15, description="旅行天数")
    budget: str = Field("中等", description="预算水平，例如：经济、中等、舒适")
    interests: list[str] = Field(default_factory=list, description="兴趣标签，例如：历史、文化、美食、亲子")
    language: str = Field("zh-CN", description="输出语言")


class TravelPlanResponse(BaseModel):
    request_id: str
    generated_at: str
    data: dict[str, Any]


def _model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[attr-defined]
    return model.dict()  # type: ignore[attr-defined]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "cultural-travel-agent-backend"}


@router.post("/travel-plan", response_model=TravelPlanResponse)
def create_travel_plan(request: TravelPlanRequest) -> TravelPlanResponse:
    data = trip_agent.generate_plan(_model_to_dict(request))
    return TravelPlanResponse(
        request_id=data["request_id"],
        generated_at=datetime.now(timezone.utc).isoformat(),
        data=data,
    )


@router.get("/cities")
def list_cities(q: str | None = Query(None, description="关键词，例如：唐代、园林、亲子")) -> dict[str, Any]:
    return {"cities": trip_agent.service.get_cities(q)}


@router.get("/scenic-spots")
def list_scenic_spots(
    city_id: str | None = Query(None, description="城市 ID，例如：xian、beijing"),
    q: str | None = Query(None, description="景点关键词"),
    limit: int = Query(6, ge=1, le=20, description="返回数量"),
) -> dict[str, Any]:
    return {"spots": trip_agent.service.get_scenic_spots(city_id=city_id, query=q, limit=limit)}


@router.get("/scenic-spots/{spot_id}/detail")
def get_scenic_spot_detail(spot_id: str) -> dict[str, Any]:
    detail = trip_agent.service.get_spot_detail(spot_id)
    if not detail:
        raise HTTPException(status_code=404, detail="景点不存在")
    return {"spot": detail}


@router.get("/routes")
def get_routes(
    spot_ids: str = Query(..., description="景点 ID 列表，使用英文逗号分隔"),
    city_id: str | None = Query(None, description="城市 ID"),
    days: int = Query(2, ge=1, le=15, description="旅行天数"),
) -> dict[str, Any]:
    ids = [item.strip() for item in spot_ids.split(",") if item.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="spot_ids 不能为空")
    return {"route": trip_agent.service.build_route(ids, city_id=city_id, days=days)}


@router.get("/recommendations")
def get_recommendations(
    requirement: str = Query("", description="旅游要求"),
    city_id: str | None = Query(None, description="城市 ID"),
    spot_ids: str = Query("", description="景点 ID 列表，使用英文逗号分隔"),
) -> dict[str, Any]:
    ids = [item.strip() for item in spot_ids.split(",") if item.strip()]
    return {
        "recommendations": trip_agent.service.get_recommendations(
            requirement=requirement,
            city_id=city_id,
            spot_ids=ids,
        )
    }


@router.get("/")
def api_root() -> dict[str, str]:
    return {
        "name": "文化旅行 Agent API",
        "docs": "/docs",
        "health": "/api/health",
        "request_id_prefix": "ct_" + uuid.uuid4().hex[:8],
    }
