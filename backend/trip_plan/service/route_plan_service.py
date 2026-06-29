"""直接路线规划服务。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from logging_config import get_logger
from trip_plan.agent.models import ScenicSpot
from trip_plan.agent.route_plan_agent import RoutePlanAgent
from trip_plan.mcp.amap_mcp_client import AmapMcpError
from trip_plan.service.amap_service import AmapError, AmapService
from trip_plan.service.route_optimizer import RouteConstraints, RouteOptimizer

logger = get_logger("trip_plan.service.route_plan")

STATIC_ROUTES: dict[str, dict[str, Any]] = {
    "xian": {
        "provider": "高德地图静态路线",
        "totalDistance": "约 42 公里",
        "totalDuration": "约 1 小时 35 分钟",
        "description": "推荐从市区城墙出发，先参观陕西历史博物馆，再前往秦始皇帝陵博物院，最后返回城墙区域。",
        "navUrl": "https://uri.amap.com/search?keyword=西安城墙,陕西历史博物馆,秦始皇帝陵博物院",
        "legs": [
            {"from": "西安城墙", "to": "陕西历史博物馆", "distance": "约 5 公里", "duration": "约 20 分钟", "tip": "市区道路较熟，建议避开早晚高峰。"},
            {"from": "陕西历史博物馆", "to": "秦始皇帝陵博物院", "distance": "约 37 公里", "duration": "约 1 小时 15 分钟", "tip": "前往临潼方向路程较长，建议预留充足时间。"},
        ],
    },
    "hangzhou": {
        "provider": "高德地图静态路线",
        "totalDistance": "约 28 公里",
        "totalDuration": "约 1 小时 10 分钟",
        "description": "推荐从西湖核心区开始，随后前往浙江省博物馆之江馆区，最后沿京杭大运河杭州段感受城市生活。",
        "navUrl": "https://uri.amap.com/search?keyword=西湖风景名胜区,浙江省博物馆之江馆区,京杭大运河杭州段",
        "legs": [
            {"from": "西湖风景名胜区", "to": "浙江省博物馆之江馆区", "distance": "约 14 公里", "duration": "约 35 分钟", "tip": "西湖周边人流较大，建议提前规划停车或公共交通。"},
            {"from": "浙江省博物馆之江馆区", "to": "京杭大运河杭州段", "distance": "约 14 公里", "duration": "约 35 分钟", "tip": "晚间可结合运河夜景安排轻松游览。"},
        ],
    },
    "beijing": {
        "provider": "高德地图静态路线",
        "totalDistance": "约 35 公里",
        "totalDuration": "约 1 小时 30 分钟",
        "description": "推荐以故宫为核心，再前往天坛了解礼制建筑，最后到什刹海胡同片区体验老北京街巷。",
        "navUrl": "https://uri.amap.com/search?keyword=故宫博物院,天坛公园,什刹海胡同片区",
        "legs": [
            {"from": "故宫博物院", "to": "天坛公园", "distance": "约 7 公里", "duration": "约 25 分钟", "tip": "故宫参观时间较长，建议控制节奏。"},
            {"from": "天坛公园", "to": "什刹海胡同片区", "distance": "约 12 公里", "duration": "约 40 分钟", "tip": "晚高峰前往前门和鼓楼周边可能拥堵。"},
        ],
    },
    "nanjing": {
        "provider": "高德地图静态路线",
        "totalDistance": "约 22 公里",
        "totalDuration": "约 1 小时",
        "description": "推荐先参观南京博物院，再登明城墙，最后前往南京总统府理解近代历史。",
        "navUrl": "https://uri.amap.com/search?keyword=南京博物院,明城墙,南京总统府",
        "legs": [
            {"from": "南京博物院", "to": "明城墙", "distance": "约 5 公里", "duration": "约 20 分钟", "tip": "可从解放门或台城段登城，视野较好。"},
            {"from": "明城墙", "to": "南京总统府", "distance": "约 4 公里", "duration": "约 18 分钟", "tip": "总统府建议提前预约。"},
        ],
    },
    "chengdu": {
        "provider": "高德地图静态路线",
        "totalDistance": "约 26 公里",
        "totalDuration": "约 1 小时 15 分钟",
        "description": "推荐从锦里古街体验民俗，再前往杜甫草堂，最后参观金沙遗址博物馆。",
        "navUrl": "https://uri.amap.com/search?keyword=锦里古街,杜甫草堂,金沙遗址博物馆",
        "legs": [
            {"from": "锦里古街", "to": "杜甫草堂", "distance": "约 3 公里", "duration": "约 15 分钟", "tip": "两地距离较近，可结合武侯祠片区游览。"},
            {"from": "杜甫草堂", "to": "金沙遗址博物馆", "distance": "约 6 公里", "duration": "约 25 分钟", "tip": "下午参观金沙遗址，时间更从容。"},
        ],
    },
    "dunhuang": {
        "provider": "高德地图静态路线",
        "totalDistance": "约 210 公里",
        "totalDuration": "约 3 小时 30 分钟",
        "description": "推荐以莫高窟为核心，搭配敦煌研究院陈列中心；雅丹地质公园路程较远，建议单独安排半日。",
        "navUrl": "https://uri.amap.com/search?keyword=莫高窟,敦煌研究院陈列中心,雅丹地质公园",
        "legs": [
            {"from": "莫高窟", "to": "敦煌研究院陈列中心", "distance": "约 2 公里", "duration": "约 10 分钟", "tip": "建议先参观数字展示中心，再进入洞窟。"},
            {"from": "敦煌研究院陈列中心", "to": "雅丹地质公园", "distance": "约 180 公里", "duration": "约 3 小时", "tip": "路程较远，注意防晒、补水和车辆安排。"},
        ],
    },
}


@dataclass
class RoutePlanServiceResult:
    """路线规划服务结果。"""

    result: dict[str, Any]
    provider: str
    model: str
    fallback: bool = False


class RoutePlanService:
    """根据推荐目的地和景点直接规划路线。"""

    def __init__(self, amap_service: AmapService | None = None) -> None:
        self.amap_service = amap_service

    async def plan(
        self,
        requirement: str,
        destination_id: str,
        destination_city: str,
        destination_province: str,
        spots: list[ScenicSpot],
        mode: str = "auto",
        origin: dict[str, Any] | None = None,
        destination: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> RoutePlanServiceResult:
        """规划路线：MCP Agent → Web API → 静态兜底。"""

        logger.info(
            "=== 路线规划开始 === destination=%s city=%s spots=%s mode=%s",
            destination_id,
            destination_city,
            len(spots),
            mode,
        )

        normalized_constraints = self._normalize_constraints(mode, constraints or {}, requirement)
        optimizer = RouteOptimizer(destination_id, normalized_constraints)
        resolved_mode = optimizer.resolve_mode(requirement)
        resolved_origin = optimizer.resolve_origin(origin)
        resolved_destination = optimizer.resolve_destination(destination)

        logger.info(
            "约束解析完成 mode=%s pace=%s prefer_transit=%s",
            resolved_mode,
            normalized_constraints.pace,
            normalized_constraints.prefer_transit,
        )

        # 1. 优先使用 MCP Agent（LLM 自主调用高德工具）
        try:
            logger.info("→ 尝试 MCP Agent 路线规划...")
            result = await self._plan_with_mcp_agent(
                requirement=requirement,
                destination_id=destination_id,
                destination_city=destination_city,
                destination_province=destination_province,
                spots=spots,
                mode=resolved_mode,
                origin=resolved_origin,
                destination=resolved_destination,
                constraints=normalized_constraints,
            )
            logger.info(
                "← MCP Agent 路线规划成功 provider=%s model=%s spots=%s segments=%s",
                result.get("provider", "mcp-amap"),
                result.get("model", "N/A"),
                len(result.get("orderedSpots", [])),
                len(result.get("segments", [])),
            )
            return RoutePlanServiceResult(
                result=result,
                provider=result.get("provider", "mcp-amap"),
                model=result.get("model", "mcp-agent"),
                fallback=False,
            )
        except (AmapMcpError, AmapError) as mcp_exc:
            logger.warning(
                "MCP Agent 路线规划失败 → 降级到 Web API: %s",
                mcp_exc,
            )

        # 2. 降级到高德 Web API 直接调用
        try:
            logger.info("→ 尝试高德 Web API 路线规划...")
            result = await self._plan_with_amap(
                requirement=requirement,
                destination_id=destination_id,
                destination_city=destination_city,
                destination_province=destination_province,
                spots=spots,
                mode=resolved_mode,
                origin=resolved_origin,
                destination=resolved_destination,
                constraints=normalized_constraints,
            )
            logger.info(
                "← 高德 Web API 路线规划成功 segments=%s",
                len(result.get("segments", [])),
            )
            return RoutePlanServiceResult(
                result=result,
                provider="amap",
                model="direct-route-service",
                fallback=False,
            )
        except AmapError as exc:
            logger.warning("高德 Web API 路线规划失败 → 降级到静态路线: %s", exc)

        # 3. 静态路线兜底
        logger.info("→ 使用静态路线兜底...")
        result = self._fallback_route(destination_id, spots, resolved_mode, "MCP 和 Web API 均不可用")
        logger.info(
            "← 静态路线兜底 destination=%s fallback=%s",
            destination_id,
            destination_id in STATIC_ROUTES,
        )
        return RoutePlanServiceResult(
            result=result,
            provider="static",
            model="static-route",
            fallback=True,
        )

    async def _plan_with_mcp_agent(
        self,
        requirement: str,
        destination_id: str,
        destination_city: str,
        destination_province: str,
        spots: list[ScenicSpot],
        mode: str,
        origin: dict[str, Any],
        destination: dict[str, Any],
        constraints: RouteConstraints,
    ) -> dict[str, Any]:
        """使用 MCP Agent（LangGraph + 高德 MCP 工具）规划路线。"""
        logger.debug("_plan_with_mcp_agent 开始约束=%s", constraints)

        # 对起终点做地理编码，确保 lng/lat 不为 null（与 _plan_with_amap 对齐）
        service = self.amap_service or AmapService()
        origin = await self._geocode_point(service, origin, destination_city)
        destination = await self._geocode_point(service, destination, destination_city)

        agent = RoutePlanAgent()
        try:
            agent_result = await agent.run(
                requirement=requirement,
                destination_id=destination_id,
                destination_city=destination_city,
                destination_province=destination_province,
                spots=spots,
                mode=mode,
                origin=origin,
                destination=destination,
                constraints={
                    "pace": constraints.pace,
                    "preferTransit": constraints.prefer_transit,
                    "avoidLongWalk": constraints.avoid_long_walk,
                    "totalDuration": constraints.total_duration,
                },
            )
        finally:
            await agent.close()

        result = agent_result.result
        # 合并元信息
        result.setdefault("provider", agent_result.provider)
        result.setdefault("model", agent_result.model)
        result.setdefault("fallback", False)
        result.setdefault("destination", {
            "id": destination_id,
            "city": destination_city,
            "province": destination_province,
        })
        result.setdefault("origin", origin)
        result.setdefault("destinationPoint", destination)
        result.setdefault("mode", mode)
        result.setdefault("navUrl", "")
        result.setdefault("notices", [])

        # 从 segments 累加总距离和总时间（不依赖 LLM 输出），用于前端计算
        segments = result.get("segments", [])
        result["totalDistanceMeters"] = sum(
            int(seg.get("distanceMeters", seg.get("distance", 0)) or 0)
            for seg in segments
        )
        result["totalDurationSeconds"] = sum(
            int(seg.get("durationSeconds", seg.get("duration", 0)) or 0)
            for seg in segments
        )

        # 补充 segments 中每条路段的距离/耗时格式化
        result["segments"] = self._ensure_segment_units(segments)

        # 确保 orderedSpots 格式兼容
        result["orderedSpots"] = self._ensure_lng_lat_present(
            result.get("orderedSpots", [])
        )
        return result

    async def _plan_with_amap(
        self,
        requirement: str,
        destination_id: str,
        destination_city: str,
        destination_province: str,
        spots: list[ScenicSpot],
        mode: str,
        origin: dict[str, Any],
        destination: dict[str, Any],
        constraints: RouteConstraints,
    ) -> dict[str, Any]:
        logger.debug("_plan_with_amap 开始 spots=%s mode=%s", len(spots), mode)
        service = self.amap_service or AmapService()
        processed_spots = self._process_spots(service, spots, destination_city)
        if not processed_spots:
            raise AmapError("没有可用于规划的景点")
        logger.info("Web API 处理后景点: %s -> %s", len(spots), len(processed_spots))

        origin = await self._geocode_point(service, origin, destination_city)
        destination = await self._geocode_point(service, destination, destination_city)
        processed_spots = [
            await self._ensure_location(service, spot, destination_city)
            for spot in processed_spots
        ]

        optimizer = RouteOptimizer(destination_id, constraints)
        ordered_spots = optimizer.optimize_order(processed_spots, origin, destination)
        route_points = [
            origin,
            *[self._spot_to_point(spot) for spot in ordered_spots],
            destination,
        ]
        segments = await self._plan_segments(service, route_points, mode, destination_city)

        total_distance = sum(int(segment.get("distanceMeters") or 0) for segment in segments)
        total_duration = sum(int(segment.get("durationSeconds") or 0) for segment in segments)
        nav_keywords = ",".join([origin["name"], *(spot.name for spot in ordered_spots), destination["name"]])

        return {
            "provider": "amap",
            "fallback": False,
            "mode": mode,
            "destination": {
                "id": destination_id,
                "city": destination_city,
                "province": destination_province,
            },
            "origin": origin,
            "destinationPoint": destination,
            "orderedSpots": self._ensure_lng_lat_present([self._spot_to_dict(spot) for spot in ordered_spots]),
            "totalDistanceMeters": total_distance,
            "totalDurationSeconds": total_duration,
            "totalDistance": self._format_distance(total_distance),
            "totalDuration": self._format_duration(total_duration),
            "segments": segments,
            "navUrl": f"https://uri.amap.com/search?keyword={nav_keywords}",
            "notices": self._build_notices(requirement, mode, origin, destination),
        }

    def _process_spots(
        self,
        service: AmapService,
        spots: list[ScenicSpot],
        city: str,
    ) -> list[ScenicSpot]:
        normalized: list[ScenicSpot] = []
        seen_ids: set[str] = set()
        for spot in spots[:5]:
            spot_id = spot.id.strip().lower()
            if not spot_id or spot_id in seen_ids:
                continue
            seen_ids.add(spot_id)
            normalized.append(spot)
        return normalized

    async def _ensure_location(
        self,
        service: AmapService,
        spot: ScenicSpot,
        city: str,
    ) -> ScenicSpot:
        if getattr(spot, "lng", None) and getattr(spot, "lat", None):
            return spot
        try:
            poi = await service.search_place(spot.name, city)
            spot.lng = poi["lng"]
            spot.lat = poi["lat"]
            spot.address = poi.get("address") or spot.address
        except AmapError:
            geo = await service.geocode(f"{spot.name}{spot.address}", city)
            spot.lng = geo["lng"]
            spot.lat = geo["lat"]
            spot.address = geo.get("address") or spot.address
        return spot

    async def _geocode_point(
        self,
        service: AmapService,
        point: dict[str, Any],
        city: str,
    ) -> dict[str, Any]:
        if point.get("lng") and point.get("lat"):
            return point
        name = point.get("name") or point.get("address") or city
        address = point.get("address") or name
        try:
            poi = await service.search_place(name, city)
            return {
                "name": poi["name"],
                "address": poi.get("address") or address,
                "lng": poi["lng"],
                "lat": poi["lat"],
            }
        except AmapError:
            geo = await service.geocode(address, city)
            return {
                "name": geo.get("name") or name,
                "address": geo.get("address") or address,
                "lng": geo["lng"],
                "lat": geo["lat"],
            }

    async def _plan_segments(
        self,
        service: AmapService,
        points: list[dict[str, Any]],
        mode: str,
        city: str,
    ) -> list[dict[str, Any]]:
        segments: list[dict[str, Any]] = []
        for index in range(len(points) - 1):
            origin = points[index]
            destination = points[index + 1]
            transport = "路线规划失败"
            try:
                if mode == "driving":
                    route = await service.driving_route(origin, destination)
                    transport = "自驾"
                    detail = self._format_driving_detail(route)
                else:
                    route = await service.transit_route(origin, destination, city)
                    transport = "公共交通"
                    detail = self._format_transit_detail(route)
            except AmapError as exc:
                detail = str(exc)
                route = {"distance": 0, "duration": 0}
            segments.append(
                {
                    "from": origin["name"],
                    "to": destination["name"],
                    "transport": transport,
                    "distance": self._format_distance(int(route.get("distance") or 0)),
                    "distanceMeters": int(route.get("distance") or 0),
                    "duration": self._format_duration(int(route.get("duration") or 0)),
                    "durationSeconds": int(route.get("duration") or 0),
                    "detail": detail,
                }
            )
        return segments

    @staticmethod
    def _format_driving_detail(route: dict[str, Any]) -> str:
        raw = route.get("raw") or {}
        steps = raw.get("steps") or []
        if not steps:
            return "已根据高德驾车路线规划生成路线。"
        first = steps[0]
        return first.get("instruction") or "已根据高德驾车路线规划生成路线。"

    @staticmethod
    def _format_transit_detail(route: dict[str, Any]) -> str:
        raw = route.get("raw") or {}
        segments = raw.get("segments") or []
        if not segments:
            return "已根据高德公共交通路线规划生成路线。"
        walking = segments[0].get("walking") or {}
        return walking.get("instruction") or "已根据高德公共交通路线规划生成路线。"

    @staticmethod
    def _normalize_constraints(
        mode: str,
        constraints: dict[str, Any],
        requirement: str,
    ) -> RouteConstraints:
        text = requirement.lower()
        prefer_transit = bool(constraints.get("preferTransit")) or any(
            key in text for key in ["公交", "地铁", "公共交通"]
        )
        avoid_long_walk = bool(constraints.get("avoidLongWalk")) or any(
            key in text for key in ["少走路", "少走", "不要走太多", "不累", "轻松"]
        )
        total_duration = constraints.get("totalDuration")
        if isinstance(total_duration, str) and total_duration.isdigit():
            total_duration = int(total_duration)
        return RouteConstraints(
            mode=mode,
            pace=str(constraints.get("pace") or ("relaxed" if avoid_long_walk else "balanced")),
            prefer_transit=prefer_transit,
            avoid_long_walk=avoid_long_walk,
            total_duration=total_duration,
        )

    @staticmethod
    def _build_notices(
        requirement: str,
        mode: str,
        origin: dict[str, Any],
        destination: dict[str, Any],
    ) -> list[str]:
        notices = ["已根据推荐目的地、景点位置和交通耗时生成路线。"]
        if any(key in requirement for key in ["轻松", "不累", "少走路"]):
            notices.append("已优先控制步行和换乘压力。")
        if mode == "transit":
            notices.append("已按公共交通优先规划。")
        if mode == "driving":
            notices.append("已按自驾路线规划。")
        if origin.get("name") == destination.get("name"):
            notices.append("未指定起终点时，已使用城市中心作为默认起终点。")
        return notices

    @staticmethod
    def _ensure_lng_lat_present(spots: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for spot in spots:
            spot.setdefault("lng", None)
            spot.setdefault("lat", None)
        return spots

    @staticmethod
    def _ensure_segment_units(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """确保 segments 中每条都有带单位的 distance 和 duration 字段。

        MCP Agent 输出只含 distance/duration 数字（米/秒），
        这里补充 ``distanceText`` 和 ``durationText`` 用于前端展示。
        """
        for seg in segments:
            distance_m = seg.get("distance", seg.get("distanceMeters", 0))
            duration_s = seg.get("duration", seg.get("durationSeconds", 0))
            seg.setdefault("distanceMeters", int(distance_m) if isinstance(distance_m, (int, float)) else 0)
            seg.setdefault("durationSeconds", int(duration_s) if isinstance(duration_s, (int, float)) else 0)
            seg.setdefault("distance", RoutePlanService._format_distance(int(distance_m or 0)))
            seg.setdefault("duration", RoutePlanService._format_duration(int(duration_s or 0)))
        return segments

    @staticmethod
    def _spot_to_point(spot: ScenicSpot) -> dict[str, Any]:
        return {
            "name": spot.name,
            "address": spot.address,
            "lng": getattr(spot, "lng", None),
            "lat": getattr(spot, "lat", None),
        }

    @staticmethod
    def _spot_to_dict(spot: ScenicSpot) -> dict[str, Any]:
        return {
            "id": spot.id,
            "name": spot.name,
            "address": spot.address,
            "type": spot.type,
            "lng": getattr(spot, "lng", None),
            "lat": getattr(spot, "lat", None),
            "suggestedDuration": RoutePlanService._parse_duration_minutes(spot.visitTime),
            "cultureTags": spot.cultureTags or [],
        }

    @staticmethod
    def _parse_duration_minutes(text: str) -> int | None:
        if not text:
            return None
        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        if not numbers:
            return None
        value = float(numbers[0])
        if "小时" in text:
            return int(value * 60)
        if "分钟" in text:
            return int(value)
        return int(value * 60)

    @staticmethod
    def _format_distance(meters: int) -> str:
        if meters <= 0:
            return "距离待更新"
        if meters < 1000:
            return f"约 {meters} 米"
        return f"约 {meters / 1000:.1f} 公里"

    @staticmethod
    def _format_duration(seconds: int) -> str:
        if seconds <= 0:
            return "耗时待更新"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours and minutes:
            return f"约 {hours} 小时 {minutes} 分钟"
        if hours:
            return f"约 {hours} 小时"
        return f"约 {minutes} 分钟"

    def _fallback_route(
        self,
        destination_id: str,
        spots: list[ScenicSpot],
        mode: str,
        reason: str,
    ) -> dict[str, Any]:
        route = STATIC_ROUTES.get(destination_id)
        if not route:
            return {
                "provider": "static",
                "fallback": True,
                "mode": mode,
                "orderedSpots": [self._spot_to_dict(spot) for spot in spots],
                "totalDistance": "待更新",
                "totalDuration": "待更新",
                "segments": [],
                "notices": [f"高德路线规划失败：{reason}"],
            }
        ordered_ids = self._spot_names_in_static_route(route, spots)
        return {
            "provider": "static",
            "fallback": True,
            "mode": mode,
            "orderedSpots": [self._spot_to_dict(spot) for spot in spots if spot.name in ordered_ids] or [self._spot_to_dict(spot) for spot in spots],
            "totalDistance": route["totalDistance"],
            "totalDuration": route["totalDuration"],
            "segments": route["legs"],
            "navUrl": route["navUrl"],
            "description": route["description"],
            "notices": [f"高德路线规划暂时不可用，已使用备用路线：{reason}"],
        }

    @staticmethod
    def _spot_names_in_static_route(route: dict[str, Any], spots: list[ScenicSpot]) -> set[str]:
        names: set[str] = set()
        for leg in route.get("legs", []):
            names.add(leg.get("from", ""))
            names.add(leg.get("to", ""))
        return {spot.name for spot in spots if spot.name in names}
