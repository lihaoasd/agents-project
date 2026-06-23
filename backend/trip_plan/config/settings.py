from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
TRIP_PLAN_DIR = Path(__file__).resolve().parents[1]

# 只读取项目内 backend/.env；不要求用户设置系统环境变量。
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str = "文化旅行 Agent"
    version: str = "0.1.0"
    default_language: str = "zh-CN"
    cors_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
    amap_key: str = ""
    enable_amap: bool = False
    llm_api_key: str = ""
    enable_llm: bool = False
    mcp_config_path: Path | None = None


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    mcp_config_path_raw = os.getenv("MCP_CONFIG_PATH", "").strip()
    mcp_config_path = Path(mcp_config_path_raw) if mcp_config_path_raw else None

    return Settings(
        app_name=os.getenv("APP_NAME", "文化旅行 Agent"),
        version=os.getenv("APP_VERSION", "0.1.0"),
        default_language=os.getenv("DEFAULT_LANGUAGE", "zh-CN"),
        cors_origins=tuple(
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            ).split(",")
            if origin.strip()
        ),
        amap_key=os.getenv("AMAP_KEY", "").strip(),
        enable_amap=_parse_bool(
            os.getenv("ENABLE_AMAP"),
            default=bool(os.getenv("AMAP_KEY", "").strip()),
        ),
        llm_api_key=os.getenv("ANTHROPIC_API_KEY", "").strip(),
        enable_llm=_parse_bool(
            os.getenv("ENABLE_LLM"),
            default=bool(os.getenv("ANTHROPIC_API_KEY", "").strip()),
        ),
        mcp_config_path=mcp_config_path,
    )
