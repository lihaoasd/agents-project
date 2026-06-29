export const progressSteps = [
  { key: 'city', label: '地方推荐' },
  { key: 'spots', label: '旅游景点生成' },
  { key: 'culture', label: '综合文化解读' },
  { key: 'route', label: '地图路线规划' },
]

export const destinationData = [
  {
    id: 'xian',
    province: '陕西省',
    city: '西安市',
    matchScore: 96,
    tags: ['唐代文化', '博物馆', '历史遗址', '美食'],
    reasons: [
      '适合围绕周秦汉唐文化展开研学旅行。',
      '博物馆和历史遗址密集，适合亲子或深度文化游。',
      '城市交通便利，可串联城墙、博物院和遗址公园。',
    ],
    intro: '西安是十三朝古都，唐代文化、城墙格局、陵墓遗址和博物馆资源都非常丰富，适合作为历史文化旅行的核心目的地。',
  },
  {
    id: 'hangzhou',
    province: '浙江省',
    city: '杭州市',
    matchScore: 88,
    tags: ['宋韵文化', '西湖', '茶文化', '运河'],
    reasons: [
      '适合体验西湖景观、宋韵审美和江南城市生活。',
      '茶文化、运河文化和博物馆资源容易形成轻松的文化路线。',
      '适合预算中等、节奏舒缓的文化旅行。',
    ],
    intro: '杭州以西湖、宋韵文化、茶文化和运河文化见长，适合把自然景观和城市人文结合起来。',
  },
  {
    id: 'beijing',
    province: '北京市',
    city: '北京市',
    matchScore: 86,
    tags: ['皇家文化', '故宫', '长城', '中轴线'],
    reasons: [
      '适合了解皇家建筑、宫廷文化和北京中轴线。',
      '故宫、天坛、长城等资源知名度高，适合首次文化旅行。',
      '博物馆和历史文化街区丰富，适合多日深度游览。',
    ],
    intro: '北京拥有故宫、天坛、长城、胡同和中轴线等代表性文化资源，适合皇家文化和古都城市主题旅行。',
  },
  {
    id: 'nanjing',
    province: '江苏省',
    city: '南京市',
    matchScore: 82,
    tags: ['六朝文化', '明文化', '民国建筑', '博物馆'],
    reasons: [
      '适合围绕六朝文化、明城墙和民国建筑展开。',
      '南京博物院等场馆适合系统了解区域历史。',
      '城市节奏适中，适合历史文化爱好者。',
    ],
    intro: '南京兼具六朝、明代和民国文化记忆，适合通过博物馆、城墙和近代建筑理解城市历史。',
  },
  {
    id: 'chengdu',
    province: '四川省',
    city: '成都市',
    matchScore: 79,
    tags: ['蜀文化', '川菜', '茶馆', '古镇'],
    reasons: [
      '适合把蜀文化、川菜体验和城市慢生活结合起来。',
      '周边古镇和博物馆资源丰富。',
      '适合亲子、美食和文化休闲结合的旅行。',
    ],
    intro: '成都适合围绕蜀文化、川菜、茶馆文化和周边古镇展开，旅行节奏相对轻松。',
  },
  {
    id: 'dunhuang',
    province: '甘肃省',
    city: '敦煌市',
    matchScore: 76,
    tags: ['丝路文化', '石窟艺术', '边塞历史', '沙漠'],
    reasons: [
      '适合围绕莫高窟、丝路艺术和边塞历史展开。',
      '文化主题非常鲜明，适合深度研学。',
      '自然地貌和文化遗产结合度高。',
    ],
    intro: '敦煌以莫高窟、丝路文化和沙漠地貌闻名，适合主题鲜明、偏深度讲解的文化旅行。',
  },
]

