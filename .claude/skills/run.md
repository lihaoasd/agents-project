---
description: 启动、运行并验证文化旅行后端 FastAPI 项目。
---

# run 技能：文化旅行后端启动测试

当用户要求“启动测试”“跑一下后端”“验证 API”“启动 FastAPI”“测试 /api/travel-plan”时，使用本技能。

## 目标

- 使用 `backend/.venv` 虚拟环境启动后端。
- 只测试后端项目，不主动启动或修改前端。
- 优先验证 FastAPI 是否能启动，再验证核心 API 是否可调用。
- 如果端口被占用或依赖缺失，给出明确修复步骤。

## 默认命令

在项目根目录执行：

```bash
cd backend/trip_plan
../.venv/Scripts/python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

如果 `../.venv/Scripts/python.exe` 不存在，则先提示用户执行：

```bash
cd backend
py -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```

## 启动后验证

后端启动成功后，测试以下接口：

```bash
curl http://127.0.0.1:8000/api/health
```

```bash
curl http://127.0.0.1:8000/api/cities
```

```bash
curl -X POST http://127.0.0.1:8000/api/travel-plan \
  -H "Content-Type: application/json" \
  -d "{\"requirement\":\"想带孩子了解唐代文化，3天，预算中等\",\"days\":3,\"budget\":\"中等\",\"interests\":[\"历史\",\"文化\",\"亲子\"],\"language\":\"zh-CN\"}"
```

可选验证：

```bash
curl "http://127.0.0.1:8000/api/scenic-spots?city_id=xian&limit=3"
```

```bash
curl "http://127.0.0.1:8000/api/scenic-spots/xian_museum/detail"
```

```bash
curl "http://127.0.0.1:8000/api/routes?spot_ids=xian_museum,xian_citywall,xian_datang&city_id=xian&days=2"
```

## 输出要求

- 用中文汇报。
- 明确写出启动命令。
- 明确写出测试接口和结果。
- 如果失败，贴出关键错误，并给出下一步修复建议。
- 不要修改前端文件。
