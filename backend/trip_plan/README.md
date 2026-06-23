# 文化旅行 Agent 后端

这是一个轻量 FastAPI 后端 MVP，默认不依赖数据库，不要求系统环境变量。未配置 LLM / 高德地图 Key 时，会使用本地规则模板生成城市、景点、详情、文本路线和内容推荐。

## 目录

```text
backend/
├─ .env
├─ requirements.txt
└─ trip_plan/
   ├─ main.py
   ├─ api/
   ├─ agent/
   ├─ service/
   ├─ config/
   └─ README.md
```

## 启动

```bash
cd backend
py -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt

cd trip_plan
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

如果 `uvicorn` 不可用：

```bash
cd backend/trip_plan
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## API

- `GET /api/health`：健康检查
- `POST /api/travel-plan`：根据旅游要求生成完整旅行计划
- `GET /api/cities`：获取候选省份地市
- `GET /api/scenic-spots`：根据地市或关键词获取景点
- `GET /api/scenic-spots/{spot_id}/detail`：获取景点详情
- `GET /api/routes`：获取文本路线规划
- `GET /api/recommendations`：获取书籍、短视频、文章推荐

示例：

```bash
curl -X POST http://127.0.0.1:8000/api/travel-plan \
  -H "Content-Type: application/json" \
  -d "{\"requirement\":\"想带孩子了解唐代文化，3天，预算中等\",\"days\":3,\"budget\":\"中等\",\"interests\":[\"历史\",\"文化\",\"亲子\"],\"language\":\"zh-CN\"}"
```

## 配置

`backend/.env` 已提供占位配置。不要把真实密钥提交到仓库。

```env
ENABLE_LLM=false
ANTHROPIC_API_KEY=
ENABLE_AMAP=false
AMAP_KEY=
MCP_CONFIG_PATH=
```

当前默认 `ENABLE_LLM=false`、`ENABLE_AMAP=false`，因此可以直接本地运行。后续接入 LLM / MCP / 高德地图时，可在 `agent/trip_agent.py` 和 `service/trip_service.py` 中扩展。

## 免责声明

文化介绍、开放时间、票价和路线可能变化，出行前请以景区、博物馆和地图平台实时信息为准。
