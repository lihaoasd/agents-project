from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class City:
    id: str
    province: str
    city: str
    tags: tuple[str, ...]
    summary: str
    cultural_focus: str


@dataclass(frozen=True)
class ScenicSpot:
    id: str
    city_id: str
    name: str
    address: str
    category: str
    tags: tuple[str, ...]
    reason: str
    image_alt: str


CITIES: list[City] = [
    City("xian", "陕西省", "西安市", ("历史", "唐代", "博物馆", "亲子", "美食", "古城"), "十三朝古都，适合围绕唐代文化、博物馆和古城墙做深度游览。", "周秦汉唐文化、丝路起点、关中民俗。"),
    City("beijing", "北京市", "北京市", ("历史", "博物馆", "皇家文化", "亲子", "建筑"), "适合第一次系统了解中国古代都城、皇家建筑和国家博物馆资源。", "明清皇家文化、中轴线、国家博物馆。"),
    City("suzhou", "江苏省", "苏州市", ("园林", "水乡", "非遗", "江南", "慢旅行"), "适合体验江南园林、昆曲评弹、古镇水乡和苏式生活美学。", "江南园林、昆曲、苏绣、古镇文化。"),
    City("hangzhou", "浙江省", "杭州市", ("西湖", "宋韵", "茶文化", "自然", "博物馆"), "适合把西湖山水、宋代文化和茶文化结合起来做轻松行程。", "西湖文化、宋韵、龙井茶、运河文化。"),
    City("chengdu", "四川省", "成都市", ("亲子", "美食", "博物馆", "熊猫", "巴蜀"), "适合亲子出行，把熊猫、巴蜀文明和川味美食放在同一行程。", "巴蜀文明、三国文化、川剧、蜀锦。"),
    City("dunhuang", "甘肃省", "敦煌市", ("丝路", "壁画", "历史", "研学", "自然"), "适合丝路研学，把莫高窟、鸣沙山和边塞文化串联起来。", "丝路文明、敦煌壁画、汉唐边塞。"),
    City("guangzhou", "广东省", "广州市", ("岭南", "美食", "博物馆", "城市漫步", "非遗"), "适合岭南文化、骑楼街区和广府美食体验。", "岭南建筑、广府饮食、粤剧、海丝文化。"),
]

