"""行程规划业务服务。"""

from __future__ import annotations

from dataclasses import dataclass

from agent import AgentError
from logging_config import get_logger

from trip_plan.agent.models import (
    CulturalInterpretation,
    CulturalInterpretationsResult,
    PlaceRecommendation,
    PlaceRecommendationResult,
    ScenicSpot,
    ScenicSpotsResult,
)
from trip_plan.agent.cultural_interpretation_agent import CulturalInterpretationAgent
from trip_plan.agent.place_recommendation_agent import PlaceRecommendationAgent
from trip_plan.agent.scenic_spot_agent import ScenicSpotAgent
from trip_plan.service.unsplash_image_service import UnsplashImageService

FALLBACK_DESTINATIONS = [
    PlaceRecommendation(
        id="xian",
        province="陕西省",
        city="西安市",
        matchScore=96,
        tags=["唐代文化", "博物馆", "历史遗址", "美食"],
        reasons=[
            "适合围绕周秦汉唐文化展开研学旅行。",
            "博物馆和历史遗址密集，适合亲子或深度文化游。",
            "城市交通便利，可串联城墙、博物院和遗址公园。",
        ],
        intro="西安是十三朝古都，唐代文化、城墙格局、陵墓遗址和博物馆资源都非常丰富，适合作为历史文化旅行的核心目的地。",
    ),
    PlaceRecommendation(
        id="hangzhou",
        province="浙江省",
        city="杭州市",
        matchScore=88,
        tags=["宋韵文化", "西湖", "茶文化", "运河"],
        reasons=[
            "适合体验西湖景观、宋韵审美和江南城市生活。",
            "茶文化、运河文化和博物馆资源容易形成轻松的文化路线。",
            "适合预算中等、节奏舒缓的文化旅行。",
        ],
        intro="杭州以西湖、宋韵文化、茶文化和运河文化见长，适合把自然景观和城市人文结合起来。",
    ),
    PlaceRecommendation(
        id="beijing",
        province="北京市",
        city="北京市",
        matchScore=86,
        tags=["皇家文化", "故宫", "长城", "中轴线"],
        reasons=[
            "适合了解皇家建筑、宫廷文化和北京中轴线。",
            "故宫、天坛、长城等资源知名度高，适合首次文化旅行。",
            "博物馆和历史文化街区丰富，适合多日深度游览。",
        ],
        intro="北京拥有故宫、天坛、长城、胡同和中轴线等代表性文化资源，适合皇家文化和古都城市主题旅行。",
    ),
]


@dataclass
class PlaceRecommendationServiceResult:
    """地方推荐服务结果。"""

    result: PlaceRecommendationResult
    provider: str
    model: str
    fallback: bool = False


@dataclass
class ScenicSpotsServiceResult:
    """景点推荐服务结果。"""

    result: ScenicSpotsResult
    provider: str
    model: str
    fallback: bool = False


@dataclass
class CulturalInterpretationsServiceResult:
    """综合文化解读服务结果。"""

    result: CulturalInterpretationsResult
    provider: str
    model: str
    fallback: bool = False


