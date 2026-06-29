---
description: 为“文化旅行的 FastAPI + Vue 3 Agent 项目”提供需求澄清、架构设计、代码实现和验证指南。
---

# 文化旅行 FastAPI + Vue 3 Agent 项目 Skill

当用户提到“文化旅行”“文旅”“HTML + Python agent”“旅行助手”“景点讲解”“行程规划”“文化导览”等需求时，使用本 skill 协助规划、搭建或迭代一个面向文化旅行的 Web Agent 项目。

## 目标

构建一个轻量、可运行、可扩展的文化旅行 Agent Web 应用：

- 后端：Python + FastAPI，固定使用 FastAPI，不使用 Flask。
- 前端：Vue 3 + Vite，使用 `.vue` 组件组织页面。
- 架构：基于大模型 + MCP 实现，后端负责调用大模型/MCP 工具、编排推荐结果。
- Agent 能力：围绕旅行目的地、文化背景、地市推荐、景点推荐、景点基本信息、历史文化介绍、路线规划、书籍/短视频/文章推荐生成建议。
- 不使用数据库，不设计登录、后台管理、支付等复杂功能。
- 默认提供可本地运行的最小版本，并保留后续接入高德地图 MCP/API、搜索 MCP、知识库 MCP 的能力。
- 当前环境中无法设置系统环境变量，因此不要把系统环境变量作为运行前提；如需配置，优先使用项目内 `.env` 或显式配置文件。

## 默认项目结构

```text
cultural_travel_agent/
├─ backend/
│  ├─ .env
│  └─ trip_plan
│     ├─ api/
│     ├─ agent/
│     ├─ service/
│     ├─ config/
│     └─ README.md
├─ frontend/
│  ├─ index.html
│  ├─ package.json
│  ├─ vite.config.js
│  └─ src/
│     ├─ main.js
│     ├─ App.vue
│     ├─ assets/
│     └─ components/
└─ README.md
```

后端固定采用以下结构：

- `.env`：项目内配置文件，用于本地配置；不要求用户设置系统环境变量。高德地图 API Key、LLM API Key 等放在这里。
- `api`：FastAPI 路由和请求/响应模型。
- `agent`：旅游需求理解、地市推荐、景点推荐、历史文化生成、内容推荐等 Agent 逻辑。
- `service`：业务服务层，协调配置、Agent、高德地图、景点数据和内容拼装。
- `config`：配置读取与校验。

核心功能包括：

1. 用户输入一个旅游要求。
2. 根据用户要求推荐省份地市。
3. 根据地市推荐旅游景点。
4. 生成旅游景点基本信息。
5. 生成每个旅游景点的历史文化介绍。
6. 获取景点图片并支持浏览。
7. 通过高德地图生成规划路线。
8. 推荐相关书籍、短视频、文章。

如当前目录已经是项目根目录，可直接在当前目录创建对应结构，避免重复套目录。

## 环境约定

Node 固定目录：

```text
D:\lihao\Programs\node-v20.3.1-win-x64
```

npm 全局包目录：

```text
D:\lihao\Programs\node-v20.3.1-win-x64\node_global
```

前端命令使用该目录下的 Node/npm：

```bash
cd frontend
D:/lihao/Programs/node-v20.3.1-win-x64/npm.cmd install
D:/lihao/Programs/node-v20.3.1-win-x64/npm.cmd run dev
```

后端 Python 命令按系统实际 Python 路径执行。若在 VS Code 终端中 `python` 不可用，可改用 `py`：