export const spotData = {
  xian: [
    {
      id: 'xian-terracotta',
      name: '秦始皇帝陵博物院',
      address: '陕西省西安市临潼区',
      type: '遗址博物馆',
      recommendReason: '以秦代军事、雕塑和陵寝文化为核心，是理解秦文化的代表景点。',
      visitTime: '建议 3-4 小时',
      ticket: '旺季约 120 元，淡季约 120 元，以官方公布为准',
      openingHours: '08:30-18:00，节假日可能调整',
      cultureTags: ['秦文化', '世界遗产', '考古'],
      imageAlt: '秦始皇帝陵博物院',
    },
    {
      id: 'xian-museum',
      name: '陕西历史博物馆',
      address: '陕西省西安市雁塔区小寨东路',
      type: '综合博物馆',
      recommendReason: '馆藏丰富，适合系统了解陕西从史前到唐代的历史脉络。',
      visitTime: '建议 2-3 小时',
      ticket: '基础馆常设展通常免费预约，特展以官方为准',
      openingHours: '周二至周日开放，周一闭馆',
      cultureTags: ['周秦汉唐', '青铜器', '唐代文物'],
      imageAlt: '陕西历史博物馆',
    },
    {
      id: 'xian-city-wall',
      name: '西安城墙',
      address: '陕西省西安市碑林区',
      type: '古城防御遗址',
      recommendReason: '可体验古代城防体系和城市空间格局，适合傍晚游览。',
      visitTime: '建议 1.5-2 小时',
      ticket: '约 54 元，以官方公布为准',
      openingHours: '08:00-22:00，季节可能调整',
      cultureTags: ['城防', '古都格局', '城市漫步'],
      imageAlt: '西安城墙',
    },
  ],
  hangzhou: [
    {
      id: 'hangzhou-west-lake',
      name: '西湖风景名胜区',
      address: '浙江省杭州市西湖区',
      type: '文化景观',
      recommendReason: '适合体验湖山景观、诗词文化和宋韵审美。',
      visitTime: '建议半日',
      ticket: '核心景区免费，部分景点另收费',
      openingHours: '全天开放',
      cultureTags: ['西湖文化', '诗词', '园林'],
      imageAlt: '西湖风景名胜区',
    },
    {
      id: 'hangzhou-museum',
      name: '浙江省博物馆之江馆区',
      address: '浙江省杭州市西湖区之江文化中心',
      type: '综合博物馆',
      recommendReason: '适合了解浙江地域文明、良渚文化和江南艺术。',
      visitTime: '建议 2 小时',
      ticket: '通常需预约，以官方公布为准',
      openingHours: '周二至周日开放，周一闭馆',
      cultureTags: ['良渚文化', '江南艺术', '地域文明'],
      imageAlt: '浙江省博物馆',
    },
    {
      id: 'hangzhou-grand-canal',
      name: '京杭大运河杭州段',
      address: '浙江省杭州市拱墅区',
      type: '运河文化街区',
      recommendReason: '适合了解运河商贸、桥巷空间和城市生活。',
      visitTime: '建议 2-3 小时',
      ticket: '街区免费，部分场馆另收费',
      openingHours: '街区全天开放，场馆以官方为准',
      cultureTags: ['运河文化', '市井生活', '商贸历史'],
      imageAlt: '京杭大运河杭州段',
    },
  ],
  beijing: [
    {
      id: 'beijing-palace-museum',
      name: '故宫博物院',
      address: '北京市东城区景山前街4号',
      type: '皇家宫殿博物馆',
      recommendReason: '皇家建筑、宫廷文化和明清历史的核心代表。',
      visitTime: '建议 3-5 小时',
      ticket: '旺季约 60 元，淡季约 40 元，以官方公布为准',
      openingHours: '周二至周日开放，周一闭馆，节假日以官方为准',
      cultureTags: ['皇家文化', '明清历史', '古建筑'],
      imageAlt: '故宫博物院',
    },
    {
      id: 'beijing-temple-heaven',
      name: '天坛公园',
      address: '北京市东城区天坛内东里7号',
      type: '礼制建筑',
      recommendReason: '适合了解古代祭天礼制、建筑象征和皇家礼仪。',
      visitTime: '建议 2 小时',
      ticket: '联票约 28 元，以官方公布为准',
      openingHours: '公园和景点开放时间不同，以官方为准',
      cultureTags: ['礼制文化', '古建筑', '皇家礼仪'],
      imageAlt: '天坛公园',
    },
    {
      id: 'beijing-hutong',
      name: '什刹海胡同片区',
      address: '北京市西城区什刹海地区',
      type: '历史街区',
      recommendReason: '适合体验老北京胡同、市井生活和传统街区空间。',
      visitTime: '建议 2-3 小时',
      ticket: '街区免费，部分体验项目另收费',
      openingHours: '街区全天开放',
      cultureTags: ['胡同文化', '市井生活', '老北京'],
      imageAlt: '什刹海胡同片区',
    },
  ],
  nanjing: [
    {
      id: 'nanjing-museum',
      name: '南京博物院',
      address: '江苏省南京市玄武区中山东路321号',
      type: '综合博物馆',
      recommendReason: '馆藏体系完整，适合理解江南与六朝文化。',
      visitTime: '建议 2-3 小时',
      ticket: '通常需预约，以官方公布为准',
      openingHours: '周二至周日开放，周一闭馆',
      cultureTags: ['六朝文化', '江南文明', '博物馆'],
      imageAlt: '南京博物院',
    },
    {
      id: 'nanjing-city-wall',
      name: '明城墙',
      address: '江苏省南京市玄武区解放门附近',
      type: '古城墙遗址',
      recommendReason: '适合了解明代城防、城市格局和山水城林关系。',
      visitTime: '建议 1.5 小时',
      ticket: '部分登城段收费，以官方公布为准',
      openingHours: '以景区官方公布为准',
      cultureTags: ['明文化', '城防', '城市格局'],
      imageAlt: '明城墙',
    },
    {
      id: 'nanjing-presidential-palace',
      name: '南京总统府',
      address: '江苏省南京市玄武区长江路292号',
      type: '近代历史建筑',
      recommendReason: '适合了解近代城市与民国历史文化。',
      visitTime: '建议 2 小时',
      ticket: '约 35 元，以官方公布为准',
      openingHours: '周二至周日开放，周一闭馆',
      cultureTags: ['民国建筑', '近代史', '城市记忆'],
      imageAlt: '南京总统府',
    },
  ],
  chengdu: [
    {
      id: 'chengdu-jinli',
      name: '锦里古街',
      address: '四川省成都市武侯区武侯祠大街231号',
      type: '民俗街区',
      recommendReason: '适合体验川蜀民俗、小吃和传统街巷氛围。',
      visitTime: '建议 1.5-2 小时',
      ticket: '街区免费',
      openingHours: '通常白天至夜间开放，以现场为准',
      cultureTags: ['川蜀民俗', '小吃', '街巷文化'],
      imageAlt: '锦里古街',
    },
    {
      id: 'chengdu-dufu',
      name: '杜甫草堂',
      address: '四川省成都市青羊区青华路37号',
      type: '名人纪念地',
      recommendReason: '适合了解唐代诗歌文化和成都文人记忆。',
      visitTime: '建议 1.5-2 小时',
      ticket: '约 50 元，以官方公布为准',
      openingHours: '09:00-18:00，以官方公布为准',
      cultureTags: ['唐诗', '文人文化', '园林'],
      imageAlt: '杜甫草堂',
    },
    {
      id: 'chengdu-jinsha',
      name: '金沙遗址博物馆',
      address: '四川省成都市青羊区金沙遗址路2号',
      type: '考古遗址博物馆',
      recommendReason: '适合了解古蜀文明、太阳神鸟和金器文化。',
      visitTime: '建议 2 小时',
      ticket: '约 70 元，以官方公布为准',
      openingHours: '09:00-18:00，以官方公布为准',
      cultureTags: ['古蜀文明', '考古', '金器'],
      imageAlt: '金沙遗址博物馆',
    },
  ],
  dunhuang: [
    {
      id: 'dunhuang-mogao',
      name: '莫高窟',
      address: '甘肃省敦煌市东南25公里处',
      type: '石窟寺遗址',
      recommendReason: '丝路艺术和佛教文化的代表性遗产。',
      visitTime: '建议 3-4 小时',
      ticket: '需预约，票价和开放窟以官方公布为准',
      openingHours: '旺季和淡季开放时间不同，以官方公布为准',
      cultureTags: ['丝路文化', '佛教艺术', '世界遗产'],
      imageAlt: '莫高窟',
    },
    {
      id: 'dunhuang-academy',
      name: '敦煌研究院陈列中心',
      address: '甘肃省敦煌市莫高窟数字展示中心附近',
      type: '专题展馆',
      recommendReason: '适合在参观莫高窟前后补充了解石窟保护和壁画艺术。',
      visitTime: '建议 1 小时',
      ticket: '以官方公布为准',
      openingHours: '以官方公布为准',
      cultureTags: ['文物保护', '壁画艺术', '敦煌学'],
      imageAlt: '敦煌研究院陈列中心',
    },
    {
      id: 'dunhuang-yardang',
      name: '雅丹地质公园',
      address: '甘肃省敦煌市西北约180公里',
      type: '地貌景观',
      recommendReason: '适合结合边塞历史与沙漠地貌体验。',
      visitTime: '建议半日',
      ticket: '约 120 元，以官方公布为准',
      openingHours: '以景区官方公布为准',
      cultureTags: ['边塞历史', '沙漠地貌', '自然遗产'],
      imageAlt: '雅丹地质公园',
    },
  ],
}

