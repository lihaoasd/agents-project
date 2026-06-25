"""Unsplash 图片检索服务。"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from logging_config import get_logger

logger = get_logger("trip_plan.service.unsplash_image")

_CACHE_MISS = object()


@dataclass(frozen=True)
class UnsplashImage:
    """Unsplash 图片检索结果。"""

    url: str
    thumbnailUrl: str
    alt: str = ""
    photographerName: str = ""
    sourceUrl: str = ""


class UnsplashImageService:
    """根据景点信息从 Unsplash 检索展示图片。"""

    _BASE_URL = "https://api.unsplash.com/search/photos"

    def __init__(
        self,
        access_key: str | None = None,
        timeout_seconds: float = 3.0,
        cache_ttl_seconds: int = 7 * 24 * 60 * 60,
    ) -> None:
        self._access_key = (
            access_key
            or os.getenv("UNSPLASH_ACCESS_KEY")
            or self._load_env_value("UNSPLASH_ACCESS_KEY")
            or os.getenv("TRIP_PLAN_UNSPLASH_ACCESS_KEY")
            or ""
        ).strip()
        self._timeout_seconds = timeout_seconds
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, tuple[float, UnsplashImage | None]] = {}
        self._disabled_logged = False

    def search_for_spot(
        self,
        spot_name: str,
        city: str = "",
        province: str = "",
        spot_type: str = "",
        preferred_query: str = "",
    ) -> UnsplashImage | None:
        """按优先级检索景点图片。"""

        queries = self._build_queries(spot_name, city, province, spot_type, preferred_query)
        logger.debug(
            "开始 Unsplash 图片检索 spot_name=%s city=%s province=%s type=%s preferred_query=%s queries=%s",
            spot_name,
            city,
            province,
            spot_type,
            preferred_query,
            queries,
        )
        for query in queries:
            image = self.search(query)
            if image:
                logger.info(
                    "Unsplash 图片检索成功 spot_name=%s query=%s source=%s",
                    spot_name,
                    query,
                    image.sourceUrl,
                )
                return image
        logger.info("Unsplash 图片检索无结果 spot_name=%s", spot_name)
        return None

    def search(self, query: str) -> UnsplashImage | None:
        """搜索一张 Unsplash 横图。"""

        normalized_query = self._normalize_query(query)
        if not normalized_query:
            return None
        if not self._access_key:
            self._log_disabled_once()
            return None

        cached = self._cache.get(normalized_query, _CACHE_MISS)
        if cached is not _CACHE_MISS:
            expires_at, image = cached
            if expires_at >= time.time():
                logger.debug("Unsplash 图片缓存命中 query=%s", normalized_query)
                return image
            self._cache.pop(normalized_query, None)

        logger.info("开始调用 Unsplash API query=%s", normalized_query)
        image = self._search_unsplash(normalized_query)
        self._cache[normalized_query] = (time.time() + self._cache_ttl_seconds, image)
        if image:
            logger.debug("Unsplash 图片写入缓存 query=%s", normalized_query)
        return image

    def _search_unsplash(self, query: str) -> UnsplashImage | None:
        headers = {
            "Authorization": f"Client-ID {self._access_key}",
            "Accept-Version": "v1",
        }
        params = {
            "query": query,
            "per_page": "3",
            "orientation": "landscape",
            "language": "zh",
        }

        try:
            with httpx.Client(timeout=self._timeout_seconds, headers=headers) as client:
                response = client.get(self._BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])
                logger.info("Unsplash API 调用成功 query=%s result_count=%s", query, len(results))
        except httpx.HTTPError as exc:
            logger.warning("Unsplash 图片检索失败 query=%s error=%s", query, exc)
            return None
        except ValueError as exc:
            logger.warning("Unsplash 图片响应解析失败 query=%s error=%s", query, exc)
            return None

        return self._pick_image(results)

    @staticmethod
    def _pick_image(results: list[dict]) -> UnsplashImage | None:
        for index, result in enumerate(results, start=1):
            urls = result.get("urls") or {}
            url = urls.get("regular") or urls.get("small") or urls.get("thumb")
            if not url or not str(url).startswith("https://"):
                logger.debug("Unsplash 图片结果跳过 index=%s reason=invalid_url", index)
                continue

            user = result.get("user") or {}
            links = result.get("links") or {}
            source_url = links.get("html") or url
            image = UnsplashImage(
                url=str(url),
                thumbnailUrl=str(urls.get("small") or urls.get("thumb") or url),
                alt=str(result.get("alt_description") or result.get("description") or ""),
                photographerName=str(user.get("name") or ""),
                sourceUrl=str(source_url),
            )
            logger.debug("Unsplash 图片结果可用 index=%s source=%s", index, image.sourceUrl)
            return image
        logger.info("Unsplash API 无可用横图 result_count=%s", len(results))
        return None

    def _build_queries(
        self,
        spot_name: str,
        city: str,
        province: str,
        spot_type: str,
        preferred_query: str = "",
    ) -> list[str]:
        clean_preferred_query = self._clean_query_part(preferred_query)
        clean_spot_name = self._clean_query_part(spot_name)
        clean_city = self._clean_query_part(city)
        clean_province = self._clean_query_part(province)
        clean_spot_type = self._clean_query_part(spot_type)

        queries: list[str] = []
        if clean_preferred_query:
            queries.append(clean_preferred_query)
        if clean_spot_name:
            if clean_city:
                queries.append(f"{clean_spot_name} {clean_city}")
            if clean_province and clean_province != clean_city:
                queries.append(f"{clean_spot_name} {clean_province}")
            queries.append(clean_spot_name)
        if clean_city:
            queries.append(f"{clean_city} 旅行")
            queries.append(f"{clean_city} 风景")
        if clean_spot_type:
            queries.append(f"{clean_spot_type} 中国")

        seen: set[str] = set()
        deduped: list[str] = []
        for query in queries:
            normalized = self._normalize_query(query)
            if normalized and normalized not in seen:
                seen.add(normalized)
                deduped.append(normalized)
        return deduped

    @staticmethod
    def _clean_query_part(value: str) -> str:
        return re.sub(r"\s+", " ", value.replace("，", " ").replace(",", " ")).strip()

    @staticmethod
    def _normalize_query(value: str) -> str:
        return re.sub(r"\s+", " ", value.strip())

    @staticmethod
    def _load_env_value(key: str) -> str:
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if not env_path.exists():
            return ""
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            env_key, value = stripped.split("=", 1)
            if env_key.strip() == key:
                return value.strip().strip('"').strip("'")
        return ""

    def _log_disabled_once(self) -> None:
        if self._disabled_logged:
            return
        logger.warning("未配置 UNSPLASH_ACCESS_KEY，跳过 Unsplash 图片检索")
        self._disabled_logged = True
