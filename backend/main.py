"""FastAPI 启动入口。"""

from __future__ import annotations

import logging
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import AppConfig
from logging_config import get_logger, setup_logging
from debate.api.routes import router as debate_router
from trip_plan.api import router as trip_plan_router

setup_logging()
logger = get_logger("trip_plan.api")

app_config = AppConfig()

app = FastAPI(
    title=app_config.project_name,
    description="文化旅行 Agent 后端 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.app_config = app_config
app.include_router(trip_plan_router)
app.include_router(debate_router)


@app.get("/")
async def root() -> dict[str, str]:
    """返回 API 基础信息。"""

    return {
        "service": app_config.project_name,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health() -> dict[str, str | bool]:
    """健康检查接口。"""

    return {
        "status": "ok",
        "debug": app_config.debug,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
