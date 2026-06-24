"""行程规划业务配置。"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict


class TripPlanConfig(BaseSettings):
    """行程规划模块的专有业务配置。"""

    default_days: int = Field(default=3, ge=1, le=14, validation_alias="TRIP_PLAN_DEFAULT_DAYS")
    default_budget: str = Field(default="中等", validation_alias="TRIP_PLAN_DEFAULT_BUDGET")
    max_city_recommendations: int = Field(
        default=3,
        ge=1,
        le=10,
        validation_alias="TRIP_PLAN_MAX_CITY_RECOMMENDATIONS",
    )
    max_spot_recommendations: int = Field(
        default=5,
        ge=1,
        le=20,
        validation_alias="TRIP_PLAN_MAX_SPOT_RECOMMENDATIONS",
    )
    disclaimer: str = Field(
        default="文化、开放时间和费用可能变化，出行前需核实。",
        validation_alias="TRIP_PLAN_DISCLAIMER",
    )

    _env_file: Path = PrivateAttr()

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __init__(self, env_file: Path | None = None) -> None:
        backend_dir = Path(__file__).resolve().parents[2]
        self._env_file = env_file or backend_dir / ".env"
        super().__init__(_env_file=self._env_file, _env_file_encoding="utf-8", _env={})


__all__ = ["TripPlanConfig"]