export const cultureData = {
  'xian-terracotta': {
    overview: '秦始皇帝陵博物院以兵马俑为核心，展示了秦代军事制度、雕塑艺术和陵寝文化。',
    history: '秦始皇统一六国后建立中央集权帝国，陵墓与陪葬坑体现了秦代强大的组织能力和“事死如事生”的丧葬观念。',
    value: '兵马俑被称为“世界第八大奇迹”，是研究秦代军事、工艺、服饰和社会制度的重要实物资料。',
    tip: '参观时建议重点关注一号坑军阵、铜车马和秦代兵器细节。',
  },
  'xian-museum': {
    overview: '陕西历史博物馆系统展示陕西地区从史前到唐代的文化发展脉络。',
    history: '陕西长期是中国古代政治、经济和文化中心，周、秦、汉、唐等朝代在这里留下大量珍贵遗存。',
    value: '馆藏青铜器、唐代金银器和壁画等文物，能帮助游客理解中华文明的重要阶段。',
    tip: '建议提前预约，并按历史朝代顺序参观。',
  },
  'xian-city-wall': {
    overview: '西安城墙是中国现存较完整的古代城垣之一，体现古代城市防御体系。',
    history: '明代在唐代长安城皇城基础上扩建城墙，形成今天看到的城垣格局。',
    value: '城墙不仅是军事设施，也反映了古代城市规划、交通管理和市民生活空间。',
    tip: '傍晚骑行或步行城墙，可以更好感受古城空间尺度。',
  },
  'hangzhou-west-lake': {
    overview: '西湖是江南文化景观的代表，融合了湖山、诗词、园林和民俗生活。',
    history: '唐宋以来，西湖经过多次疏浚和景观营造，逐渐成为文人吟咏和市民游赏的重要空间。',
    value: '西湖文化景观体现了中国传统山水审美和人与自然和谐相处的理念。',
    tip: '可结合白堤、苏堤、孤山等点位理解西湖的文化层积。',
  },
  'hangzhou-museum': {
    overview: '浙江省博物馆展示浙江地域文明，良渚文化是其中重要内容。',
    history: '良渚文化距今约五千年，是中华文明起源研究的重要实证。',
    value: '通过玉器、陶器和遗址资料，可以理解早期国家形态和江南文明发展。',
    tip: '适合与良渚古城遗址公园联动参观。',
  },
  'hangzhou-grand-canal': {
    overview: '京杭大运河杭州段展示了运河商贸、城市交通和市井生活。',
    history: '大运河连接南北，杭州因运河和钱塘江水运而兴盛，形成独特的商贸文化。',
    value: '运河文化体现了古代交通网络对城市经济和生活方式的影响。',
    tip: '可沿桥、码头和老街巷观察运河与城市生活的关系。',
  },
  'beijing-palace-museum': {
    overview: '故宫是明清皇家宫殿建筑群，也是宫廷文化和古代建筑艺术的集中体现。',
    history: '故宫始建于明代，历经明清两代皇家使用，见证了中国古代都城和礼制文化。',
    value: '其中轴线布局、殿宇等级和文物收藏共同构成理解中国传统政治文化的入口。',
    tip: '建议沿中轴线参观，并结合钟表馆、陶瓷馆等专题展。',
  },
  'beijing-temple-heaven': {
    overview: '天坛是明清皇帝祭天祈谷的礼制建筑群。',
    history: '古代帝王通过祭天仪式表达“天命”观念，天坛建筑以圆丘、祈年殿等象征天圆地方。',
    value: '天坛展示了礼制、建筑象征和古代宇宙观的结合。',
    tip: '重点观察祈年殿木构、回音壁和圜丘坛的空间象征。',
  },
  'beijing-hutong': {
    overview: '什刹海胡同片区保留了老北京街巷、民居和市井生活气息。',
    history: '胡同是北京传统城市肌理的重要组成部分，记录了居民生活、商业活动和城市变迁。',
    value: '胡同文化帮助游客从日常生活角度理解北京，而不仅停留在皇家建筑层面。',
    tip: '可结合烟袋斜街、银锭桥和周边名人故居游览。',
  },
  'nanjing-museum': {
    overview: '南京博物院馆藏丰富，是理解江苏地域文明和六朝文化的重要场馆。',
    history: '南京曾为六朝古都，也长期是江南文化重镇，历史层次非常丰富。',
    value: '通过馆藏文物和民国馆展示，可以看到南京从古代到近代的文化连续性。',
    tip: '建议预留充足时间，重点看历史馆和民国馆。',
  },
  'nanjing-city-wall': {
    overview: '明城墙体现了南京山水城林格局和明代城防思想。',
    history: '明代南京城墙规模宏大，结合自然山水进行防御布局，是古代城市工程的重要案例。',
    value: '登城可直观理解城墙、湖泊、山体与城市空间的关系。',
    tip: '可从台城或解放门段开始，远眺玄武湖和紫金山。',
  },
  'nanjing-presidential-palace': {
    overview: '南京总统府展示了近代政治建筑和民国历史记忆。',
    history: '这里曾与太平天国、两江总督署和民国政府等历史阶段相关，见证南京近代转型。',
    value: '总统府适合理解中国近代政治制度变迁和南京城市地位。',
    tip: '可结合建筑群、办公室复原展和园林空间参观。',
  },
  'chengdu-jinli': {
    overview: '锦里古街以川蜀民俗、传统小吃和街巷体验为主要特色。',
    history: '锦里依托武侯祠文化资源发展，展现成都传统市井生活和民俗商业氛围。',
    value: '它让游客通过饮食、手工艺和街巷空间感受成都的生活文化。',
    tip: '适合与武侯祠、三国文化线路结合游览。',
  },
  'chengdu-dufu': {
    overview: '杜甫草堂是纪念唐代诗人杜甫的重要场所，也是成都诗歌文化地标。',
    history: '杜甫曾在成都居住，留下多首描写草堂生活和蜀地风物的诗篇。',
    value: '草堂将诗歌、园林和纪念空间结合，体现中国文人纪念传统。',
    tip: '建议阅读《茅屋为秋风所破歌》等相关作品后再参观。',
  },
  'chengdu-jinsha': {
    overview: '金沙遗址博物馆展示古蜀文明的重要考古发现。',
    history: '金沙遗址出土太阳神鸟金饰等文物，揭示了成都平原早期文明的高度发展。',
    value: '它是理解古蜀信仰、金器工艺和成都城市起源的重要窗口。',
    tip: '重点观看太阳神鸟金饰、金面具和祭祀区展示。',
  },
  'dunhuang-mogao': {
    overview: '莫高窟是世界文化遗产，以石窟建筑和壁画艺术闻名。',
    history: '莫高窟开凿于十六国时期，历经多个朝代营建，成为丝路文化交流的重要见证。',
    value: '壁画、彩塑和洞窟空间共同展示了佛教艺术、丝路贸易和多元文明交流。',
    tip: '参观需遵守预约和洞窟保护规定，建议搭配数字展示中心。',
  },
  'dunhuang-academy': {
    overview: '敦煌研究院陈列中心展示敦煌学研究和石窟保护成果。',
    history: '近代以来，敦煌文献和石窟艺术逐渐受到国内外学界关注，敦煌学成为重要研究领域。',
    value: '它帮助游客理解文物保护、壁画研究和数字化保存的意义。',
    tip: '适合在莫高窟参观前后作为知识补充。',
  },
  'dunhuang-yardang': {
    overview: '雅丹地质公园以风蚀地貌和沙漠景观为主要特色。',
    history: '敦煌地处古代丝绸之路要冲，周边荒漠地貌与边塞历史、商旅交通密切相关。',
    value: '自然景观与边塞文化结合，可以拓展对丝路环境的理解。',
    tip: '注意防晒和补水，日落时段景观更具层次。',
  },
}

