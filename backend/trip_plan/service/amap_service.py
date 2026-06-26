"""高德地图 Web 服务 API 封装。"""

from __future__ import annotations

from typing import Any

import asyncio
import httpx
from config import AmapConfig
from logging_config import get_logger

logger = get_logger("trip_plan.amap")


class AmapError(RuntimeError):
    """高德 API 调用异常。"""


class AmapService:
    """高德地图 Web 服务 API 客户端。"""

    BASE_URL = "https://restapi.amap.com/v3"

    def __init__(self, config: AmapConfig | None = None) -> None:
        self.config = config or AmapConfig()
        self.key = self.config.web_service_key
        if not self.key:
            raise AmapError("缺少 AMAP_WEB_SERVICE_KEY，请在 backend/.env 中配置")

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        request_params = {**params, "key": self.key}
        last_error: Exception | None = None

        for attempt in range(1, 4):
            try:
                async with httpx.AsyncClient(timeout=20) as client:
                    response = await client.get(url, params=request_params)
                    response.raise_for_status()
                    data = response.json()
            except Exception as exc:
                last_error = exc
                logger.warning("高德 API 请求失败 path=%s params=%s error=%s", path, params, exc)
                if attempt < 3:
                    await asyncio.sleep(0.8 * attempt)
                    continue
                raise AmapError("高德地图服务暂时不可用") from exc

            if str(data.get("status")) == "1":
                await asyncio.sleep(0.15)
                return data

            info = data.get("info") or "未知错误"
            infocode = str(data.get("infocode") or "")
            if infocode == "10021" and attempt < 3:
                logger.warning("高德 QPS 超限，%ss 后重试 path=%s info=%s", 0.8 * attempt, path, info)
                await asyncio.sleep(0.8 * attempt)
                continue

            logger.warning("高德 API 返回异常 path=%s info=%s data=%s", path, info, data)
            raise AmapError(f"高德地图服务返回异常：{info}")

        raise AmapError(f"高德地图服务暂时不可用：{last_error}")

    async def geocode(self, address: str, city: str = "") -> dict[str, Any]:
        """地址转经纬度。"""

        data = await self._get(
            "/geocode/geo",
            {
                "address": address,
                "city": city,
                "output": "json",
            },
        )
        geocodes = data.get("geocodes") or []
        if not geocodes:
            raise AmapError(f"未找到地点：{address}")
        item = geocodes[0]
        lng, lat = self._parse_location(item.get("location"))
        return {
            "name": item.get("formatted_address") or address,
            "address": item.get("formatted_address") or address,
            "lng": lng,
            "lat": lat,
            "raw": item,
        }

    async def search_place(self, keyword: str, city: str = "") -> dict[str, Any]:
        """搜索 POI。"""

        data = await self._get(
            "/place/text",
            {
                "keywords": keyword,
                "city": city,
                "offset": 5,
                "page": 1,
                "output": "json",
            },
        )
        pois = data.get("pois") or []
        if not pois:
            raise AmapError(f"未找到地点：{keyword}")
        item = pois[0]
        lng, lat = self._parse_location(item.get("location"))
        return {
            "id": item.get("id") or "",
            "name": item.get("name") or keyword,
            "address": item.get("address") or "",
            "lng": lng,
            "lat": lat,
            "raw": item,
        }

    async def distance_matrix(
        self,
        origins: list[dict[str, Any]],
        destinations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """计算多点距离和耗时矩阵。"""

        origin_text = "|".join(f"{item['lng']},{item['lat']}" for item in origins)
        destination_text = "|".join(f"{item['lng']},{item['lat']}" for item in destinations)
        return await self._get(
            "/distance",
            {
                "origins": origin_text,
                "destination": destination_text,
                "type": 1,
                "output": "json",
            },
        )

    async def driving_route(
        self,
        origin: dict[str, Any],
        destination: dict[str, Any],
        waypoints: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """规划驾车路线。"""

        waypoint_text = ""
        if waypoints:
            waypoint_text = "|".join(f"{item['lng']},{item['lat']}" for item in waypoints)
        data = await self._get(
            "/direction/driving",
            {
                "origin": f"{origin['lng']},{origin['lat']}",
                "destination": f"{destination['lng']},{destination['lat']}",
                "waypoints": waypoint_text,
                "strategy": 10,
                "output": "json",
            },
        )
        route = (data.get("route") or {}).get("paths") or []
        if not route:
            raise AmapError("高德未返回驾车路线")
        return {
            "distance": int(route[0].get("distance") or 0),
            "duration": int(route[0].get("duration") or 0),
            "raw": route[0],
        }

    async def transit_route(
        self,
        origin: dict[str, Any],
        destination: dict[str, Any],
        city: str,
    ) -> dict[str, Any]:
        """规划公共交通路线。"""

        data = await self._get(
            "/direction/transit/integrated",
            {
                "origin": f"{origin['lng']},{origin['lat']}",
                "destination": f"{destination['lng']},{destination['lat']}",
                "city": city,
                "cityd": city,
                "output": "json",
            },
        )
        routes = (data.get("route") or {}).get("transits") or []
        if not routes:
            raise AmapError("高德未返回公共交通路线")
        route = routes[0]
        return {
            "distance": int(route.get("distance") or 0),
            "duration": int(route.get("duration") or 0),
            "transfers": int(route.get("transits_num") or 0),
            "walking_distance": int(route.get("walking_distance") or 0),
            "raw": route,
        }

    @staticmethod
    def _parse_location(location: str | None) -> tuple[float, float]:
        if not location or "," not in location:
            raise AmapError("高德返回的地点缺少经纬度")
        lng_text, lat_text = location.split(",", 1)
        return float(lng_text), float(lat_text)