```bash
cd backend
py -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

如果 `uvicorn` 命令不可用，使用：

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## 执行流程

1. **澄清需求**
   - 如果用户只给出模糊目标，先确认：
     - 目标用户：自由行游客、研学团队、博物馆游客、城市文旅局、导游？
     - 核心功能：行程规划、景点讲解、文化问答、路线推荐、收藏 itinerary、多语言？
     - 大模型与 MCP 如何接入：本地 MCP Server、远程 MCP Server，还是通过 API 封装？
     - 高德地图能力通过 MCP 工具接入，还是通过高德 Web API 封装？
     - 是否需要登录、数据库或后台管理？默认不需要，只做几个前端页面和后端 API。
   - 若用户希望直接开做，采用默认 MVP。

2. **MVP 范围**
   - 前端只做几个必要页面，不设计后台管理页面：
     - 首页/需求输入页：输入旅游要求，例如“想带孩子了解唐代文化，3 天，预算中等”。
     - 地市推荐页：展示推荐省份、地市和推荐理由。
     - 景点列表页：展示景点名称、地址、推荐理由、图片入口。
     - 景点详情页：展示基本信息、历史文化介绍、图片浏览、高德路线和相关推荐。
   - 前端页面包含：
     - 用户旅游要求输入框，例如“想带孩子了解唐代文化，3 天，预算中等”。
     - 推荐地市展示区，展示省份、地市和推荐理由。
     - 景点推荐列表，展示景点名称、地址、推荐理由、图片入口。
     - 景点详情区，展示基本信息、历史文化介绍、图片浏览。
     - 高德地图路线区，展示景点之间的规划路线。
     - 内容推荐区，展示相关书籍、短视频、文章。
   - Agent 逻辑：
     - 默认基于大模型 + MCP 编排结果：由 Agent 调用推荐、检索、地图、内容生成等 MCP 工具。
     - 不要要求设置系统环境变量；模型 Key、MCP Server 配置、高德地图 Key 等通过项目内 `.env` 或显式配置文件读取。
     - MCP 或大模型不可用时，使用 Python 规则模板和本地文旅样例数据降级生成结果。
     - 高德地图能力优先通过 MCP 工具接入；若不可用，再通过高德 Web API 或返回可替代的文本路线。

3. **实现原则**
   - 后端固定使用 FastAPI，使用 Pydantic 定义请求/响应模型。
   - 后端采用“FastAPI + 大模型 + MCP”的编排架构，不在默认 MVP 中设计数据库访问层。
   - 前端固定使用 Vue 3 + Vite，使用 Composition API 或清晰的组件结构。
   - 后端启用 CORS，允许 Vue Vite 开发服务器访问。
   - 高德地图能力放在 `service` 层封装，优先调用 MCP 工具，避免业务代码直接依赖地图 SDK 细节。
   - 景点基础信息、历史文化、图片、内容推荐通过大模型/MCP 生成或检索，结果以 API 响应返回。
   - 代码简洁，中文注释适量。
   - API 响应使用明确字段，便于前端渲染。
   - 前端错误处理要友好，避免空白页。
   - 不硬编码密钥；如果必须配置密钥，使用不提交到仓库的本地配置文件或用户显式传入。
   - 对旅行建议添加免责声明：文化、开放时间和费用可能变化，出行前需核实。
   - 尊重当地文化，不生成冒犯、歧视、危险或违法建议。

4. **验证方式**
   - 后端启动：
     ```bash
     cd backend
     py -m venv .venv
     .venv/Scripts/activate
     pip install -r requirements.txt
     uvicorn main:app --reload --host 127.0.0.1 --port 8000
     ```
   - 前端启动：
     ```bash
     cd frontend
     D:/lihao/Programs/node-v20.3.1-win-x64/npm.cmd install
     D:/lihao/Programs/node-v20.3.1-win-x64/npm.cmd run dev
     ```
   - 前端验证：
     - 打开 Vite 输出的本地地址。
     - 输入旅游要求。
     - 确认页面能显示推荐省份地市、景点列表、景点详情、图片浏览、高德路线和书籍/短视频/文章推荐。
     - 如果未配置高德地图 Key，应看到友好提示，而不是页面报错。

## 默认回答风格

- 用中文沟通。
- 先给可运行 MVP，再给可扩展方向。
- 涉及 API Key、账号、地图密钥时，提醒用户不要提交到仓库。
- 如果用户要求“写完整项目”，直接生成文件结构、代码和运行说明。
- 如果用户要求“只写 skill”，只输出或创建 skill 文档，不要额外生成项目代码。