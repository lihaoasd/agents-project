"""通用配置读取。

通用配置独立放在 backend/config，供不同业务模块复用。
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, PrivateAttr, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["anthropic", "openai"]


class AppConfig(BaseSettings):
    """应用级配置。"""

    project_name: str = "文化旅行 Agent"
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")

    _env_file: Path = PrivateAttr()

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __init__(self, env_file: Path | None = None) -> None:
        backend_dir = Path(__file__).resolve().parents[1]
        self._env_file = env_file or backend_dir / ".env"
        super().__init__(_env_file=self._env_file, _env_file_encoding="utf-8", _env={})


class LLMConfig(BaseSettings):
    """大模型调用配置。"""

    provider: LLMProvider = Field(default="anthropic", validation_alias="LLM_PROVIDER")
    model: str = Field(default="", validation_alias="LLM_MODEL")
    api_key: SecretStr = Field(default_factory=lambda: SecretStr(""))
    base_url: str = Field(default="", validation_alias="LLM_BASE_URL")
    temperature: float = Field(default=0.2, ge=0, le=2, validation_alias="LLM_TEMPERATURE")
    max_tokens: int = Field(default=4096, gt=0, validation_alias="LLM_MAX_TOKENS")
    timeout_seconds: int = Field(default=120, gt=0, validation_alias="LLM_TIMEOUT_SECONDS")

    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None

    _env_file: Path = PrivateAttr()

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __init__(self, env_file: Path | None = None) -> None:
        backend_dir = Path(__file__).resolve().parents[1]
        self._env_file = env_file or backend_dir / ".env"
        super().__init__(_env_file=self._env_file, _env_file_encoding="utf-8", _env={})

    @model_validator(mode="after")
    def normalize_llm_config(self) -> "LLMConfig":
        provider = self.provider
        api_key_name = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
        api_key = self.anthropic_api_key if provider == "anthropic" else self.openai_api_key
        if api_key is None:
            raise ValueError(f"缺少 {api_key_name}，请在 backend/.env 中配置")

        default_model = "claude-sonnet-4-6" if provider == "anthropic" else "gpt-4.1-mini"
        default_base_url = (
            "https://api.anthropic.com/v1"
            if provider == "anthropic"
            else "https://api.openai.com/v1"
        )

        self.model = self.model or default_model
        self.api_key = api_key
        self.base_url = self.base_url or default_base_url
        return self


class AmapConfig(BaseSettings):
    """高德地图配置。"""

    web_service_key: str = Field(default="", validation_alias="AMAP_WEB_SERVICE_KEY")
    mcp_key: str = Field(default="", validation_alias="AMAP_MCP_KEY")
    js_api_key: str = Field(default="", validation_alias="AMAP_JS_API_KEY")
    js_security_code: str = Field(default="", validation_alias="AMAP_JS_SECURITY_CODE")

    _env_file: Path = PrivateAttr()

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __init__(self, env_file: Path | None = None) -> None:
        backend_dir = Path(__file__).resolve().parents[1]
        self._env_file = env_file or backend_dir / ".env"
        super().__init__(_env_file=self._env_file, _env_file_encoding="utf-8", _env={})


__all__ = [
    "AppConfig",
    "LLMConfig",
    "LLMProvider",
    "AmapConfig",
]