export const routeData = {
  xian: {
    provider: '高德地图静态路线',
    totalDistance: '约 42 公里',
    totalDuration: '约 1 小时 35 分钟',
    description: '推荐从市区城墙出发，先参观陕西历史博物馆，再前往秦始皇帝陵博物院，最后返回城墙区域。',
    navUrl: 'https://uri.amap.com/search?keyword=西安城墙,陕西历史博物馆,秦始皇帝陵博物院',
    legs: [
      { from: '西安城墙', to: '陕西历史博物馆', distance: '约 5 公里', duration: '约 20 分钟', tip: '市区道路较熟，建议避开早晚高峰。' },
      { from: '陕西历史博物馆', to: '秦始皇帝陵博物院', distance: '约 37 公里', duration: '约 1 小时 15 分钟', tip: '前往临潼方向路程较长，建议预留充足时间。' },
    ],
  },
  hangzhou: {
    provider: '高德地图静态路线',
    totalDistance: '约 28 公里',
    totalDuration: '约 1 小时 10 分钟',
    description: '推荐从西湖核心区开始，随后前往浙江省博物馆之江馆区，最后沿京杭大运河杭州段感受城市生活。',
    navUrl: 'https://uri.amap.com/search?keyword=西湖风景名胜区,浙江省博物馆之江馆区,京杭大运河杭州段',
    legs: [
      { from: '西湖风景名胜区', to: '浙江省博物馆之江馆区', distance: '约 14 公里', duration: '约 35 分钟', tip: '西湖周边人流较大，建议提前规划停车或公共交通。' },
      { from: '浙江省博物馆之江馆区', to: '京杭大运河杭州段', distance: '约 14 公里', duration: '约 35 分钟', tip: '晚间可结合运河夜景安排轻松游览。' },
    ],
  },
  beijing: {
    provider: '高德地图静态路线',
    totalDistance: '约 35 公里',
    totalDuration: '约 1 小时 30 分钟',
    description: '推荐以故宫为核心，再前往天坛了解礼制建筑，最后到什刹海胡同片区体验老北京街巷。',
    navUrl: 'https://uri.amap.com/search?keyword=故宫博物院,天坛公园,什刹海胡同片区',
    legs: [
      { from: '故宫博物院', to: '天坛公园', distance: '约 7 公里', duration: '约 25 分钟', tip: '故宫参观时间较长，建议控制节奏。' },
      { from: '天坛公园', to: '什刹海胡同片区', distance: '约 12 公里', duration: '约 40 分钟', tip: '晚高峰前往前门和鼓楼周边可能拥堵。' },
    ],
  },
  nanjing: {
    provider: '高德地图静态路线',
    totalDistance: '约 22 公里',
    totalDuration: '约 1 小时',
    description: '推荐先参观南京博物院，再登明城墙，最后前往南京总统府理解近代历史。',
    navUrl: 'https://uri.amap.com/search?keyword=南京博物院,明城墙,南京总统府',
    legs: [
      { from: '南京博物院', to: '明城墙', distance: '约 5 公里', duration: '约 20 分钟', tip: '可从解放门或台城段登城，视野较好。' },
      { from: '明城墙', to: '南京总统府', distance: '约 4 公里', duration: '约 18 分钟', tip: '总统府建议提前预约。' },
    ],
  },
  chengdu: {
    provider: '高德地图静态路线',
    totalDistance: '约 26 公里',
    totalDuration: '约 1 小时 15 分钟',
    description: '推荐从锦里古街体验民俗，再前往杜甫草堂，最后参观金沙遗址博物馆。',
    navUrl: 'https://uri.amap.com/search?keyword=锦里古街,杜甫草堂,金沙遗址博物馆',
    legs: [
      { from: '锦里古街', to: '杜甫草堂', distance: '约 3 公里', duration: '约 15 分钟', tip: '两地距离较近，可结合武侯祠片区游览。' },
      { from: '杜甫草堂', to: '金沙遗址博物馆', distance: '约 6 公里', duration: '约 25 分钟', tip: '下午参观金沙遗址，时间更从容。' },
    ],
  },
  dunhuang: {
    provider: '高德地图静态路线',
    totalDistance: '约 210 公里',
    totalDuration: '约 3 小时 30 分钟',
    description: '推荐以莫高窟为核心，搭配敦煌研究院陈列中心；雅丹地质公园路程较远，建议单独安排半日。',
    navUrl: 'https://uri.amap.com/search?keyword=莫高窟,敦煌研究院陈列中心,雅丹地质公园',
    legs: [
      { from: '莫高窟', to: '敦煌研究院陈列中心', distance: '约 2 公里', duration: '约 10 分钟', tip: '建议先参观数字展示中心，再进入洞窟。' },
      { from: '敦煌研究院陈列中心', to: '雅丹地质公园', distance: '约 180 公里', duration: '约 3 小时', tip: '路程较远，注意防晒、补水和车辆安排。' },
    ],
  },
}