_FALLBACK_SPOTS: dict[str, list[ScenicSpot]] = {
    "xian": [
        ScenicSpot(id="xian-terracotta", name="秦始皇帝陵博物院", address="陕西省西安市临潼区", type="遗址博物馆", recommendReason="以秦代军事、雕塑和陵寝文化为核心，是理解秦文化的代表景点。", visitTime="建议 3-4 小时", ticket="旺季约 120 元，淡季约 120 元，以官方公布为准", openingHours="08:30-18:00，节假日可能调整", cultureTags=["秦文化", "世界遗产", "考古"], imageAlt="秦始皇帝陵博物院", imageUrl=""),
        ScenicSpot(id="xian-museum", name="陕西历史博物馆", address="陕西省西安市雁塔区小寨东路", type="综合博物馆", recommendReason="馆藏丰富，适合系统了解陕西从史前到唐代的历史脉络。", visitTime="建议 2-3 小时", ticket="基础馆常设展通常免费预约，特展以官方为准", openingHours="周二至周日开放，周一闭馆", cultureTags=["周秦汉唐", "青铜器", "唐代文物"], imageAlt="陕西历史博物馆", imageUrl=""),
        ScenicSpot(id="xian-city-wall", name="西安城墙", address="陕西省西安市碑林区", type="古城防御遗址", recommendReason="可体验古代城防体系和城市空间格局，适合傍晚游览。", visitTime="建议 1.5-2 小时", ticket="约 54 元，以官方公布为准", openingHours="08:00-22:00，季节可能调整", cultureTags=["城防", "古都格局", "城市漫步"], imageAlt="西安城墙", imageUrl=""),
    ],
    "hangzhou": [
        ScenicSpot(id="hangzhou-west-lake", name="西湖风景名胜区", address="浙江省杭州市西湖区", type="文化景观", recommendReason="适合体验湖山景观、诗词文化和宋韵审美。", visitTime="建议半日", ticket="核心景区免费，部分景点另收费", openingHours="全天开放", cultureTags=["西湖文化", "诗词", "园林"], imageAlt="西湖风景名胜区", imageUrl=""),
        ScenicSpot(id="hangzhou-museum", name="浙江省博物馆之江馆区", address="浙江省杭州市西湖区之江文化中心", type="综合博物馆", recommendReason="适合了解浙江地域文明、良渚文化和江南艺术。", visitTime="建议 2 小时", ticket="通常需预约，以官方公布为准", openingHours="周二至周日开放，周一闭馆", cultureTags=["良渚文化", "江南艺术", "地域文明"], imageAlt="浙江省博物馆", imageUrl=""),
        ScenicSpot(id="hangzhou-grand-canal", name="京杭大运河杭州段", address="浙江省杭州市拱墅区", type="运河文化街区", recommendReason="适合了解运河商贸、桥巷空间和城市生活。", visitTime="建议 2-3 小时", ticket="街区免费，部分场馆另收费", openingHours="街区全天开放，场馆以官方为准", cultureTags=["运河文化", "市井生活", "商贸历史"], imageAlt="京杭大运河杭州段", imageUrl=""),
    ],
    "beijing": [
        ScenicSpot(id="beijing-palace-museum", name="故宫博物院", address="北京市东城区景山前街4号", type="皇家宫殿博物馆", recommendReason="皇家建筑、宫廷文化和明清历史的核心代表。", visitTime="建议 3-5 小时", ticket="旺季约 60 元，淡季约 40 元，以官方公布为准", openingHours="周二至周日开放，周一闭馆，节假日以官方为准", cultureTags=["皇家文化", "明清历史", "古建筑"], imageAlt="故宫博物院", imageUrl=""),
        ScenicSpot(id="beijing-temple-heaven", name="天坛公园", address="北京市东城区天坛内东里7号", type="礼制建筑", recommendReason="适合了解古代祭天礼制、建筑象征和皇家礼仪。", visitTime="建议 2 小时", ticket="联票约 28 元，以官方公布为准", openingHours="公园和景点开放时间不同，以官方为准", cultureTags=["礼制文化", "古建筑", "皇家礼仪"], imageAlt="天坛公园", imageUrl=""),
        ScenicSpot(id="beijing-hutong", name="什刹海胡同片区", address="北京市西城区什刹海地区", type="历史街区", recommendReason="适合体验老北京胡同、市井生活和传统街区空间。", visitTime="建议 2-3 小时", ticket="街区免费，部分体验项目另收费", openingHours="街区全天开放", cultureTags=["胡同文化", "市井生活", "老北京"], imageAlt="什刹海胡同片区", imageUrl=""),
    ],
}