SPOTS: dict[str, tuple[ScenicSpot, ...]] = {
    "xian": (
        ScenicSpot("xian_terracotta", "xian", "秦始皇帝陵博物院", "陕西省西安市临潼区秦陵北路", "博物馆", ("秦文化", "世界遗产", "亲子", "历史"), "用兵马俑理解秦代制度、军事组织和古代工艺。", "秦始皇帝陵博物院兵马俑"),
        ScenicSpot("xian_museum", "xian", "陕西历史博物馆", "陕西省西安市雁塔区小寨东路91号", "博物馆", ("历史", "文物", "周秦汉唐", "研学"), "馆藏能系统展示陕西从史前到隋唐的历史脉络。", "陕西历史博物馆外观"),
        ScenicSpot("xian_citywall", "xian", "西安城墙", "陕西省西安市碑林区南门附近", "古城", ("古城", "骑行", "亲子", "城市漫步"), "适合傍晚骑行或步行，感受古城空间格局。", "西安城墙"),
        ScenicSpot("xian_datang", "xian", "大唐不夜城", "陕西省西安市雁塔区曲江新区", "街区", ("唐代", "夜游", "亲子", "表演"), "夜间文旅氛围强，适合补充唐代主题体验。", "大唐不夜城夜景"),
    ),
    "beijing": (
        ScenicSpot("beijing_forbidden_city", "beijing", "故宫博物院", "北京市东城区景山前街4号", "博物馆", ("皇家文化", "建筑", "亲子", "历史"), "通过宫殿、文物和展陈理解明清皇家制度与礼制。", "故宫博物院"),
        ScenicSpot("beijing_national_museum", "beijing", "中国国家博物馆", "北京市东城区东长安街16号", "博物馆", ("国家记忆", "历史", "研学", "免费"), "适合用半天梳理中华文明发展脉络。", "中国国家博物馆"),
        ScenicSpot("beijing_hutong", "beijing", "什刹海胡同片区", "北京市西城区什刹海一带", "街区", ("胡同", "城市漫步", "民俗", "亲子"), "适合把城市生活、胡同文化和水系景观结合起来。", "什刹海胡同"),
    ),
    "suzhou": (
        ScenicSpot("suzhou_humble", "suzhou", "拙政园", "江苏省苏州市姑苏区东北街178号", "园林", ("园林", "世界遗产", "江南", "建筑"), "苏州园林代表，适合讲解借景、叠山理水和文人审美。", "拙政园"),
        ScenicSpot("suzhou_museum", "suzhou", "苏州博物馆", "江苏省苏州市姑苏区东北街204号", "博物馆", ("博物馆", "建筑", "江南", "亲子"), "贝聿铭设计的新馆与苏州传统空间语言结合。", "苏州博物馆"),
        ScenicSpot("suzhou_pingjiang", "suzhou", "平江路历史街区", "江苏省苏州市姑苏区平江路", "街区", ("水乡", "非遗", "评弹", "城市漫步"), "适合体验水巷、评弹和苏式小店。", "平江路"),
    ),
    "hangzhou": (
        ScenicSpot("hangzhou_west_lake", "hangzhou", "西湖风景名胜区", "浙江省杭州市西湖区", "自然文化景观", ("西湖", "宋韵", "自然", "城市漫步"), "西湖是自然山水与诗词传说结合的典型文化景观。", "杭州西湖"),
        ScenicSpot("hangzhou_museum", "hangzhou", "浙江省博物馆", "浙江省杭州市西湖区孤山路25号", "博物馆", ("博物馆", "宋韵", "历史", "研学"), "适合补充浙江历史、良渚文化和宋韵艺术。", "浙江省博物馆"),
        ScenicSpot("hangzhou_longjing", "hangzhou", "龙井村", "浙江省杭州市西湖区龙井路一带", "茶文化", ("茶文化", "自然", "慢旅行", "亲子"), "适合把龙井茶文化和西湖山水放在同一天体验。", "龙井茶园"),
    ),
    "chengdu": (
        ScenicSpot("chengdu_pandas", "chengdu", "成都大熊猫繁育研究基地", "四川省成都市成华区熊猫大道1375号", "亲子自然", ("熊猫", "亲子", "自然", "科普"), "亲子友好，适合上午参观并了解大熊猫保护。", "成都大熊猫基地"),
        ScenicSpot("chengdu_jinsha", "chengdu", "金沙遗址博物馆", "四川省成都市青羊区金沙遗址路2号", "博物馆", ("巴蜀", "考古", "历史", "研学"), "用太阳神鸟和金器理解古蜀文明。", "金沙遗址博物馆"),
        ScenicSpot("chengdu_kuanzhai", "chengdu", "宽窄巷子", "四川省成都市青羊区长顺上街附近", "街区", ("美食", "城市漫步", "民俗", "亲子"), "适合体验成都街巷生活和川味小吃。", "宽窄巷子"),
    ),
    "dunhuang": (
        ScenicSpot("dunhuang_mogao", "dunhuang", "莫高窟", "甘肃省敦煌市东南25公里鸣沙山东麓", "世界遗产", ("丝路", "壁画", "佛教艺术", "研学"), "敦煌文化核心，适合讲解丝路交流和壁画艺术。", "莫高窟"),
        ScenicSpot("dunhuang_mingsha", "dunhuang", "鸣沙山月牙泉", "甘肃省敦煌市鸣山路", "自然文化景观", ("自然", "丝路", "亲子", "研学"), "把沙漠地貌和边塞想象结合，适合研学拓展。", "鸣沙山月牙泉"),
        ScenicSpot("dunhuang_yardang", "dunhuang", "敦煌雅丹国家地质公园", "甘肃省敦煌市西北戈壁区域", "自然", ("地质", "丝路", "自然", "研学"), "适合补充丝路沿线地貌与边塞景观。", "敦煌雅丹"),
    ),
    "guangzhou": (
        ScenicSpot("guangzhou_chen", "guangzhou", "陈家祠", "广东省广州市荔湾区中山七路恩龙里34号", "博物馆", ("岭南", "建筑", "非遗", "亲子"), "岭南建筑装饰和民间工艺集中展示地。", "陈家祠"),
        ScenicSpot("guangzhou_museum", "guangzhou", "南越王博物院", "广东省广州市越秀区解放北路867号", "博物馆", ("历史", "岭南", "考古", "研学"), "适合了解岭南早期历史和南越国文化。", "南越王博物院"),
        ScenicSpot("guangzhou_yongqing", "guangzhou", "永庆坊", "广东省广州市荔湾区恩宁路", "街区", ("骑楼", "非遗", "美食", "城市漫步"), "适合把西关骑楼、粤剧和广府美食串起来。", "永庆坊"),
    ),
}