export const destinationCustoms = {
  xian: '关中面食、城墙生活、回民街饮食和博物馆研学，都是理解西安日常文化的重要入口。',
  hangzhou: '茶文化、湖山游赏、运河街区和江南市井生活，是杭州文化体验中很有代表性的部分。',
  beijing: '胡同生活、老字号小吃、京剧和节令民俗，能帮助游客从日常层面理解北京。',
  nanjing: '秦淮风物、江南饮食、街巷生活和博物馆参观，是理解南京文化层次的重要方式。',
  chengdu: '茶馆、川菜、川剧和街巷生活体现了成都重视日常体验和城市慢生活的文化特点。',
  dunhuang: '敦煌文化体验常与石窟参观、丝路故事、地方小吃和沙漠旅行记忆结合。',
}

export const destinationGeography = {
  xian: '西安位于关中平原，南依秦岭，北临渭河，平原与山河屏障共同影响了古都选址和城市发展。',
  hangzhou: '杭州处在江南水网与钱塘江流域交汇处，西湖和运河共同塑造了城市景观与生活方式。',
  beijing: '北京位于华北平原北端，背靠燕山，面向平原，城市轴线、水系和交通区位影响了都城格局。',
  nanjing: '南京依江而建，紫金山、玄武湖和长江共同构成山水城林格局，也影响了城市防御与空间发展。',
  chengdu: '成都位于四川盆地西部，平原肥沃、水系发达，为蜀地农业、城市发展和休闲生活提供了基础。',
  dunhuang: '敦煌位于河西走廊西端，周边沙漠、绿洲和戈壁共同塑造了丝路交通与边塞文化。',
}

