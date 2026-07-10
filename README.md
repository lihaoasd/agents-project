# Agent project
好用的 Agent 工具
## 🛠 技术栈

| 层 | 技术 |
|---|------|
| **前端** | Vue 3 (Composition API) + Vite + vue-router |
| **后端** | Python FastAPI + Uvicorn |
| **AI** | Pydantic AI Agent + 兼容 OpenAI 格式的 LLM |
| **地图** | 高德地图 Web API |
| **PDF** | jsPDF + html2canvas |

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- 高德地图 API Key（[申请地址](https://lbs.amap.com/)）
- LLM API Key（兼容 OpenAI 格式）

### 1. 后端配置

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
source .venv/Scripts/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入真实密钥
```

`.env` 示例：

```env
# 高德地图
AMAP_API_KEY=你的高德key

# LLM 模型
LLM_MODEL_NAME=DeepSeek-V4-Pro
LLM_API_KEY=你的LLM-API-Key
LLM_API_BASE=https://your-api-endpoint/v1
```

### 2. 启动后端

```bash
cd backend
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Git Bash / Linux / macOS
# source .venv/Scripts/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

或直接运行（默认 `127.0.0.1:8000`）：

```bash
cd backend
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Git Bash / Linux / macOS
# source .venv/Scripts/activate
python main.py
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173` 即可使用。

## 🏯 文化旅行 Agent

> AI 驱动的文化旅行规划系统 — 输入你的旅行需求，AI 自动推荐目的地、生成景点、解读文化、规划路线，并导出 PDF 旅行手帐。

### ✨ 功能

- **目的地推荐** — 根据自然语言描述，智能匹配最适合的文化旅游城市
- **景点生成** — 为选定城市自动生成推荐景点列表，附带详细介绍
- **文化解读** — 多维度文化解析（历史、民俗、地理、美食）
- **路线规划** — 基于高德地图 API 的实时路线规划
- **旅行手帐 PDF** — 一键导出精美旅行手帐，含封面、景点、文化解读、路线全览