_FALLBACK_DESTINATION_CULTURE = {
    "xian": {
        "historyCulture": "西安长期是中国古代政治和文化中心，周、秦、汉、唐等历史阶段在这里留下丰富遗存，适合通过博物馆、城墙和遗址理解古都脉络。",
        "customs": "关中面食、城墙生活、回民街饮食和博物馆研学，都是理解西安日常文化的重要入口。",
        "geography": "西安位于关中平原，南依秦岭，北临渭河，平原与山河屏障共同影响了古都选址和城市发展。",
        "foodSuggestion": "可结合肉夹馍、羊肉泡馍或回民街小吃理解关中饮食文化。",
    },
    "hangzhou": {
        "historyCulture": "杭州以西湖、宋韵文化、茶文化和运河文化见长，适合把自然景观、城市生活和江南审美结合起来理解。",
        "customs": "茶文化、湖山游赏、运河街区和江南市井生活，是杭州文化体验中很有代表性的部分。",
        "geography": "杭州处在江南水网与钱塘江流域交汇处，西湖和运河共同塑造了城市景观与生活方式。",
        "foodSuggestion": "可结合龙井茶、片儿川、南宋御街小吃体验江南饮食与城市生活。",
    },
    "beijing": {
        "historyCulture": "北京拥有故宫、天坛、长城、胡同和中轴线等代表性文化资源，适合理解皇家文化、礼制建筑和古都城市格局。",
        "customs": "胡同生活、老字号小吃、京剧和节令民俗，能帮助游客从日常层面理解北京。",
        "geography": "北京位于华北平原北端，背靠燕山，面向平原，城市轴线、水系和交通区位影响了都城格局。",
        "foodSuggestion": "可结合烤鸭、卤煮、豆汁或胡同小吃体验北京饮食文化。",
    },
    "nanjing": {
        "historyCulture": "南京兼具六朝、明代和民国文化记忆，适合通过博物馆、城墙和近代建筑理解城市历史。",
        "customs": "秦淮风物、江南饮食、街巷生活和博物馆参观，是理解南京文化层次的重要方式。",
        "geography": "南京依江而建，紫金山、玄武湖和长江共同构成山水城林格局，也影响了城市防御与空间发展。",
        "foodSuggestion": "可结合盐水鸭、鸭血粉丝汤和夫子庙小吃体验南京地方风味。",
    },
    "chengdu": {
        "historyCulture": "成都适合围绕蜀文化、川菜、茶馆文化和周边古镇展开，城市气质兼具历史厚度与生活休闲。",
        "customs": "茶馆、川菜、川剧和街巷生活体现了成都重视日常体验和城市慢生活的文化特点。",
        "geography": "成都位于四川盆地西部，平原肥沃、水系发达，为蜀地农业、城市发展和休闲生活提供了基础。",
        "foodSuggestion": "可结合担担面、钟水饺、茶馆和川菜体验成都生活文化。",
    },
    "dunhuang": {
        "historyCulture": "敦煌以莫高窟、丝路文化和沙漠地貌闻名，是理解佛教艺术、丝路交流和边塞历史的重要目的地。",
        "customs": "敦煌文化体验常与石窟参观、丝路故事、地方小吃和沙漠旅行记忆结合。",
        "geography": "敦煌位于河西走廊西端，周边沙漠、绿洲和戈壁共同塑造了丝路交通与边塞文化。",
        "foodSuggestion": "可结合驴肉黄面、胡羊焖饼或夜市小吃体验西北边塞风味。",
    },
}


logger = get_logger("trip_plan.service")