export function getRouteByDestination(destinationId) {
  return routeData[destinationId] || null
}

export const resourceData = {
  xian: {
    books: [
      { title: '《长安十二时辰》', author: '马伯庸', reason: '以唐代长安城市空间为背景，适合旅行前建立场景感。' },
      { title: '《陕西历史博物馆藏精品》', author: '陕西历史博物馆', reason: '适合配合博物馆参观，系统了解周秦汉唐文物。' },
    ],
    videos: [
      { title: '陕西历史博物馆导览', source: '官方/文博账号', reason: '可提前了解重点馆藏和参观路线。' },
      { title: '西安城墙文化讲解', source: '城市文化账号', reason: '帮助理解城墙与古都格局。' },
    ],
    articles: [
      { title: '唐代长安城市生活简介', source: '文旅科普', reason: '适合了解唐代市民生活和城市制度。' },
      { title: '秦始皇陵与兵马俑文化解读', source: '考古科普', reason: '适合补充秦代历史和考古知识。' },
    ],
  },
  hangzhou: {
    books: [
      { title: '《梦粱录》', author: '吴自牧', reason: '记录南宋临安城市生活，适合理解杭州宋韵文化。' },
      { title: '《西湖梦寻》', author: '张岱', reason: '以文学视角理解西湖景观与人文记忆。' },
    ],
    videos: [
      { title: '西湖文化景观讲解', source: '城市文化账号', reason: '可提前了解西湖十景和文化景观价值。' },
      { title: '京杭大运河杭州段导览', source: '运河文化账号', reason: '帮助理解运河与杭州城市发展的关系。' },
    ],
    articles: [
      { title: '宋韵杭州城市文化简介', source: '文旅科普', reason: '适合旅行前快速了解杭州文化主题。' },
      { title: '西湖诗词与景观审美', source: '文学科普', reason: '可结合诗词理解西湖景观。' },
    ],
  },
  beijing: {
    books: [
      { title: '《故宫六百年》', author: '阎崇年', reason: '适合了解故宫历史、建筑和宫廷文化。' },
      { title: '《北京中轴线》', author: '城市文化读物', reason: '帮助理解北京城市空间秩序。' },
    ],
    videos: [
      { title: '故宫博物院导览', source: '官方/文博账号', reason: '可提前规划故宫参观重点。' },
      { title: '北京中轴线文化讲解', source: '城市文化账号', reason: '适合理解北京古都格局。' },
    ],
    articles: [
      { title: '明清皇家建筑与礼制文化', source: '建筑科普', reason: '适合配合故宫和天坛参观。' },
      { title: '胡同里的老北京生活', source: '城市文化', reason: '适合什刹海胡同游览前阅读。' },
    ],
  },
  nanjing: {
    books: [
      { title: '《南京传》', author: '叶兆言', reason: '以城市视角理解南京历史变迁。' },
      { title: '《六朝往事》', author: '历史读物', reason: '适合补充六朝文化背景。' },
    ],
    videos: [
      { title: '南京博物院导览', source: '官方/文博账号', reason: '帮助提前了解重点展厅。' },
      { title: '明城墙与南京城市格局', source: '城市文化账号', reason: '适合登城墙前观看。' },
    ],
    articles: [
      { title: '南京六朝文化简介', source: '历史科普', reason: '适合理解南京作为六朝古都的背景。' },
      { title: '民国建筑与南京城市记忆', source: '城市文化', reason: '适合总统府参观前阅读。' },
    ],
  },
  chengdu: {
    books: [
      { title: '《成都街巷志》', author: '城市文化读物', reason: '适合了解成都街巷和市民生活。' },
      { title: '《杜甫在成都》', author: '文学读物', reason: '适合配合杜甫草堂参观。' },
    ],
    videos: [
      { title: '金沙遗址博物馆导览', source: '官方/文博账号', reason: '帮助理解古蜀文明重点文物。' },
      { title: '成都茶馆文化', source: '城市生活账号', reason: '适合体验成都慢生活前观看。' },
    ],
    articles: [
      { title: '古蜀文明与太阳神鸟', source: '考古科普', reason: '适合金沙遗址参观前阅读。' },
      { title: '成都川菜与民俗生活', source: '美食文化', reason: '适合锦里和街巷游览前阅读。' },
    ],
  },
  dunhuang: {
    books: [
      { title: '《敦煌石窟艺术》', author: '艺术史读物', reason: '适合了解莫高窟壁画和彩塑艺术。' },
      { title: '《丝绸之路简史》', author: '历史读物', reason: '帮助理解敦煌在丝路中的位置。' },
    ],
    videos: [
      { title: '数字敦煌导览', source: '敦煌研究院/文博账号', reason: '可提前了解洞窟艺术和保护工作。' },
      { title: '敦煌丝路文化讲解', source: '历史文化账号', reason: '适合理解敦煌多元文化交流。' },
    ],
    articles: [
      { title: '莫高窟壁画艺术简介', source: '艺术科普', reason: '适合参观莫高窟前阅读。' },
      { title: '敦煌与丝绸之路', source: '历史科普', reason: '帮助理解敦煌的丝路背景。' },
    ],
  },
}

