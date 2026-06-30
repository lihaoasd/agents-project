"""辩论 API 路由。"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/debate", tags=["debate"])


@router.get("/health", summary="辩论模块健康检查")
async def health() -> dict[str, str | bool]:
    """返回辩论模块健康状态。"""
    return {"status": "ok", "module": "debate"}