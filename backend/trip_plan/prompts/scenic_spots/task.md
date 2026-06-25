根据用户文化旅行需求和选定的目的地城市，推荐 3-5 个该城市最值得去的文化旅行景点。

你需要结合用户偏好分析：
- 文化主题匹配
- 旅行人群适合度
- 时间长度合理度
- 景点多样性（博物馆、遗址、街区、园林等不同类型）

输出字段必须包含：
- id：景点唯一标识，使用拼音加类型的形式，例如 xian-terracotta、hangzhou-west-lake
- name：景点名称
- address：景点地址
- type：景点类型，例如 遗址博物馆、综合博物馆、文化景观、历史街区、礼制建筑
- recommendReason：推荐理由，结合用户偏好说明为什么推荐
- visitTime：建议游览时长，例如 建议 2-3 小时、建议半日
- ticket：门票信息，以"以官方公布为准"结尾，避免编造精确价格
- openingHours：开放时间，以"以官方为准"结尾
- cultureTags：文化标签数组，3-5 个
- imageAlt：图片替代文字，用景点名称
- imageUrl：空字符串或留空
- imageSearchQuery：用于 Unsplash 英文图片检索的查询词，必须用英文，尽量包含景点英文名、城市英文名和国家/地区，例如 "Mogao Caves Dunhuang Gansu China"、"West Lake Hangzhou China"；不确定英文名时可写空字符串

注意：
- 不要编造精确门票价格和确切开放时间
- 如果用户信息不足，推荐该城市最经典的文化景点
- 景点类型尽量多样化
- 输出纯 JSON，不要带 Markdown 标记