export function getResourcesByDestination(destinationId) {
  return resourceData[destinationId] || { books: [], videos: [], articles: [] }
}

export function getRecommendedDestinations(requirement) {
  const text = requirement || ''
  const keywords = [
    { keys: ['唐', '秦', '兵马俑', '城墙'], id: 'xian' },
    { keys: ['宋', '西湖', '茶', '运河'], id: 'hangzhou' },
    { keys: ['皇家', '故宫', '长城', '中轴线'], id: 'beijing' },
    { keys: ['六朝', '民国', '明城墙', '近代'], id: 'nanjing' },
    { keys: ['蜀', '川菜', '茶馆', '熊猫'], id: 'chengdu' },
    { keys: ['丝路', '石窟', '沙漠', '莫高窟'], id: 'dunhuang' },
  ]

  const keywordHits = new Map()
  keywords.forEach((item) => {
    item.keys.forEach((key) => {
      if (text.includes(key)) {
        keywordHits.set(item.id, (keywordHits.get(item.id) || 0) + 1)
      }
    })
  })

  const ranked = destinationData
    .map((destination) => ({
      ...destination,
      matchScore: keywordHits.get(destination.id)
        ? Math.min(99, destination.matchScore + keywordHits.get(destination.id) * 2)
        : destination.matchScore,
    }))
    .sort((a, b) => b.matchScore - a.matchScore)

  return ranked.slice(0, 3)
}