class TripPlanService:
    """行程规划统一服务入口。"""

    def __init__(
        self,
        place_agent: PlaceRecommendationAgent | None = None,
        spot_agent: ScenicSpotAgent | None = None,
        culture_agent: CulturalInterpretationAgent | None = None,
        image_service: UnsplashImageService | None = None,
    ) -> None:
        self._place_agent = place_agent or PlaceRecommendationAgent()
        self._spot_agent = spot_agent or ScenicSpotAgent()
        self._culture_agent = culture_agent or CulturalInterpretationAgent()
        self._image_service = image_service or UnsplashImageService()

    def recommend_places(self, requirement: str) -> PlaceRecommendationServiceResult:
        """根据用户一句话生成地方推荐。"""

        requirement = requirement.strip()
        if not requirement:
            logger.warning("地方推荐请求缺少 requirement")
            raise ValueError("requirement 不能为空")

        logger.info("开始生成地方推荐 requirement_length=%s", len(requirement))

        try:
            agent_result = self._place_agent.run(requirement)
            destinations = self._normalize_destinations(agent_result.result.destinations)
            if not destinations:
                logger.warning("地方推荐 Agent 返回空结果，启用静态兜底")
                return self._fallback_result(agent_result.result.notice)
            logger.info(
                "地方推荐完成 count=%s provider=%s model=%s",
                len(destinations),
                agent_result.provider,
                agent_result.model,
            )
            return PlaceRecommendationServiceResult(
                result=PlaceRecommendationResult(
                    destinations=destinations,
                    notice=agent_result.result.notice,
                ),
                provider=agent_result.provider,
                model=agent_result.model,
            )
        except AgentError as exc:
            logger.warning("地方推荐 Agent 调用失败，启用静态兜底: %s", exc)
            return self._fallback_result("智能推荐暂时不可用，已为你展示通用文化旅行推荐。")

    def _normalize_destinations(
        self,
        destinations: list[PlaceRecommendation],
    ) -> list[PlaceRecommendation]:
        normalized: list[PlaceRecommendation] = []
        seen_ids: set[str] = set()
        for destination in destinations[:10]:
            dest_id = destination.id.strip().lower()
            if not dest_id:
                continue
            if dest_id in seen_ids:
                continue
            seen_ids.add(dest_id)
            normalized.append(
                PlaceRecommendation(
                    id=dest_id,
                    province=destination.province.strip(),
                    city=destination.city.strip(),
                    matchScore=max(0, min(100, destination.matchScore)),
                    tags=destination.tags or ["文化旅行"],
                    reasons=destination.reasons or ["适合文化旅行体验。"],
                    intro=destination.intro.strip(),
                )
            )
        return normalized

    def _fallback_result(self, notice: str) -> PlaceRecommendationServiceResult:
        logger.info("地方推荐静态兜底 count=%s", len(FALLBACK_DESTINATIONS))
        return PlaceRecommendationServiceResult(
            result=PlaceRecommendationResult(
                destinations=FALLBACK_DESTINATIONS,
                notice=notice,
            ),
            provider="fallback",
            model="static",
            fallback=True,
        )

    def recommend_scenic_spots(
        self,
        requirement: str,
        destination_id: str,
        destination_city: str,
        destination_province: str,
    ) -> ScenicSpotsServiceResult:
        """根据用户需求和选定目的地推荐旅游景点。"""

        if not requirement:
            logger.warning("景点推荐请求缺少 requirement")
            raise ValueError("requirement 不能为空")
        if not destination_id:
            logger.warning("景点推荐请求缺少 destination_id")
            raise ValueError("destination_id 不能为空")

        logger.info(
            "开始生成景点推荐 destination=%s city=%s",
            destination_id,
            destination_city,
        )

        user_content = (
            f"用户文化旅行需求：{requirement}\n"
            f"选定目的地：{destination_province} · {destination_city}\n"
            f"目的地ID：{destination_id}\n"
            f"请为该目的地推荐 3-5 个文化旅行景点。"
        )

        try:
            agent_result = self._spot_agent.run(user_content)
            spots = self._normalize_spots(agent_result.result.spots)
            spots = self._enrich_spot_images(spots, destination_city, destination_province)
            if not spots:
                logger.warning("景点推荐 Agent 返回空结果，启用静态兜底")
                return self._fallback_spots_result(
                    destination_id,
                    agent_result.result.notice,
                )
            logger.info(
                "景点推荐完成 count=%s provider=%s model=%s",
                len(spots),
                agent_result.provider,
                agent_result.model,
            )
            return ScenicSpotsServiceResult(
                result=ScenicSpotsResult(
                    spots=spots,
                    notice=agent_result.result.notice,
                ),
                provider=agent_result.provider,
                model=agent_result.model,
            )
        except AgentError as exc:
            logger.warning("景点推荐 Agent 调用失败，启用静态兜底: %s", exc)
            return self._fallback_spots_result(
                destination_id,
                "智能推荐暂时不可用，已为你展示通用景点推荐。",
            )

    def recommend_cultural_interpretations(
        self,
        requirement: str,
        destination_id: str,
        destination_city: str,
        destination_province: str,
        spots: list[ScenicSpot],
    ) -> CulturalInterpretationsServiceResult:
        """根据用户需求和已选景点生成综合文化解读。"""

        if not requirement:
            logger.warning("文化解读请求缺少 requirement")
            raise ValueError("requirement 不能为空")
        if not destination_id:
            logger.warning("文化解读请求缺少 destination_id")
            raise ValueError("destination_id 不能为空")
        if not spots:
            logger.warning("文化解读请求缺少 spots")
            raise ValueError("spots 不能为空")

        spots_text = "\n".join(
            f"- {spot.id}：{spot.name}，类型：{spot.type}，标签：{', '.join(spot.cultureTags)}"
            for spot in spots
        )
        user_content = (
            f"用户文化旅行需求：{requirement}\n"
            f"选定目的地：{destination_province} · {destination_city}\n"
            f"目的地ID：{destination_id}\n"
            f"已推荐景点：\n{spots_text}\n"
            f"请为每个景点生成包含历史文化、风俗习惯、地理特点的综合文化解读。"
        )

        try:
            agent_result = self._culture_agent.run(user_content)
            cultures = self._normalize_cultural_interpretations(
                agent_result.result.cultures,
                spots,
            )
            if not cultures:
                logger.warning("文化解读 Agent 返回空结果，启用静态兜底")
                return self._fallback_cultural_interpretations_result(
                    destination_id,
                    spots,
                    agent_result.result.notice,
                )
            logger.info(
                "文化解读完成 count=%s provider=%s model=%s",
                len(cultures),
                agent_result.provider,
                agent_result.model,
            )
            return CulturalInterpretationsServiceResult(
                result=CulturalInterpretationsResult(
                    cultures=cultures,
                    notice=agent_result.result.notice,
                ),
                provider=agent_result.provider,
                model=agent_result.model,
            )
        except AgentError as exc:
            logger.warning("文化解读 Agent 调用失败，启用静态兜底: %s", exc)
            return self._fallback_cultural_interpretations_result(
                destination_id,
                spots,
                "智能文化解读暂时不可用，已为你展示通用文化解读。",
            )

    @staticmethod
    def _normalize_cultural_interpretations(
        cultures: list[CulturalInterpretation],
        spots: list[ScenicSpot],
    ) -> list[CulturalInterpretation]:
        spot_map = {spot.id.lower(): spot for spot in spots}
        normalized: list[CulturalInterpretation] = []
        seen_ids: set[str] = set()
        for culture in cultures[: len(spots)]:
            spot_id = culture.spotId.strip().lower()
            if not spot_id or spot_id in seen_ids or spot_id not in spot_map:
                continue
            seen_ids.add(spot_id)
            spot = spot_map[spot_id]
            normalized.append(
                CulturalInterpretation(
                    spotId=spot_id,
                    spotName=culture.spotName.strip() or spot.name.strip(),
                    overview=culture.overview.strip() or "该景点适合从历史文化、风俗习惯和地理环境三个角度理解。",
                    historyCulture=culture.historyCulture.strip() or "该景点体现了当地历史文化的延续，可从建筑、遗存、文物或城市记忆中理解其价值。",
                    customs=culture.customs.strip() or "它也能帮助游客理解当地生活方式、市井文化和传统体验。",
                    geography=culture.geography.strip() or "其形成和发展与当地地理环境、城市格局或交通区位密切相关。",
                    foodSuggestion=culture.foodSuggestion.strip(),
                    tags=culture.tags or spot.cultureTags or ["文化旅行"],
                )
            )
        return normalized

    @staticmethod
    def _normalize_spots(spots: list[ScenicSpot]) -> list[ScenicSpot]:
        normalized: list[ScenicSpot] = []
        seen_ids: set[str] = set()
        for spot in spots[:5]:
            spot_id = spot.id.strip().lower()
            if not spot_id or spot_id in seen_ids:
                continue
            seen_ids.add(spot_id)
            normalized.append(
                ScenicSpot(
                    id=spot_id,
                    name=spot.name.strip(),
                    address=spot.address.strip(),
                    type=spot.type.strip() or "文化景点",
                    recommendReason=spot.recommendReason.strip(),
                    visitTime=spot.visitTime.strip() or "建议 2 小时",
                    ticket=spot.ticket.strip() or "以官方公布为准",
                    openingHours=spot.openingHours.strip() or "以官方为准",
                    cultureTags=spot.cultureTags or ["文化旅行"],
                    imageAlt=spot.imageAlt.strip() or spot.name.strip(),
                    imageUrl=spot.imageUrl.strip(),
                    imageSearchQuery=spot.imageSearchQuery.strip(),
                )
            )
        return normalized

    def _enrich_spot_images(
        self,
        spots: list[ScenicSpot],
        destination_city: str,
        destination_province: str,
    ) -> list[ScenicSpot]:
        for spot in spots:
            if spot.imageUrl:
                continue
            image = self._image_service.search_for_spot(
                spot.name,
                destination_city,
                destination_province,
                spot.type,
                preferred_query=spot.imageSearchQuery,
            )
            if image:
                spot.imageUrl = image.url
                spot.imageAlt = image.alt or spot.imageAlt or spot.name
        return spots

    def _fallback_spots_result(
        self,
        destination_id: str,
        notice: str,
    ) -> ScenicSpotsServiceResult:
        spots = self._enrich_spot_images(self._load_static_spots(destination_id), "", "")
        logger.info("景点推荐静态兜底 count=%s", len(spots))
        return ScenicSpotsServiceResult(
            result=ScenicSpotsResult(
                spots=spots,
                notice=notice,
            ),
            provider="fallback",
            model="static",
            fallback=True,
        )

    def _fallback_cultural_interpretations_result(
        self,
        destination_id: str,
        spots: list[ScenicSpot],
        notice: str,
    ) -> CulturalInterpretationsServiceResult:
        cultures = self._build_fallback_cultures(destination_id, spots)
        logger.info("文化解读静态兜底 count=%s", len(cultures))
        return CulturalInterpretationsServiceResult(
            result=CulturalInterpretationsResult(
                cultures=cultures,
                notice=notice,
            ),
            provider="fallback",
            model="static",
            fallback=True,
        )

    @staticmethod
    def _build_fallback_cultures(
        destination_id: str,
        spots: list[ScenicSpot],
    ) -> list[CulturalInterpretation]:
        culture = _FALLBACK_DESTINATION_CULTURE.get(destination_id, {})
        history_culture = culture.get(
            "historyCulture",
            "该目的地保留了丰富的地域文化记忆，适合通过景点、博物馆和城市空间理解当地历史。",
        )
        customs = culture.get(
            "customs",
            "当地风俗习惯和生活方式往往体现在饮食、街巷、节庆和日常体验中。",
        )
        geography = culture.get(
            "geography",
            "当地地理环境、水系、地形和交通区位共同影响了城市发展和文化形成。",
        )
        food_suggestion = culture.get("foodSuggestion", "")
        return [
            CulturalInterpretation(
                spotId=spot.id,
                spotName=spot.name,
                overview=spot.recommendReason,
                historyCulture=history_culture,
                customs=customs,
                geography=geography,
                foodSuggestion=food_suggestion,
                tags=spot.cultureTags or ["文化旅行"],
            )
            for spot in spots
        ]

    @staticmethod
    def _load_static_spots(destination_id: str) -> list[ScenicSpot]:
        return _FALLBACK_SPOTS.get(destination_id, [])