class TripService:
    """本地服务层。负责候选城市、景点、详情、路线和内容推荐的规则化生成。"""

    def get_cities(self, query: str | None = None) -> list[dict[str, Any]]:
        normalized = self._normalize(query or "")
        if not normalized:
            return [self._city_to_dict(city) for city in CITIES]

        matched = []
        for city in CITIES:
            haystack = " ".join([city.province, city.city, *city.tags, city.summary, city.cultural_focus])
            if normalized in self._normalize(haystack):
                matched.append(city)
        return [self._city_to_dict(city) for city in matched] or [self._city_to_dict(CITIES[0])]

    def select_cities(self, requirement: str, interests: list[str] | tuple[str, ...] | None, days: int, budget: str) -> list[dict[str, Any]]:
        text = self._normalize(" ".join([requirement, *(interests or []), budget]))
        ranked: list[tuple[int, City]] = []

        for city in CITIES:
            score = 0
            for tag in city.tags:
                if self._normalize(tag) in text:
                    score += 3
            for keyword in city.cultural_focus.split("、"):
                if self._normalize(keyword) in text:
                    score += 2
            if city.id == "xian" and any(word in text for word in ("唐", "秦", "兵马俑", "长安", "关中")):
                score += 6
            if city.id == "dunhuang" and any(word in text for word in ("敦煌", "丝路", "壁画", "莫高窟")):
                score += 6
            if city.id == "suzhou" and any(word in text for word in ("园林", "江南", "水乡", "昆曲")):
                score += 5
            if city.id == "chengdu" and any(word in text for word in ("熊猫", "巴蜀", "川菜", "成都")):
                score += 5
            if city.id == "beijing" and any(word in text for word in ("故宫", "皇家", "北京", "博物馆")):
                score += 4
            if city.id == "hangzhou" and any(word in text for word in ("西湖", "宋韵", "茶", "杭州")):
                score += 4
            if city.id == "guangzhou" and any(word in text for word in ("岭南", "广府", "广州", "骑楼")):
                score += 4
            if score:
                ranked.append((score, city))

        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = [city for _, city in ranked[: 2 if days >= 3 else 1]]
        if not selected:
            selected = [CITIES[0]]
        return [self._city_to_dict(city) for city in selected]

    def get_scenic_spots(self, city_id: str | None = None, query: str | None = None, limit: int = 6) -> list[dict[str, Any]]:
        city_id = city_id or "xian"
        spots = list(SPOTS.get(city_id, SPOTS["xian"]))
        normalized = self._normalize(query or "")

        if normalized:
            scored = []
            for spot in spots:
                haystack = " ".join([spot.name, spot.category, *spot.tags, spot.reason])
                score = 1 if normalized in self._normalize(haystack) else 0
                scored.append((score, spot))
            spots = [spot for _, spot in sorted(scored, key=lambda item: item[0], reverse=True)]

        return [self._spot_to_dict(spot) for spot in spots[:limit]]

    def get_spot_detail(self, spot_id: str) -> dict[str, Any] | None:
        spot = self._find_spot(spot_id)
        if not spot:
            return None
        return {
            "id": spot.id,
            "name": spot.name,
            "category": spot.category,
            "address": spot.address,
            "tags": list(spot.tags),
            "basic_info": self._basic_info(spot),
            "cultural_intro": self._cultural_intro(spot),
            "visit_tips": self._visit_tips(spot),
            "image_alt": spot.image_alt,
            "source": "local_rule_template",
        }

    def build_route(self, spot_ids: list[str], city_id: str | None = None, days: int = 2) -> dict[str, Any]:
        city_id = city_id or "xian"
        city = next((item for item in CITIES if item.id == city_id), CITIES[0])
        spots = [spot for spot in (self._find_spot(spot_id) for spot_id in spot_ids) if spot]

        if not spots:
            return {"city": city.city, "summary": "暂无可规划路线，请重新选择景点。", "steps": [], "source": "local_rule_template"}

        day_count = max(1, min(days, 5))
        steps = []
        for index, spot in enumerate(spots, start=1):
            day_label = f"第{(index - 1) % day_count + 1}天"
            steps.append(f"{day_label}：前往{spot.name}，重点了解{spot.category}与{self._first_tag(spot)}。")

        return {
            "city": city.city,
            "summary": f"建议以{city.city}为中心，按区域和开放时间串联{len(spots)}个点位。",
            "steps": steps,
            "amap_notice": "当前未启用高德地图 API；已返回文本路线。配置 AMAP_KEY 并开启 ENABLE_AMAP 后可接入真实路线规划。",
            "source": "local_rule_template",
        }

    def get_recommendations(self, requirement: str, city_id: str | None = None, spot_ids: list[str] | None = None) -> dict[str, list[dict[str, str]]]:
        text = self._normalize(" ".join([requirement, city_id or ""]))
        books = [
            {"type": "book", "title": "《中国国家地理：中国古镇》", "reason": "适合补充目的地自然与人文背景。"},
            {"type": "book", "title": "《博物馆里的中国历史》", "reason": "适合亲子或研学前做知识预热。"},
        ]
        videos = [
            {"type": "video", "title": "《国家宝藏》相关集数", "reason": "用文物故事帮助理解目的地文化。"},
            {"type": "video", "title": "央视纪录片《航拍中国》对应省市集", "reason": "出发前快速建立地理和景观印象。"},
        ]
        articles = [
            {"type": "article", "title": "目的地博物馆官方参观指南", "reason": "核对预约、开放时间和交通信息。"},
            {"type": "article", "title": "当地文旅局发布的非遗与节庆活动", "reason": "补充在地文化体验。"},
        ]

        if any(word in text for word in ("唐", "秦", "xian", "西安", "长安")):
            books.insert(0, {"type": "book", "title": "《唐朝穿越指南》", "reason": "用轻松方式理解唐代生活与礼仪。"})
            videos.insert(0, {"type": "video", "title": "《大明宫》相关纪录片", "reason": "帮助理解唐代都城与宫廷文化。"})
        if any(word in text for word in ("园林", "江南", "suzhou", "苏州")):
            books.insert(0, {"type": "book", "title": "《苏州园林》", "reason": "补充园林审美、造园手法和江南生活。"})
        if any(word in text for word in ("熊猫", "巴蜀", "chengdu", "成都")):
            books.insert(0, {"type": "book", "title": "《古蜀王国》", "reason": "帮助理解三星堆、金沙和巴蜀文明。"})
        if any(word in text for word in ("敦煌", "丝路", "dunhuang")):
            books.insert(0, {"type": "book", "title": "《敦煌石窟艺术》", "reason": "适合出发前了解壁画、彩塑和丝路交流。"})
            videos.insert(0, {"type": "video", "title": "《敦煌》纪录片", "reason": "用影像建立莫高窟和丝路背景。"})

        return {"books": books[:4], "videos": videos[:4], "articles": articles[:4]}

    def _city_to_dict(self, city: City) -> dict[str, Any]:
        return {
            "id": city.id,
            "province": city.province,
            "city": city.city,
            "tags": list(city.tags),
            "summary": city.summary,
            "cultural_focus": city.cultural_focus,
        }

    def _spot_to_dict(self, spot: ScenicSpot) -> dict[str, Any]:
        return {
            "id": spot.id,
            "city_id": spot.city_id,
            "name": spot.name,
            "address": spot.address,
            "category": spot.category,
            "tags": list(spot.tags),
            "reason": spot.reason,
            "image_alt": spot.image_alt,
        }

    def _find_spot(self, spot_id: str) -> ScenicSpot | None:
        for spots in SPOTS.values():
            for spot in spots:
                if spot.id == spot_id:
                    return spot
        return None

    def _basic_info(self, spot: ScenicSpot) -> str:
        return f"{spot.name}位于{spot.address}，属于{spot.category}类目的地。推荐停留约2小时，适合结合{self._first_tag(spot)}主题进行讲解。"

    def _cultural_intro(self, spot: ScenicSpot) -> str:
        city = next((item for item in CITIES if item.id == spot.city_id), None)
        focus = city.cultural_focus if city else "当地历史文化"
        return f"{spot.name}可以放在“{focus}”的线索中理解。参观时建议关注建筑、文物、展陈或街巷空间背后的生活方式，而不是只看打卡照片。{spot.reason}"

    def _visit_tips(self, spot: ScenicSpot) -> list[str]:
        return [
            "提前查看官方预约、开放时间和闭馆日。",
            "博物馆类景点建议预留讲解或语音导览时间。",
            "节假日人流较大，尽量错峰出行。",
            "文化场所请遵守拍照、饮食和安静参观规则。",
        ]

    def _first_tag(self, spot: ScenicSpot) -> str:
        return spot.tags[0] if spot.tags else "文化"

    def _normalize(self, text: str) -> str:
        return "".join(str(text).lower().split())