export function getSpotsByDestination(destinationId) {
  return (spotData[destinationId] || []).map((spot) => ({
    ...spot,
    culture: cultureData[spot.id] || null,
    imageUrl: spot.imageUrl || `https://picsum.photos/seed/cultural-${destinationId}-${spot.id}/640/420`,
  }))
}

export function getCultureByDestination(destinationId, spot) {
  const baseCulture = cultureData[spot.id] || {}
  const customs = destinationCustoms[destinationId] || '当地风俗习惯和生活方式往往体现在饮食、街巷、节庆和日常体验中。'
  const geography = destinationGeography[destinationId] || '当地地理环境、水系、地形和交通区位共同影响了城市发展和文化形成。'
  const foodSuggestions = {
    xian: '可结合肉夹馍、羊肉泡馍或回民街小吃理解关中饮食文化。',
    hangzhou: '可结合龙井茶、片儿川、南宋御街小吃体验江南饮食与城市生活。',
    beijing: '可结合烤鸭、卤煮、豆汁或胡同小吃体验北京饮食文化。',
    nanjing: '可结合盐水鸭、鸭血粉丝汤和夫子庙小吃体验南京地方风味。',
    chengdu: '可结合担担面、钟水饺、茶馆和川菜体验成都生活文化。',
    dunhuang: '可结合驴肉黄面、胡羊焖饼或夜市小吃体验西北边塞风味。',
  }

  return {
    spotId: spot.id,
    spotName: spot.name,
    overview: baseCulture.overview || '该景点适合从历史文化、风俗习惯和地理环境三个角度理解。',
    historyCulture: [baseCulture.history, baseCulture.value].filter(Boolean).join('') || '该景点体现了当地历史文化的延续，可从建筑、遗存、文物或城市记忆中理解其价值。',
    customs: customs,
    geography: geography,
    foodSuggestion: foodSuggestions[destinationId] || '',
    tags: spot.cultureTags || ['文化旅行'],
  }
}
