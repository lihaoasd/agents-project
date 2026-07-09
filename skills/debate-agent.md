---
description: 多Agent辩论 — 聊天室形式，用户+辩者+裁判三类角色，后端状态机驱动 SSE 实时推送，支持立论/质询/结辩/投票/裁判总结全流程。
---

# 多 Agent 辩论 Skill

当用户提到"辩论""多agent辩论""角色辩论""圣贤辩论""思想比较""聊天辩论"时，使用本 skill。

## 产品形态

一个**实时聊天室**，参与者有 3 类角色：

```
┌──────────────────────────────────────────────────┐
│  聊天室                                          │
│                                                  │
│  👤 用户      — 提出问题，旁观辩论               │
│  🎭 辩者 A    — 立论、质询、回答、结辩、投票     │
│  🎭 辩者 B    — 同上                             │
│  🎭 辩者 C    — 同上                             │
│  ⚖️ 裁判      — 统计票数、总结辩论               │
│                                                  │
│  所有发言以聊天消息形式逐条出现                    │
└──────────────────────────────────────────────────┘
```

- **用户**：发起辩论（输入问题 + 选择辩者 + 选择裁判），旁观全程
- **辩者**：以角色人格发言，每条消息标注"谁在说、对谁说、属于哪个阶段"
- **裁判**：不参与辩论，只在最后阶段统计和总结

---

## 接口设计（5 个端点）

### 1. GET /api/debate/roles — 获取角色库

前端初始化时调用，获取所有可选辩者和裁判预设。

**响应**：

```json
{
  "data": {
    "debaters": [
      {
        "id": "confucius",
        "name": "孔子",
        "school": "儒家",
        "avatar": "🎭",
        "persona_short": "仁爱礼治，中庸之道，以周礼为理想秩序",
        "persona_full": "你是孔子，儒家学派创始人。你主张仁爱礼治、中庸之道..."
      },
      {
        "id": "laozi",
        "name": "老子",
        "school": "道家",
        "avatar": "🎭",
        "persona_short": "道法自然，无为而治，柔弱胜刚强",
        "persona_full": "..."
      }
    ],
    "judges": [
      {
        "id": "mozi",
        "name": "墨子",
        "avatar": "⚖️",
        "persona_short": "逻辑严谨，以论证质量和一致性为评判标准",
        "persona_full": "..."
      }
    ]
  }
}
```

### 2. POST /api/debate/start — 发起辩论

用户选择辩者+裁判+输入问题后调用。后端创建会话，初始化状态机，返回 session_id。

**请求**：

```json
{
  "question": "人之初，性本善还是性本恶？",
  "debater_ids": ["confucius", "laozi", "hanfei", "wangyangming"],
  "judge_id": "mozi",
  "cross_examination_rounds": 1
}
```

**响应**：

```json
{
  "data": {
    "session_id": "debate_a1b2c3d4",
    "status": "starting",
    "participants": [
      {"id": "user", "name": "用户", "role": "user", "avatar": "👤"},
      {"id": "confucius", "name": "孔子", "role": "debater", "avatar": "🎭", "school": "儒家"},
      {"id": "laozi", "name": "老子", "role": "debater", "avatar": "🎭", "school": "道家"},
      {"id": "hanfei", "name": "韩非", "role": "debater", "avatar": "🎭", "school": "法家"},
      {"id": "wangyangming", "name": "王阳明", "role": "debater", "avatar": "🎭", "school": "心学"},
      {"id": "mozi", "name": "墨子", "role": "judge", "avatar": "⚖️"}
    ]
  }
}
```

### 3. GET /api/debate/stream/{session_id} — SSE 实时辩论流

前端连接此 SSE 端点后，后端自动按状态机推进全部辩论流程，逐条推送聊天消息。

**SSE 事件类型**：共 6 种事件。

---

#### event: message_start — 某角色开始发言

后端调度到某个角色发言时**立即推送**，不等待 LLM 生成。前端可据此**创建空消息气泡**，准备逐字填充。

```json
event: message_start
data: {
  "id": "msg_001",
  "timestamp": 1719740001.234,
  "phase": "opening",
  "speaker": {
    "id": "confucius",
    "name": "孔子",
    "role": "debater",
    "avatar": "🎭"
  },
  "target": {
    "id": "all",
    "name": "所有人"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 消息唯一 ID，后续 `message_delta` / `message_end` 都用同一个 id |
| `timestamp` | float | 发言开始时间 |
| `phase` | string | 当前阶段 |
| `speaker.id` | string | 发言人 ID |
| `speaker.name` | string | 发言人名称 |
| `speaker.role` | string | `user` / `debater` / `judge` |
| `speaker.avatar` | string | 头像 emoji |
| `target.id` | string | 说话对象 ID，`"all"` 表示对所有人 |
| `target.name` | string | 说话对象名称 |

---

#### event: message_delta — 逐 token 增量文本

后端 LLM 流式生成时，**每拿到一个 token 就推送一次**。同一 `id` 会推送 N 次。前端**追加**到对应消息气泡末尾。

```json
event: message_delta
data: {
  "id": "msg_001",
  "delta": "子"
}
```

```json
event: message_delta
data: {
  "id": "msg_001",
  "delta": "曰"
}
```

…LLM 每生成一个 token 推送一条，直到发言完毕。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 对应 `message_start` 的消息 ID |
| `delta` | string | 增量文本，每次 1 到几个 token（通常 1-3 个中文字符） |

> **并行打字机效果**：多个辩者并行发言时，`message_delta` 会**交错推送**。前端按 `id` 分组，每个 id 独立拼接。表现为多个气泡**同时逐字增长**——这正是 ChatGPT 多轮对话的体验。

---

#### event: message_end — 某角色发言完毕

LLM 生成完成后推送。前端标记该消息气泡**已完成**。

```json
event: message_end
data: {
  "id": "msg_001",
  "timestamp": 1719740005.678
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 对应 `message_start` 的消息 ID |
| `timestamp` | float | 发言完成时间 |

---

#### event: phase_change — 阶段切换

后端进入新阶段时推送（在该阶段所有发言 `message_end` 之后）。前端展示**阶段分隔条**。

```json
event: phase_change
data: {
  "phase": "cross_examine",
  "label": "⚔️ 质询环节",
  "description": "辩者互相质询，直击论证弱点",
  "round": 1,
  "total_rounds": 1
}
```

---

#### event: done — 辩论结束

```json
event: done
data: {
  "session_id": "debate_a1b2c3d4",
  "total_messages": 20,
  "duration_seconds": 68.5,
  "winner": {
    "id": "wangyangming",
    "name": "王阳明",
    "votes": 2
  }
}
```

---

#### event: error — 错误

某次 LLM 调用失败时推送。不影响其他并行的 LLM 调用。

```json
event: error
data: {
  "id": "msg_005",
  "speaker": "韩非",
  "code": "LLM_TIMEOUT",
  "message": "韩非回答质询超时，已跳过"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 失败的消息 ID（如果有） |
| `speaker` | string | 失败的发言者 |
| `code` | string | 错误码：`LLM_TIMEOUT` / `LLM_ERROR` |
| `message` | string | 人类可读的错误描述 |

---

### SSE 时序示例（立论阶段，3 个辩者并行）

```
event: phase_change     ← 进入立论阶段
data: {"phase":"opening","label":"📜 立论"}

event: message_start    ← 孔子开始发言（前端创建气泡 A）
data: {"id":"msg_01","speaker":{"name":"孔子"},...}

event: message_start    ← 老子同时开始（创建气泡 B）
data: {"id":"msg_02","speaker":{"name":"老子"},...}

event: message_start    ← 韩非同时开始（创建气泡 C）
data: {"id":"msg_03","speaker":{"name":"韩非"},...}

event: message_delta    ← 三个气泡交错逐字增长
data: {"id":"msg_01","delta":"子"}
event: message_delta
data: {"id":"msg_02","delta":"道"}
event: message_delta
data: {"id":"msg_01","delta":"曰"}
event: message_delta
data: {"id":"msg_03","delta":"韩"}
event: message_delta
data: {"id":"msg_02","delta":"可"}
  ...（持续交错推送）...

event: message_end      ← 老子最先完成
data: {"id":"msg_02"}

event: message_end      ← 韩非完成
data: {"id":"msg_03"}

event: message_end      ← 孔子最后完成
data: {"id":"msg_01"}

event: phase_change     ← 全部完成，进入下一阶段
data: {"phase":"cross_examine","round":1}
```

---

### 4. GET /api/debate/sessions/{session_id} — 获取会话记录

辩论结束后，前端可通过此接口获取完整的结构化辩论记录（JSON 格式），支持存档和导出。

**响应**：

```json
{
  "data": {
    "session_id": "debate_a1b2c3d4",
    "question": "人之初，性本善还是性本恶？",
    "status": "completed",
    "created_at": 1719740001.234,
    "duration_seconds": 68.5,
    "config": {
      "debaters": [
        {"id": "confucius", "name": "孔子", "school": "儒家", "avatar": "🎭"},
        {"id": "laozi", "name": "老子", "school": "道家", "avatar": "🎭"},
        {"id": "hanfei", "name": "韩非", "school": "法家", "avatar": "🎭"},
        {"id": "wangyangming", "name": "王阳明", "school": "心学", "avatar": "🎭"}
      ],
      "judge": {"id": "neutral_analyst", "name": "中立分析者", "avatar": "⚖️"},
      "cross_examination_rounds": 1
    },
    "stages": {
      "opening": {
        "phase": "opening",
        "label": "📜 立论",
        "messages": [
          {
            "id": "msg_01",
            "timestamp": 1719740001.5,
            "speaker": {"id": "confucius", "name": "孔子", "role": "debater", "avatar": "🎭", "school": "儒家"},
            "target": {"id": "all", "name": "所有人"},
            "content": "子曰：性相近也，习相远也..."
          }
        ]
      },
      "cross_examine": {
        "phase": "cross_examine",
        "label": "⚔️ 质询",
        "rounds": 1,
        "qa_pairs": [
          {
            "round": 1,
            "asker": {"id": "confucius", "name": "孔子"},
            "answerer": {"id": "hanfei", "name": "韩非"},
            "question": "若人性果真好利恶害，何以解释子路负米、曾子易箦之行为？",
            "answer": "子路负米乃为孝名，曾子易箦恰证明了奖惩机制的内化..."
          }
        ]
      },
      "closing": {
        "phase": "closing",
        "label": "🏁 结辩",
        "messages": []
      },
      "voting": {
        "phase": "voting",
        "label": "🗳️ 投票",
        "votes": [
          {"voter": "confucius", "vote_for": "wangyangming", "reason": "知行合一将抽象问题操作化..."},
          {"voter": "laozi", "vote_for": "wangyangming", "reason": "心外无物说绕开了善恶二元对立..."},
          {"voter": "hanfei", "vote_for": "confucius", "reason": "教化论提供了可操作的治理路径..."},
          {"voter": "wangyangming", "vote_for": "hanfei", "reason": "法治主义的现实感最强..."}
        ],
        "tally": {
          "wangyangming": 2,
          "confucius": 1,
          "hanfei": 1,
          "laozi": 0
        },
        "awards": {
          "best_argument": {
            "recipient": "wangyangming",
            "reason": "知行合一框架将抽象人性论转化为可验证的实践命题，论证最严密且具原创性"
          },
          "best_cross_examine": {
            "recipient": "confucius",
            "reason": "孔子对韩非的质询——「若人性好利恶害，何以解释子路负米」——直击法家人性论的经验反例"
          }
        }
      },
      "judge_summary": {
        "phase": "judge_summary",
        "label": "📝 裁判总结",
        "content": "# 辩论总结：人之初，性本善还是性本恶？\n\n## 辩论概览\n..."
      }
    },
    "export": {
      "markdown": "# 多Agent辩论：人之初，性本善还是性本恶？\n\n**辩论时间**：2026-06-30 10:30\n...",
      "markdown_url": "/api/debate/sessions/debate_a1b2c3d4/export?format=md",
      "json_url": "/api/debate/sessions/debate_a1b2c3d4/export?format=json"
    }
  }
}
```

**状态码**：
- `200`：成功
- `404`：会话不存在或已过期
- `409`：辩论仍在进行中（返回 `status: "running"` 和当前阶段）

### 5. GET /api/debate/sessions/{session_id}/export?format=md|json|pdf — 导出会话

下载辩论记录文件。辩论进行中时不可导出（返回 409）。

**查询参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `format` | string | `pdf` — 下载美观排版的 PDF 文件；`md` — 下载 Markdown 文件；`json` — 下载 JSON 文件 |

**响应**：

- `format=pdf`：`Content-Type: application/pdf`，`Content-Disposition: attachment; filename="debate_{session_id}.pdf"`（直接在浏览器中预览更友好，使用 `inline` 替代 `attachment`）
- `format=md`：`Content-Type: text/markdown`，`Content-Disposition: attachment; filename="debate_{session_id}.md"`
- `format=json`：`Content-Type: application/json`，`Content-Disposition: attachment; filename="debate_{session_id}.json"`

### PDF 生成方案

后端使用 **WeasyPrint**（Python 库，支持中文）将 Markdown → HTML → PDF。流程：

```
辩论记录 Markdown
      │
      ▼  marked / markdown-it (前端) 或 Python markdown 库
HTML（带 CSS 排版）
      │
      ▼  WeasyPrint
PDF 文件（美观排版）
```

**PDF 排版设计**：

```
┌─────────────────────────────────────┐
│                                     │
│        多Agent辩论                   │
│   人之初，性本善还是性本恶？          │
│                                     │
│  辩论时间：2026年6月30日 10:30 CST   │
│  辩者：孔子（儒家）、老子（道家）、  │
│        韩非（法家）、王阳明（心学）   │
│  裁判：中立分析者                    │
│                                     │
│  ═══════════════════════════════    │
│                                     │
│   📜 立论                           │
│  ┌─────────────────────────────┐    │
│  │ 🎭 孔子 · 儒家              │    │
│  │                             │    │
│  │ 子曰：性相近也，习相远也。   │    │
│  │ 人之初，性非本善亦非本恶，   │    │
│  │ 性如素丝，染于苍则苍...     │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 🎭 老子 · 道家              │    │
│  │                             │    │
│  │ 道可道，非常道...           │    │
│  └─────────────────────────────┘    │
│                                     │
│   ⚔️ 质询 · 第 1 轮                 │
│  ┌─────────────────────────────┐    │
│  │ 🎭 孔子 → @韩非             │    │
│  │                             │    │
│  │ 若人性果真好利恶害，        │    │
│  │ 何以解释子路负米？          │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 🎭 韩非 → @孔子             │    │
│  │                             │    │
│  │ 子路负米乃为孝名...         │    │
│  └─────────────────────────────┘    │
│                                     │
│   🏁 结辩                          │
│   ...                               │
│   🗳️ 投票                          │
│   ...                               │
│                                     │
│   ═══════════════════════════════    │
│                                     │
│   📊 票数统计                       │
│   ┌──────────────────────────┐     │
│   │ 王阳明  2票  孔子, 老子   │     │
│   │ 韩非    1票  王阳明      │     │
│   │ 🏆 最佳论点：王阳明      │     │
│   │ 🎯 最佳质询：孔子        │     │
│   └──────────────────────────┘     │
│                                     │
│   📝 裁判总结                       │
│   这场辩论从四个学派视角探讨了...    │
│                                     │
└─────────────────────────────────────┘
```

**PDF CSS 样式规范**：

```python
# debate/service/pdf_generator.py

PDF_STYLES = """
@page {
    margin: 24px 32px;
}

body {
    font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 12px;
    line-height: 1.7;
    color: #2c3e50;
}

/* 封面标题 */
.cover-title {
    text-align: center;
    margin: 16px 0 10px;
    font-size: 22px;
    font-weight: 700;
    color: #1a1a2e;
}

.cover-question {
    text-align: center;
    font-size: 15px;
    color: #34495e;
    margin-bottom: 16px;
    padding: 12px;
    border-top: 2px solid #f1c40f;
    border-bottom: 2px solid #f1c40f;
}

.cover-meta {
    text-align: center;
    font-size: 11px;
    color: #7f8c8d;
    margin-bottom: 20px;
}

/* 阶段标题 */
.phase-title {
    font-size: 16px;
    font-weight: 700;
    color: #1a1a2e;
    margin: 18px 0 10px;
    padding-bottom: 4px;
    border-bottom: 2px solid #f1c40f;
}

/* 消息卡片 */
.message-card {
    background: #f8f9fa;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 6px 0;
    border-left: 4px solid #3498db;
}

.message-card .speaker {
    font-weight: 700;
    font-size: 13px;
    color: #2c3e50;
    margin-bottom: 4px;
}

.message-card .speaker .school {
    font-weight: 400;
    font-size: 10px;
    color: #95a5a6;
    margin-left: 6px;
}

.message-card .target-label {
    font-size: 10px;
    color: #e74c3c;
    margin-bottom: 2px;
}

.message-card .content {
    font-size: 12px;
    line-height: 1.8;
}

.message-card .content p {
    margin: 2px 0;
}

/* 不同学派左边框颜色 */
.school-confucian  { border-left-color: #e74c3c; }
.school-daoist     { border-left-color: #2ecc71; }
.school-legalist   { border-left-color: #7f8c8d; }
.school-mohist     { border-left-color: #3498db; }
.school-mind       { border-left-color: #9b59b6; }
.school-military   { border-left-color: #e67e22; }
.school-synthesizer { border-left-color: #f1c40f; }

/* 裁判卡片特殊样式 */
.judge-card {
    background: linear-gradient(135deg, #fef9e7, #fdf2d0);
    border: 2px solid #f1c40f;
    border-radius: 6px;
    padding: 12px 16px;
    margin: 10px 0;
}

/* 票数统计表格 */
.vote-table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 12px;
}

.vote-table th {
    background: #f1c40f;
    color: #1a1a2e;
    padding: 6px 10px;
    text-align: left;
    font-weight: 700;
}

.vote-table td {
    padding: 6px 10px;
    border-bottom: 1px solid #ecf0f1;
}

.vote-table .winner-row {
    background: #fef9e7;
    font-weight: 700;
}

/* 获奖徽章 */
.award-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 11px;
    font-weight: 700;
    margin: 2px;
}

.award-best-argument {
    background: #f1c40f;
    color: #1a1a2e;
}

.award-best-cross {
    background: #3498db;
    color: white;
}

/* 裁判总结 */
.judge-summary {
    margin: 14px 0;
}

.judge-summary h2 {
    font-size: 15px;
    color: #1a1a2e;
    margin: 12px 0 6px;
}

.judge-summary table {
    width: 100%;
    border-collapse: collapse;
    margin: 6px 0;
}

.judge-summary table th,
.judge-summary table td {
    border: 1px solid #ddd;
    padding: 4px 8px;
    font-size: 11px;
}

/* 页脚分隔线 */
.section-divider {
    border: none;
    border-top: 1px dashed #bdc3c7;
    margin: 16px 0;
}
"""
```

**后端 PDF 生成接口**：

```python
# debate/service/pdf_generator.py

import markdown
from weasyprint import HTML

class PdfGenerator:
    """将辩论 Markdown 记录转为美观的 PDF"""

    def generate(self, session_data: dict) -> bytes:
        """
        输入: 会话序列化数据（JSON）
        输出: PDF 二进制数据
        """
        # 1. 构建 HTML
        html = self._build_html(session_data)

        # 2. WeasyPrint 渲染 PDF
        pdf = HTML(string=html).write_pdf()

        return pdf

    def _build_html(self, session: dict) -> str:
        """构建带样式和结构化的 HTML"""
        # 将 Markdown 转为 HTML，并通过模板嵌入 CSS + 卡片结构
        ...
```

**前端导出按钮**（视图 2 done_banner + 视图 3）：

```html
<!-- 辩论结束横幅中的导出按钮 -->
<div class="export-actions">
  <button @click="exportPdf" class="btn-export-pdf">
    📄 导出 PDF
  </button>
  <button @click="exportMarkdown" class="btn-export-md">
    📝 导出 Markdown
  </button>
  <button @click="exportJson" class="btn-export-json">
    📋 导出 JSON
  </button>
</div>
```

```javascript
// PDF 导出：触发浏览器下载或在浏览器中预览
function exportPdf(sessionId) {
  // 方案1：直接下载
  window.open(`/api/debate/sessions/${sessionId}/export?format=pdf`);

  // 方案2：先在新标签页预览（Content-Disposition: inline），用户手动保存
  // window.open(`/api/debate/sessions/${sessionId}/export?format=pdf&disposition=inline`);
}
```
---

## 后端状态机设计

### 状态流转

```
                         START
                           │
                           ▼
                      ┌─ OPENING ──────────────────→ 所有辩者并行立论，推送给所有人
                      │
                      ▼
              ┌─ CROSS_EXAMINE ──────────────────→ 第 R 轮质询
              │      │
              │      ├─ CROSS_ASK    (辩者向其他辩者提问，并行)
              │      │       │
              │      │       ▼
              │      ├─ CROSS_ANSWER (被质询者回答，并行)
              │      │
              │      └─ 还有轮次？── 是 ──→ R+1，回到 CROSS_ASK
              │            │
              │            否
              │            ▼
              └─────── CLOSING ──────────────────→ 所有辩者并行结辩
                           │
                           ▼
                       VOTING ───────────────────→ 所有辩者并行投票
                           │
                           ▼
                     JUDGE_TALLY ────────────────→ 裁判统计票数+颁奖
                           │
                           ▼
                     JUDGE_SUMMARY ──────────────→ 裁判综合总结
                           │
                           ▼
                        COMPLETE
```

### 各阶段调度逻辑

#### OPENING（立论）

```
发起人: 后端自动
说话人: 每个辩者 → target: "all"（所有人）
并行度: 全部辩者并行调用 LLM
推送: 每个辩者立论完成后立即 SSE 推送，不等其他人

LLM prompt:
  system: {辩者 persona_full}
  user:   辩论问题：「{question}」
          请你从自身学派立场发表立论观点（200-400字）：
          1. 核心立场
          2. 2-3 个关键论据
          3. 论证前提/假设
          输出 Markdown 格式。
```

#### CROSS_EXAMINE（质询，可配置 1-N 轮）

每轮分两步，两步之间是串行的，但每步内部是并行的：

**步骤 1 — CROSS_ASK（提问）**：
```
发起人: 后端自动
说话人: 每个辩者 A → target: 每个其他辩者 B（1 对多提问）
并行度: 全部辩者并行调用 LLM
上下文: 传入所有辩者的立论内容
推送: 每个辩者生成的所有质询问题作为一条消息推送

LLM prompt:
  system: {辩者 A persona_full}
  user:   辩论问题：「{question}」
          以下是所有辩者的立论观点：
          {other_openings...}
          
          请你向每位其他辩者提出 1 个质询问题（共 N-1 个）：
          - 直击对方论证弱点、矛盾或未说明前提
          - 每个问题简洁有力（≤50字）
          - 格式：「@name：问题内容」
```

**步骤 2 — CROSS_ANSWER（回答）**：
```
发起人: 后端自动
说话人: 被质询的辩者 B → target: 提问的辩者 A（定向回答）
并行度: 每个 Q&A 对并行调用 LLM
上下文: 传入 B 的立论 + A 对 B 的质询问题
推送: 每个回答作为独立消息推送

LLM prompt:
  system: {辩者 B persona_full}
  user:   辩论问题：「{question}」
          你的立论：{B_opening}
          
          对方 @{A_name} 质询：{A_question}
          
          请正面回答（100-200字）：
          - 正面回应对手质疑
          - 可以坚持，也可以承认局限性
          - 保持角色风格
```

#### CLOSING（结辩）

```
发起人: 后端自动
说话人: 每个辩者 → target: "all"（所有人）
并行度: 全部辩者并行调用 LLM
上下文: 传入该辩者自己的立论 + 全部质询记录摘要
推送: 每个辩者结辩完成后立即 SSE 推送

LLM prompt:
  system: {辩者 persona_full}
  user:   辩论问题：「{question}」
          你的立论：{my_opening}
          质询过程：{all_cross_examinations_for_me}
          
          请发表结辩陈述（200-400字）：
          1. 重申或修正你的核心立场
          2. 回应质询中暴露的关键问题
          3. 你的立场相比其他人的独特价值
```

#### VOTING（投票）

```
发起人: 后端自动
说话人: 每个辩者 → target: "all"
并行度: 全部辩者并行调用 LLM
上下文: 传入完整辩论记录（立论+质询+结辩）
推送: 每个辩者投票完成后立即 SSE 推送

LLM prompt:
  system: {辩者 persona_full}
  user:   辩论问题：「{question}」
          完整辩论记录：{full_transcript}
          
          请投票给最有说服力的辩者（除自己外）：
          - 投票对象：{name}
          - 理由：哪个论点/论证方式最有说服力（50-100字）
          格式：「@name — 理由」
```

#### JUDGE_TALLY（裁判统计）

```
发起人: 后端自动
说话人: 裁判 → target: "all"
并行度: 1 次 LLM 调用
上下文: 传入完整辩论记录 + 投票结果
推送: 统计结果作为一条消息推送

LLM prompt:
  system: {裁判 persona_full}
  user:   辩论问题：「{question}」
          完整辩论记录：{full_transcript}
          投票记录：{all_votes}
          
          请统计：
          1. 票数分布（表格）
          2. 🏆 最佳论点奖：1名 + 理由
          3. 🎯 最佳质询奖：1名 + 理由
```

#### JUDGE_SUMMARY（裁判总结）

```
发起人: 后端自动
说话人: 裁判 → target: "all"
并行度: 1 次 LLM 调用
上下文: 传入完整辩论记录 + 投票 + 统计
推送: 总结作为最后一条消息推送

LLM prompt:
  system: {裁判 persona_full}
  user:   辩论问题：「{question}」
          完整辩论记录：{full_transcript}
          投票与统计：{tally_result}
          
          请做综合总结（500-800字）：
          1. 辩论概览（一句话）
          2. 各派观点摘要（表格）
          3. 共识点
          4. 分歧点（哪些根本分歧无法调和？为什么？）
          5. 核心洞见（超越各派立场的深层洞察）
          6. 未解决问题
          7. 裁判评语
```

---

## LLM 调用策略

### 并行与串行

```
OPENING:         N 个辩者 ── 全部并行
CROSS_ASK:       N 个辩者 ── 全部并行（每个辩者生成 N-1 个问题）
CROSS_ANSWER:    N×(N-1) 个 Q&A ── 全部并行
CLOSING:         N 个辩者 ── 全部并行
VOTING:          N 个辩者 ── 全部并行
JUDGE_TALLY:     1 次
JUDGE_SUMMARY:   1 次
```

阶段之间是串行的（必须等上阶段全部完成才能进入下一阶段），但阶段内部全部并行。

### 调用次数

公式：`N(立论) + R×[N+N×(N-1)](质询) + N(结辩) + N(投票) + 2(裁判)`

| 辩者数 | 质询轮次 | LLM 调用次数 |
|--------|---------|-------------|
| 2 | 1 | 2 + 4 + 2 + 2 + 2 = 12 |
| 3 | 1 | 3 + 9 + 3 + 3 + 2 = 20 |
| 4 | 1 | 4 + 16 + 4 + 4 + 2 = 30 |
| 5 | 1 | 5 + 25 + 5 + 5 + 2 = 42 |
| 4 | 2 | 4 + 32 + 4 + 4 + 2 = 46 |

### 超时处理

- 每个 LLM 调用超时：120 秒
- 阶段总超时：`max(并行数 × 120s, 300s)`
- 超时的辩者跳过（推送 error 事件），不影响其他辩者

---

## 后端目录结构

```
backend/debate/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── routes.py              # 3 个端点 + SSE
│   └── schemas.py             # Pydantic 模型
├── service/
│   ├── __init__.py
│   └── debate_service.py      # 辩论编排（状态机 + SSE 推送）
├── agent/
│   ├── __init__.py
│   └── debate_agent.py        # LLM 调用封装（复用 BaseAgent）
├── state/
│   ├── __init__.py
│   └── machine.py             # 状态机定义 + 状态流转
├── prompts/
│   ├── __init__.py            # load_prompt() 工具函数
│   ├── config/
│   │   └── prompt.py          # PromptConfig 常量 + 索引
│   ├── roles/                 # ← 角色 prompt（每个角色一个 .md 文件）
│   │   ├── debater/
│   │   │   ├── confucius.md   # 孔子
│   │   │   ├── mencius.md     # 孟子
│   │   │   ├── laozi.md       # 老子
│   │   │   ├── zhuangzi.md    # 庄子
│   │   │   ├── hanfei.md      # 韩非
│   │   │   ├── wangyangming.md# 王阳明
│   │   │   ├── sunzi.md       # 孙子
│   │   │   ├── zhuxi.md       # 朱熹
│   │   │   ├── mozi.md        # 墨子（辩者）
│   │   │   └── index.json     # 辩者索引（id, name, school, avatar, persona_short）
│   │   └── judge/
│   │       ├── mozi.md        # 墨子（裁判）
│   │       ├── modern_philosopher.md  # 现代哲学家
│   │       └── index.json     # 裁判索引
│   ├── opening.md             # 立论 task prompt
│   ├── cross_ask.md           # 质询提问 task prompt
│   ├── cross_answer.md        # 质询回答 task prompt
│   ├── closing.md             # 结辩 task prompt
│   ├── vote.md                # 投票 task prompt
│   ├── judge_tally.md         # 裁判统计 task prompt
│   └── judge_summary.md       # 裁判总结 task prompt
├── config/
│   ├── __init__.py
│   └── settings.py            # debate 模块配置
└── session/
    ├── __init__.py
    ├── store.py               # 会话存储（内存 + 持久化）
    └── archive/               # 已完成的辩论存档（JSON 文件，gitignore）
```

### 角色 prompt 文件组织

每个角色一个 `.md` 文件，存放在 `prompts/roles/{type}/` 目录下。文件内容就是该角色的 `persona_full`（直接作为 LLM system prompt）。

每个目录下有一个 `index.json`，提供轻量索引（`persona_short` + 元信息），供 `GET /api/debate/roles` 接口返回。

**辩者 prompt 示例** (`prompts/roles/debater/confucius.md`)：

```markdown
你是孔子，儒家学派创始人。

## 核心主张
你主张"仁"为核心、"礼"为规范、中庸为方法论。
你相信人性可塑，教化使人向善，社会应恢复周礼秩序。

## 论证风格
温和而坚定，善引《诗经》《尚书》和尧舜禹典故。

## 语气
循循善诱，以"子曰"开头，多用设问和比喻。
```

**辩者索引** (`prompts/roles/debater/index.json`)：

```json
[
  {
    "id": "confucius",
    "name": "孔子",
    "school": "儒家",
    "avatar": "🎭",
    "persona_short": "仁爱礼治，中庸之道，以周礼为理想秩序"
  },
  {
    "id": "mencius",
    "name": "孟子",
    "school": "儒家",
    "avatar": "🎭",
    "persona_short": "性善论，民本思想，王道政治"
  }
]
```

**裁判 prompt 示例** (`prompts/roles/judge/mozi.md`)：

```markdown
你是墨子，本次辩论的裁判。你不参与辩论，只做评判和总结。

## 评判原则
你以逻辑严谨著称，重视论证的一致性、清晰性和实践可行性。

## 评判标准
- 论点是否自洽？
- 论据是否可靠？
- 论证是否严密？

## 语气
客观、冷静，以"裁判曰"开头。
```

**加载方式**：

后端在立论/质询/结辩等阶段，按 `debater_id` 加载对应的角色 `.md` 文件作为 system prompt，再拼接阶段 task prompt 作为 user prompt。加载复用项目已有的 `load_prompt()` 函数：

```python
from trip_plan.prompts import load_prompt

# 加载角色 system prompt
role_prompt = load_prompt(f"roles/debater/{debater_id}")  # → prompts/roles/debater/confucius.md

# 加载阶段 task prompt
task_prompt = load_prompt("opening")  # → prompts/opening.md
```

---

## 会话存储设计

### 总体思路

会话存储是**内存级**的，不做持久化（项目不引入数据库）。每个辩论会话生命周期内，后端维护完整的辩论记录，供各阶段 LLM 调用时作为上下文。辩论结束后保留 30 分钟可查询，超时自动清除。

### Session 数据结构

```python
# session/store.py

@dataclass
class Message:
    """一条辩论消息"""
    id: str                    # 消息唯一 ID
    timestamp: float           # Unix 时间戳
    phase: str                 # opening / cross_examine / closing / voting / judge_tally / judge_summary
    speaker_id: str            # 发言人 ID
    speaker_name: str          # 发言人名称
    speaker_role: str          # user / debater / judge
    target_id: str             # 说话对象 ID，"all" 表示所有人
    target_name: str           # 说话对象名称
    content: str               # 完整发言内容


@dataclass
class DebateSession:
    """一场辩论的完整会话"""
    session_id: str                          # 唯一会话 ID
    question: str                            # 辩论问题
    config: DebateConfig                     # 辩者 + 裁判 + 质询轮次配置
    status: str                              # starting / running / completed / error
    created_at: float                        # 创建时间
    
    # 状态机
    current_phase: str | None                # 当前阶段
    current_round: int                       # 当前质询轮次（质询阶段用）
    
    # 全文记录（按发送时间排序）
    messages: list[Message]                  # 所有消息
    
    # 阶段产出物（结构化的，方便后续阶段取用）
    openings: dict[str, Message]             # debater_id → opening message
    cross_examinations: list[CrossQA]        # 质询问答对
    closings: dict[str, Message]             # debater_id → closing message
    votes: list[VoteResult]                  # 投票记录
    tally_result: Message | None             # 裁判统计消息
    summary: Message | None                  # 裁判总结消息


@dataclass
class CrossQA:
    """一对质询问答"""
    round: int
    asker_id: str          # 提问辩者
    answerer_id: str       # 回答辩者
    ask_message: Message   # 质询问题消息
    answer_message: Message | None  # 质询回答（可能为 None，超时等）


@dataclass
class VoteResult:
    """一条投票记录"""
    voter_id: str          # 投票人
    vote_for_id: str       # 投票对象
    reason: str            # 投票理由
    message: Message       # 投票消息


@dataclass
class DebateConfig:
    """辩论配置"""
    question: str
    debaters: list[DebaterRole]
    judge: JudgeRole
    cross_examination_rounds: int
```

### SessionStore 接口

```python
# session/store.py

class SessionStore:
    """会话存储管理器（单例）"""
    
    _sessions: dict[str, DebateSession]     # 活跃会话
    _ttl_seconds: int = 1800                # 30 分钟过期
    
    def create(self, config: DebateConfig) -> DebateSession:
        """创建新会话，返回 session_id"""
    
    def get(self, session_id: str) -> DebateSession | None:
        """获取会话，不存在或已过期返回 None"""
    
    def add_message(self, session_id: str, message: Message) -> None:
        """追加一条消息到会话记录"""
    
    def get_messages_by_phase(self, session_id: str, phase: str) -> list[Message]:
        """按阶段查询消息"""
    
    def get_all_messages(self, session_id: str) -> list[Message]:
        """获取全部消息（按时间排序）"""
    
    def get_full_transcript(self, session_id: str) -> str:
        """生成全文记录文本，用于 LLM 上下文"""
    
    def update_phase(self, session_id: str, phase: str) -> None:
        """更新当前阶段"""
    
    def cleanup_expired(self) -> None:
        """清除过期会话（可定时调用）"""
```

### 各阶段取上下文策略

不同阶段的 LLM 调用需要不同的上下文窗口。不是把所有消息都塞进去，按需裁剪：

| 阶段 | 传什么上下文 | 说明 |
|------|-------------|------|
| **立论** | `{question}` | 只需要问题，不需要看别人的立论 |
| **质询提问** | `{question}` + 所有辩者的立论 (`openings`) | 看到所有立论才能针对性提问 |
| **质询回答** | `{question}` + 自己的立论 + 对方的质询问题 | 只需这一条 Q&A 对 |
| **结辩** | `{question}` + 自己的立论 + 所有被质询和质询过的 Q&A | 只看与自己相关的质询 |
| **投票** | `{question}` + 全部消息（full_transcript） | 需要全局视野 |
| **裁判统计** | `{question}` + 全部消息 + 投票记录 | 全局视野 |
| **裁判总结** | `{question}` + 全部消息 + 投票 + 统计 | 全局视野 |

### 全文记录生成

```python
def get_full_transcript(self, session_id: str) -> str:
    """生成 LLM 可读的辩论全文记录"""
    session = self._sessions[session_id]
    lines = [f"# 辩论主题：{session.config.question}\n"]
    
    phase_labels = {
        "opening": "📜 立论",
        "cross_examine": "⚔️ 质询",
        "closing": "🏁 结辩",
        "voting": "🗳️ 投票",
        "judge_tally": "📊 裁判统计",
        "judge_summary": "📝 裁判总结",
    }
    
    for msg in session.messages:
        target = f" → @{msg.target_name}" if msg.target_id != "all" else ""
        lines.append(
            f"[{phase_labels.get(msg.phase, msg.phase)}] "
            f"{msg.speaker_name}（{msg.speaker_role}）{target}：\n"
            f"{msg.content}\n"
        )
    
    return "\n".join(lines)
```

### 断线重连处理

SSE 断开后前端重连同一 session_id。后端需要知道前端错过了什么：

```python
# 方案：前端重连时带上最后收到的 message_id
# GET /api/debate/stream/{session_id}?last_msg_id=msg_xxx

def resume_stream(self, session_id: str, last_msg_id: str | None):
    """断线重连时，先补发错过的消息，再恢复正常流式推送"""
    if last_msg_id:
        missed = self._get_messages_after(session_id, last_msg_id)
        for msg in missed:
            yield self._build_replay_event(msg)
    # 继续从当前阶段推送
    yield from self._continue_stream(session_id)
```

重连时使用 `message_start` + `message_delta`（一次性补发完整 content）+ `message_end` 补发错过的消息。不会显示打字机效果（已经生成完了），直接渲染完整气泡。

如果当前阶段正在进行（有辩者在发言中），重连后的前端仍然能收到正在发言的后续 `message_delta`。

### 内存估算

以 4 辩者 1 轮质询为例：约 20 条消息，每条消息 content 约 200-500 字。单个会话约 50-100KB。100 个并发会话约 10MB——内存完全够用，不需要 Redis。

### 持久化存储

辩论结束后，后端将会话记录序列化为 JSON 文件保存到本地文件系统。内存中的会话在 30 分钟后清理，但持久化文件长期保留。

**存储路径**：`backend/debate/sessions/archive/{session_id}.json`

**持久化时机**：辩论状态变为 `completed` 或 SSE 连接断开 5 分钟后（防止前端断线）。

**存储内容**：完整的 `DebateSession` 序列化，包含所有消息、结构化阶段记录、投票和裁判总结。

```python
# session/store.py 中持久化相关方法

class SessionStore:
    
    _archive_dir: str = "backend/debate/sessions/archive/"
    
    def persist(self, session_id: str) -> str:
        """将完成后的会话序列化到磁盘，返回文件路径"""
        session = self._sessions.get(session_id)
        if not session or session.status not in ("completed",):
            raise ValueError("只能持久化已完成的会话")
        
        data = self._serialize_session(session)
        path = f"{self._archive_dir}{session_id}.json"
        os.makedirs(self._archive_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path
    
    def load_archived(self, session_id: str) -> dict | None:
        """从磁盘加载已存档会话（用于导出接口）"""
        path = f"{self._archive_dir}{session_id}.json"
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def list_archived(self, limit: int = 50) -> list[dict]:
        """列出最近存档的会话摘要"""
        summaries = []
        archive_dir = Path(self._archive_dir)
        if not archive_dir.exists():
            return []
        for f in sorted(archive_dir.glob("*.json"), key=os.path.getmtime, reverse=True)[:limit]:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            summaries.append({
                "session_id": data["session_id"],
                "question": data["question"],
                "status": data["status"],
                "created_at": data["created_at"],
                "debater_count": len(data["config"]["debaters"]),
                "judge": data["config"]["judge"]["name"],
            })
        return summaries
```

### 导出与存档流程图

```
辩论完成（done 事件推送后）
      │
      ├── 1. SessionStore.persist(session_id) → 写 JSON 到磁盘
      │
      ├── 2. 用户前端：
      │      ├── [导出 Markdown] → GET /api/debate/sessions/{id}/export?format=md
      │      │                     → 后端读取存档 JSON，渲染 Markdown，返回文件下载
      │      ├── [导出 JSON]    → GET /api/debate/sessions/{id}/export?format=json
      │      │                     → 后端直接返回存档 JSON 文件下载
      │      └── [浏览存档]     → 前端展示完整辩论（视图3 结果摘要）
      │                          → 数据来源：GET /api/debate/sessions/{id}
      │
      └── 3. 内存会话 30 分钟后过期清理（磁盘存档不受影响）
```

### 过期清理

```python
# 每次 create() 时触发一次宽松的清理
def _maybe_cleanup(self):
    now = time.time()
    expired = [
        sid for sid, s in self._sessions.items()
        if now - s.created_at > self._ttl_seconds
    ]
    for sid in expired:
        del self._sessions[sid]
```

---

## 前端设计

### 技术选型

- **框架**：Vue 3 + Vite（与现有项目一致）
- **UI 风格**：类聊天应用（微信/Telegram 风格），深色模式优先
- **SSE 客户端**：原生 `EventSource` 或轻量封装
- **Markdown 渲染**：`marked` + `highlight.js`（辩者发言可能含列表、引用等）

### 页面设计

#### 页面结构（单页应用，3 个视图）

```
┌──────────────────────────────────────────────────┐
│  Debate App                                       │
│                                                    │
│  ┌─ 视图1：辩论配置 ────────────────────────────┐  │
│  │  选择辩者 + 裁判 + 输入问题 + 开始辩论         │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌─ 视图2：聊天室 ──────────────────────────────┐  │
│  │  ┌─ 顶栏：辩论标题 + 在线辩者头像列表 ─────┐  │  │
│  │  ├─ 消息区：滚动消息列表 ──────────────────┤  │  │
│  │  │  ├── phase_banner（阶段分隔条）          │  │  │
│  │  │  ├── chat_bubble（辩者发言气泡）        │  │  │
│  │  │  ├── chat_bubble（另一辩者，并行打字）  │  │  │
│  │  │  ├── ...                                │  │  │
│  │  │  └── judge_bubble（裁判发言，特殊样式） │  │  │
│  │  └──────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌─ 视图3：结果摘要 ────────────────────────────┐  │
│  │  获胜者 + 票数 + 完整摘要（Markdown 渲染）      │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### 视图 1：辩论配置（DebateSetup）

**功能**：用户配置辩论参数并启动

**布局**：
```
┌────────────────────────────────────────┐
│  🎭 多Agent辩论                        │
│                                        │
│  辩论问题                               │
│  ┌────────────────────────────────────┐│
│  │ 输入你的问题...                     ││
│  └────────────────────────────────────┘│
│                                        │
│  选择辩者（2-5人）         已选: 3     │
│  ┌────────────────────────────────────┐│
│  │ ┌──────────────────────────────┐   ││
│  │ │ 🔍 搜索角色...               │   ││
│  │ ├──────────────────────────────┤   ││
│  │ │ 📁 中国古典哲学 (8)          │   ││
│  │ │   ○ 孔子  儒家  春秋         │   ││
│  │ │   ● 孟子  儒家  战国   ✓已选 │   ││
│  │ │   ○ 老子  道家  春秋         │   ││
│  │ │   ○ 庄子  道家  战国         │   ││
│  │ │   ○ 韩非  法家  战国          │   ││
│  │ │   ...                         │   ││
│  │ │ 📁 西方古典哲学 (3)  [折叠]   │   ││
│  │ │ 📁 经济学 (3)        [折叠]   │   ││
│  │ │ 📁 学科全集大成者 (10)[折叠]  │   ││
│  │ │ ...                          │   ││
│  │ └──────────────────────────────┘   ││
│  └────────────────────────────────────┘│
│                                        │
│  选择裁判                   已选: 1    │
│  ┌────────────────────────────────────┐│
│  │ ● 中立分析者                        ││
│  │ ○ 苏格拉底式裁判                    ││
│  └────────────────────────────────────┘│
│                                        │
│  质询轮次:  [1]  (1-3)                │
│                                        │
│  ┌──────────┐                          │
│  │ 开始辩论  │  (辩者≥2 才可点击)      │
│  └──────────┘                          │
└────────────────────────────────────────┘
```

**交互细节**：
- 角色列表按分类折叠，默认展开"中国古典哲学"
- 支持搜索（姓名、学派、时期模糊匹配）
- 每个角色显示：头像 emoji + 姓名 + 学派 + 时期 + 一句话简介
- 已选角色高亮，再次点击取消
- 辩者最少 2 人，最多 5 人
- "开始辩论"调用 `POST /api/debate/start`，成功后跳转视图 2

### 视图 2：聊天室（DebateChat）

**功能**：实时展示辩论过程，所有发言以聊天消息形式呈现

**布局**：
```
┌──────────────────────────────────────────┐
│ ← 返回   人之初性本善还是性本恶？   👤🎭🎭🎭⚖️│ ← 顶栏（sticky）
├──────────────────────────────────────────┤
│                                          │
│ ───── 📜 立论 ──────────────────────────│ ← phase_banner
│                                          │
│  ┌─────────────────────────────────┐     │
│  │ 🎭 孔子 · 儒家                    │     │ ← 头像 + 名称 + 学派
│  │ ┌─────────────────────────────┐  │     │
│  │ │ 子曰：性相近也，习相远也...  │  │     │ ← 气泡（正在逐字增长）
│  │ └─────────────────────────────┘  │     │
│  └─────────────────────────────────┘     │
│                                          │
│  ┌─────────────────────────────────┐     │
│  │ 🎭 韩非 · 法家                    │     │
│  │ ┌─────────────────────────────┐  │     │
│  │ │ 韩非曰：人皆挟自为心...      │  │     │ ← 另一个气泡（同时逐字增长）
│  │ └── 正在输入... ──────────────┘  │     │
│  └─────────────────────────────────┘     │
│                                          │
│ ───── ⚔️ 质询 · 第 1 轮 ────────────────│ ← phase_banner
│                                          │
│  ┌─────────────────────────────────┐     │
│  │ 🎭 孔子 → @韩非                  │     │ ← 定向发言标注
│  │ ┌─────────────────────────────┐  │     │
│  │ │ 若人性果真好利恶害，         │  │     │
│  │ │ 何以解释子路负米、           │  │     │
│  │ │ 曾子易箦之行为？            │  │     │
│  │ └─────────────────────────────┘  │     │
│  └─────────────────────────────────┘     │
│                                          │
│  ┌─────────────────────────────────┐     │
│  │ 🎭 韩非 → @孔子                  │     │ ← 回答
│  │ ┌─────────────────────────────┐  │     │
│  │ │ 子路负米乃为孝名，           │  │     │
│  │ │ 曾子易箦恰证明了            │  │     │
│  │ │ 奖惩机制的内化...           │  │     │
│  │ └─────────────────────────────┘  │     │
│  └─────────────────────────────────┘     │
│                                          │
│ ───── 🏁 结辩 ──────────────────────────│
│  ...                                     │
│                                          │
│ ───── 🗳️ 投票 ──────────────────────────│
│  ...                                     │
│                                          │
│ ───── ⚖️ 裁判总结 ──────────────────────│
│  ┌─────────────────────────────────┐     │
│  │ ⚖️ 中立分析者                    │     │ ← 裁判特殊样式（金色边框）
│  │ ┌─────────────────────────────┐  │     │
│  │ │ # 辩论总结                   │  │     │
│  │ │                              │  │     │
│  │ │ ## 辩论概览                  │  │     │
│  │ │ ...                          │  │     │
│  │ │ ## 核心洞见                  │  │     │
│  │ │ ...                          │  │     │
│  │ └─────────────────────────────┘  │     │
│  └─────────────────────────────────┘     │
│                                          │
│  ┌────────── 辩论结束 ──────────────┐    │ ← done_banner
│  │  🏆 王阳明 胜出（2票）            │    │
│  │  [查看完整总结]                   │    │
│  └──────────────────────────────────┘    │
│                                          │
├──────────────────────────────────────────┤
│  [自动滚动]  [跳至底部 ▼]               │ ← 底栏
└──────────────────────────────────────────┘
```

**交互细节**：

| 元素 | 行为 |
|------|------|
| **顶栏** | 辩论问题（截断）+ 参与者头像列表（在线状态圆点：绿=正在发言，灰=已结束） |
| **phase_banner** | 半透明分隔条，居中文字 + icon，进入新阶段时滑入动画 |
| **chat_bubble 辩者** | 左对齐，头像 + 姓名·学派 + 气泡（圆角矩形，该学派主题色边框），Markdown 渲染 |
| **chat_bubble 定向发言** | 气泡上方标注"@目标角色名"，目标角色名高亮 |
| **chat_bubble 裁判** | 居中/特殊样式，金色边框，`⚖️` 前缀，与辩者气泡明显区分 |
| **打字机效果** | `message_delta` 到达时，气泡内文字逐字追加，光标闪烁（`▌`），`message_end` 时光标消失 |
| **并行打字** | 多个气泡同时逐字增长，互不影响 |
| **自动滚动** | 有新消息时自动滚到底部；用户手动上滚时暂停自动滚动，显示"跳至底部"按钮 |
| **正在输入指示** | `message_start` 后、第一个 `message_delta` 到达前，气泡内显示"...正在输入..." |
| **done_banner** | 辩论结束时最后一条消息后插入，显示获胜者 + 票数 + 跳转按钮 |

**消息气泡样式规范**：

```css
/* 辩者气泡通用 */
.bubble-debater {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 18px;
  border-left: 3px solid var(--school-color);
  background: var(--bubble-bg);
}

/* 学派主题色 */
.school-confucian  { --school-color: #e74c3c; }  /* 儒家 · 红 */
.school-daoist     { --school-color: #2ecc71; }  /* 道家 · 绿 */
.school-legalist   { --school-color: #7f8c8d; }  /* 法家 · 灰 */
.school-mohist     { --school-color: #3498db; }  /* 墨家 · 蓝 */
.school-mind       { --school-color: #9b59b6; }  /* 心学 · 紫 */
/* ... 更多学派 */

/* 裁判气泡特殊样式 */
.bubble-judge {
  max-width: 85%;
  padding: 16px 20px;
  border: 2px solid #f1c40f;
  border-radius: 12px;
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  margin: 0 auto;
}

/* 定向发言标注 */
.target-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}
.target-label .target-name {
  color: var(--school-color);
  font-weight: 600;
}

/* 打字光标 */
.typing-cursor::after {
  content: "▌";
  animation: blink 1s infinite;
}
.typing-done::after {
  content: "";
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 正在输入 */
.typing-indicator {
  color: var(--text-tertiary);
  font-style: italic;
  animation: pulse 1.5s infinite;
}
```

### 视图 3：结果摘要（DebateResult）

**功能**：辩论结束后展示完整总结

**布局**：
```
┌──────────────────────────────────────────┐
│  ← 返回聊天室    辩论结果                │
├──────────────────────────────────────────┤
│                                          │
│        🏆 王阳明 胜出                     │
│        获得 2 票                          │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ 票数统计                            │  │
│  │ 王阳明  2票  ← 孔子, 老子           │  │
│  │ 韩非    1票  ← 王阳明               │  │
│  │ 老子    0票                          │  │
│  │ 🏆 最佳论点奖：韩非                  │  │
│  │ 🎯 最佳质询奖：孔子                  │  │
│  └────────────────────────────────────┘  │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ 裁判总结（Markdown 渲染）            │  │
│  │                                    │  │
│  │ # 辩论总结：人之初性本善还是性本恶？ │  │
│  │                                    │  │
│  │ ## 辩论概览                         │  │
│  │ 这是一场关于...                     │  │
│  │                                    │  │
│  │ ## 各派观点摘要                     │  │
│  │ | 辩者 | 核心立场 |                 │  │
│  │ |------|----------|                 │  │
│  │ | 孔子 | 性无善恶...|               │  │
│  │ ...                                │  │
│  │                                    │  │
│  │ ## 共识点                           │  │
│  │ ## 分歧点                           │  │
│  │ ## 核心洞见                         │  │
│  │ ## 未解决问题                       │  │
│  │ ## 裁判评语                         │  │
│  └────────────────────────────────────┘  │
│                                          │
│  [开始新一轮辩论]                        │
└──────────────────────────────────────────┘
```

### 路由设计

```javascript
// router/index.js
const routes = [
  {
    path: '/',
    name: 'debate-setup',
    component: DebateSetupView,
  },
  {
    path: '/debate/:sessionId',
    name: 'debate-chat',
    component: DebateChatView,
    props: true,
  },
  {
    path: '/debate/:sessionId/result',
    name: 'debate-result',
    component: DebateResultView,
    props: true,
  },
];
```

### 组件树

```
App.vue
├── DebateSetupView.vue       # 视图1：辩论配置
│   ├── RoleSelector.vue      # 角色选择器（分类折叠 + 搜索 + 多选）
│   ├── JudgeSelector.vue     # 裁判选择器
│   └── QuestionInput.vue     # 问题输入 + 质询轮次 + 开始按钮
│
├── DebateChatView.vue        # 视图2：聊天室
│   ├── ChatTopBar.vue        # 顶栏（标题 + 参与者头像列表）
│   ├── ChatMessageList.vue   # 消息列表（滚动容器）
│   │   ├── PhaseBanner.vue   # 阶段分隔条
│   │   ├── ChatBubble.vue    # 通用消息气泡（根据 role 切换样式）
│   │   └── DoneBanner.vue    # 辩论结束横幅
│   └── ChatBottomBar.vue     # 底栏（自动滚动状态）
│
└── DebateResultView.vue      # 视图3：结果摘要
    ├── WinnerCard.vue        # 获胜者卡片
    ├── VoteTable.vue         # 票数统计 + 获奖
    ├── JudgeSummary.vue      # 裁判总结（Markdown 渲染）
    └── NewDebateButton.vue   # 新一轮辩论
```

### 数据流

```
DebateSetupView                DebateChatView                DebateResultView
      │                              │                              │
      │ POST /api/debate/start       │                              │
      │ {roles, judge, question}     │                              │
      ├──────────────────────────────►                              │
      │ ◄── {session_id, participants}                              │
      │                              │                              │
      ├─ router.push(/debate/:id) ──►                              │
      │                              │                              │
      │                   GET /api/debate/stream/:id (SSE)          │
      │                              │                              │
      │                    ◄── phase_change                         │
      │                    ◄── message_start → 创建气泡             │
      │                    ◄── message_delta → 追加文字（N次）      │
      │                    ◄── message_end   → 标记完成             │
      │                    ◄── done          → 跳转结果             │
      │                              │                              │
      │                              ├─ router.push(/debate/:id/result) ──►
      │                              │                              │
      │                              │              渲染 WinnerCard + VoteTable
      │                              │              + JudgeSummary (Markdown)
```

### 关键实现细节

**1. SSE 断线重连**：

```javascript
// DebateChatView.vue
let retryCount = 0;
const MAX_RETRY = 3;

function connectSSE(sessionId) {
  const es = new EventSource(`/api/debate/stream/${sessionId}`);

  es.onerror = () => {
    es.close();
    if (retryCount < MAX_RETRY) {
      retryCount++;
      showToast(`连接断开，正在重连 (${retryCount}/${MAX_RETRY})...`);
      setTimeout(() => connectSSE(sessionId), 2000 * retryCount);
    } else {
      showToast('连接失败，请刷新页面重试');
    }
  };

  es.addEventListener('open', () => {
    retryCount = 0;
  });

  // ... message_start, message_delta, message_end, phase_change, done
}
```

**2. 多气泡并行追加**：

```javascript
const bubbles = reactive(new Map());  // id → { speaker, target, content, done }

function onMessageDelta({ id, delta }) {
  const bubble = bubbles.get(id);
  if (bubble) {
    bubble.content += delta;
    bubble.done = false;
  }
}

function onMessageEnd({ id }) {
  const bubble = bubbles.get(id);
  if (bubble) {
    bubble.done = true;
  }
}
```

模板中按 Map 的插入顺序渲染，每个气泡独立绑定自己的 `content`，由于 Vue 3 响应式系统是细粒度的，修改一个气泡的 `content` 只触发该气泡的重新渲染，不影响其他气泡。

**3. Markdown 实时渲染**：

辩者发言可能含 Markdown（列表、引用、加粗等）。气泡内容在 `typing` 状态时显示纯文本 + 打字光标；`done` 后切换为 Markdown 渲染。也可以始终纯文本渲染（更轻量，看产品决定）。

**4. 角色颜色映射**：

```javascript
// 学派 → CSS 变量
const SCHOOL_COLORS = {
  '儒家': '#e74c3c',
  '道家': '#2ecc71',
  '法家': '#95a5a6',
  '墨家': '#3498db',
  '兵家': '#e67e22',
  '心学': '#9b59b6',
  '理学': '#1abc9c',
  '古希腊哲学': '#f39c12',
  '德国古典哲学': '#c0392b',
  '马克思主义': '#e74c3c',
  '政治现实主义': '#34495e',
  '社会契约论': '#2980b9',
  '自由主义': '#27ae60',
  '古典经济学': '#2c3e50',
  '凯恩斯主义': '#16a085',
  '奥地利学派': '#d4ac0d',
  '科学哲学': '#8e44ad',
  '政治哲学': '#2c3e50',
  '进化生物学': '#27ae60',
  '社会学': '#e67e22',
  '心理学': '#c0392b',
  '人类学': '#d35400',
  '语言学': '#2980b9',
  '传播学': '#8e44ad',
  '政治学': '#2c3e50',
  // 集大成者用金色
  '集大成者': '#f1c40f',
};
```

---

## 预设角色库（prompts/roles/ 目录）

所有角色 persona 存放在 `.md` 文件中，索引用 `.json` 文件。

### 设计原则

- **辩者**：覆盖各历史时期、各学科领域。每个辩者文件放在 `prompts/roles/debater/` 目录下
- **裁判**：始终中立，不持有任何学派立场。裁判文件放在 `prompts/roles/judge/` 目录下

### 辩者清单（28 个预设）

#### 中国古典哲学（先秦）

| 文件 | 角色 | 学派 | 时期 | 一句话 |
|------|------|------|------|--------|
| `confucius.md` | 孔子 | 儒家 | 春秋 | 仁爱礼治，中庸之道，以周礼为理想秩序 |
| `mencius.md` | 孟子 | 儒家 | 战国 | 性善论，民本思想，王道仁政 |
| `xunzi.md` | 荀子 | 儒家 | 战国 | 性恶论，化性起伪，隆礼重法 |
| `laozi.md` | 老子 | 道家 | 春秋 | 道法自然，无为而治，柔弱胜刚强 |
| `zhuangzi.md` | 庄子 | 道家 | 战国 | 逍遥游，齐物论，精神绝对自由 |
| `mozi.md` | 墨子 | 墨家 | 战国 | 兼爱非攻，节用尚贤，三表法逻辑论证 |
| `hanfei.md` | 韩非 | 法家 | 战国 | 法治主义，人性好利恶害，法术势结合 |
| `sunzi.md` | 孙子 | 兵家 | 春秋 | 知己知彼，虚实相生，不战而屈人之兵 |

#### 中国宋明理学

| 文件 | 角色 | 学派 | 时期 | 一句话 |
|------|------|------|------|--------|
| `zhuxi.md` | 朱熹 | 理学 | 南宋 | 格物致知，存天理灭人欲，理先气后 |
| `wangyangming.md` | 王阳明 | 心学 | 明代 | 知行合一，致良知，心外无物 |

#### 西方古典哲学

| 文件 | 角色 | 学派 | 时期 | 一句话 |
|------|------|------|------|--------|
| `socrates.md` | 苏格拉底 | 古希腊哲学 | 公元前5世纪 | 认识你自己，产婆术诘问，知识即美德 |
| `plato.md` | 柏拉图 | 古希腊哲学 | 公元前4世纪 | 理念论，哲人王，灵魂三分，洞穴隐喻 |
| `aristotle.md` | 亚里士多德 | 古希腊哲学 | 公元前4世纪 | 中庸之道（mesotes），目的论，逻辑学之父 |

#### 西方近代哲学

| 文件 | 角色 | 学派 | 时期 | 一句话 |
|------|------|------|------|--------|
| `kant.md` | 康德 | 德国古典哲学 | 18世纪 | 纯粹理性批判，道德律令，人为自然立法 |
| `hegel.md` | 黑格尔 | 德国古典哲学 | 19世纪 | 辩证法，绝对精神，主奴辩证，历史有目的 |
| `nietzsche.md` | 尼采 | 存在主义先驱 | 19世纪 | 上帝已死，超人哲学，权力意志，重估一切价值 |
| `marx.md` | 马克思 | 马克思主义 | 19世纪 | 历史唯物主义，阶级斗争，剩余价值，人的异化 |

#### 西方政治哲学

| 文件 | 角色 | 学派 | 时期 | 一句话 |
|------|------|------|------|--------|
| `machiavelli.md` | 马基雅维利 | 政治现实主义 | 16世纪 | 目的正当则手段正当，君主应兼具狮子与狐狸 |
| `hobbes.md` | 霍布斯 | 社会契约论 | 17世纪 | 自然状态是万人之敌，利维坦保障秩序 |
| `locke.md` | 洛克 | 自由主义 | 17世纪 | 天赋人权，财产权源于劳动，有限政府 |
| `rousseau.md` | 卢梭 | 社会契约论 | 18世纪 | 人生而自由却无往不在枷锁中，公意 |

#### 经济学

| 文件 | 角色 | 学派 | 时期 | 一句话 |
|------|------|------|------|--------|
| `adam_smith.md` | 亚当·斯密 | 古典经济学 | 18世纪 | 看不见的手，分工创造财富，理性自利 |
| `keynes.md` | 凯恩斯 | 凯恩斯主义 | 20世纪 | 有效需求不足，政府干预，财政刺激 |
| `hayek.md` | 哈耶克 | 奥地利学派 | 20世纪 | 自发秩序，价格信号，反对计划经济的致命自负 |

#### 社会科学

| 文件 | 角色 | 领域 | 时期 | 一句话 |
|------|------|------|------|--------|
| `durkheim.md` | 涂尔干 | 社会学 | 19世纪 | 社会事实，有机团结，失范（anomie），集体意识 |
| `bourdieu.md` | 布迪厄 | 社会学 | 20世纪 | 场域（field），惯习（habitus），文化资本，符号暴力 |
| `goffman.md` | 戈夫曼 | 社会学 | 20世纪 | 拟剧论，污名，全控机构，日常生活中的自我呈现 |
| `freud.md` | 弗洛伊德 | 心理学 | 20世纪 | 无意识，本我自我超我，俄狄浦斯情结，压抑与升华 |
| `jung.md` | 荣格 | 心理学 | 20世纪 | 集体无意识，原型，人格类型，个体化 |
| `skinner.md` | 斯金纳 | 心理学 | 20世纪 | 操作条件反射，激进行为主义，自由与尊严的消解 |
| `piaget.md` | 皮亚杰 | 心理学 | 20世纪 | 认知发展阶段，图式-同化-顺应，发生认识论 |
| `levi_strauss.md` | 列维-斯特劳斯 | 人类学 | 20世纪 | 结构主义人类学，二元对立，神话逻辑，生的与熟的 |
| `geertz.md` | 格尔茨 | 人类学 | 20世纪 | 深描（thick description），文化解释，地方性知识 |
| `chomsky.md` | 乔姆斯基 | 语言学 | 20世纪 | 普遍语法，生成语言学，深层-表层结构，语言与自由 |
| `mcluhan.md` | 麦克卢汉 | 传播学 | 20世纪 | 媒介即讯息，热媒介与冷媒介，地球村 |
| `huntington.md` | 亨廷顿 | 政治学 | 20世纪 | 文明冲突论，政治秩序，民主化浪潮 |
| `fukuyama.md` | 福山 | 政治学 | 20世纪 | 历史终结论，信任与社会资本，身份政治 |

#### 现代哲学与科学

| 文件 | 角色 | 学派 | 时期 | 一句话 |
|------|------|------|------|--------|
| `popper.md` | 波普尔 | 科学哲学 | 20世纪 | 证伪主义，开放社会，反对历史决定论 |
| `rawls.md` | 罗尔斯 | 政治哲学 | 20世纪 | 正义即公平，无知之幕，差别原则 |
| `dawkins.md` | 道金斯 | 进化生物学 | 20世纪 | 自私的基因，模因（meme），盲眼钟表匠 |

#### 跨学科思想家

| 文件 | 角色 | 学派/领域 | 时期 | 一句话 |
|------|------|------|------|--------|
| `arendt.md` | 汉娜·阿伦特 | 政治哲学+历史学 | 20世纪 | 极权主义起源，平庸之恶，积极生活（vita activa） |
| `foucault.md` | 福柯 | 哲学+历史学+社会学 | 20世纪 | 知识-权力，规训社会，话语分析，现代性批判 |
| `weber.md` | 马克斯·韦伯 | 社会学+经济学+宗教学 | 20世纪 | 新教伦理与资本主义精神，科层制，价值中立 |
| `kahneman.md` | 丹尼尔·卡尼曼 | 心理学+行为经济学 | 21世纪 | 系统1与系统2，前景理论，认知偏误，噪声 |

#### 自定义角色（组合学派）

| 文件 | 角色 | 学派/领域 | 一句话 |
|------|------|------|--------|
| `daoist_ecologist.md` | 道家生态主义者 | 道家+深层生态学 | 道法自然 + 生态中心主义，批判人类中心论和工业文明 |
| `confucian_liberal.md` | 儒家自由主义者 | 儒家+自由主义 | 仁义礼智 + 个人权利，试图融合东亚伦理与宪政民主 |
| `buddhist_neuroscientist.md` | 佛学神经科学家 | 佛学+认知神经科学 | 无我（anatta）+ 意识科学研究，以第一人称经验对话第三人称数据 |
| `techno_skeptic.md` | 技术怀疑论者 | 技术哲学+人文主义 | 质疑"技术解决一切"的叙事，强调不可量化的人文价值 |
| `systems_thinker.md` | 系统思维者 | 系统论+复杂性科学 | 非线性因果，涌现，反馈循环，反对还原论思维 |

#### 学科全集大成者

每个学科一位"全能角色"，融汇该学科各家思想，能灵活调用不同流派来论证或反驳。不是某个具体历史人物，而是该领域的综合代言人。

| 文件 | 角色 | 融合内容 | 一句话 |
|------|------|----------|--------|
| `confucian_synthesizer.md` | 儒家集大成者 | 孔子仁学+孟子性善/民本+荀子性恶/礼法+朱熹理学+王阳明心学 | 贯通儒家两千年，从仁礼到心性，从内圣到外王，可调用任一分支 |
| `daoist_synthesizer.md` | 道家集大成者 | 老子道论+庄子逍遥+黄老之术+魏晋玄学+道教内丹 | 贯通道家各支，从宇宙本源到个体解脱，从无为而治到生命修炼 |
| `western_philosophy_synthesizer.md` | 西方哲学集大成者 | 古希腊形而上学+大陆理性主义+英国经验论+德国观念论+分析哲学+欧陆哲学 | 贯通西方哲学三千年，从柏拉图洞穴到维特根斯坦语言游戏 |
| `political_philosophy_synthesizer.md` | 政治哲学集大成者 | 古典共和+社会契约论+自由主义+马克思主义+社群主义+共和主义 | 贯通政治思想史，从亚里士多德政体分类到罗尔斯无知之幕 |
| `economic_synthesizer.md` | 经济学集大成者 | 古典经济学+马克思政治经济学+边际革命+凯恩斯主义+奥地利学派+行为经济学 | 贯通经济学各派，从斯密看不见的手到卡尼曼认知偏误 |
| `sociology_synthesizer.md` | 社会学集大成者 | 涂尔干功能主义+韦伯解释社会学+马克思冲突论+布迪厄场域论+戈夫曼拟剧论 | 贯通社会学各范式，从社会事实到符号互动 |
| `psychology_synthesizer.md` | 心理学集大成者 | 精神分析+行为主义+人本主义+认知心理学+进化心理学+社会心理学 | 贯通心理学各派，从弗洛伊德无意识到卡尼曼双系统 |
| `anthropology_synthesizer.md` | 人类学集大成者 | 进化论学派+文化相对主义+结构主义+象征人类学+反思人类学 | 贯通人类学各范式，从泰勒万物有灵论到格尔茨深描 |
| `political_science_synthesizer.md` | 政治学集大成者 | 制度主义+行为主义+理性选择+文明冲突论+民主化理论+身份政治 | 贯通政治学各范式，从亚里士多德到亨廷顿与福山 |
| `science_synthesizer.md` | 科学哲学集大成者 | 逻辑实证主义+证伪主义+范式革命+科学知识社会学（SSK）+科学实在论 | 贯通科学哲学各派，从波普尔证伪到库恩范式不可通约 |

### 裁判清单（2 个，始终中立）

| 文件 | 角色 | 一句话 |
|------|------|--------|
| `neutral_analyst.md` | 中立分析者 | 逻辑严谨，概念清晰，以论证质量和证据可靠性为唯一评判标准 |
| `socratic_judge.md` | 苏格拉底式裁判 | 以诘问法检验论证一致性，揭示隐含前提和逻辑漏洞 |

### 角色 .md 文件格式

每个角色 `.md` 文件内容直接作为该角色的 **system prompt**。

**辩者格式**：
```markdown
你是{角色名}，{学派/领域}的代表人物（{时期}）。

## 核心主张
{2-3 句核心思想描述}

## 论证风格
{论证特点和偏好}

## 语气
{具体语气描述}
```

**裁判格式**（强调中立）：
```markdown
你是{角色名}，本次辩论的裁判。

**你不持有任何学派立场**，不参与辩论，不表达自己的观点。

## 评判原则
- 只以论证质量、逻辑一致性、证据可靠性为评判标准
- 不偏向任何学派，不预设任何价值立场
- 善于发现论证中的逻辑漏洞、隐含前提和概念混淆

## 语气
中立、精确、冷静。
```

### 角色 index.json 格式

```json
[
  {
    "id": "confucius",
    "name": "孔子",
    "school": "儒家",
    "period": "春秋",
    "avatar": "🎭",
    "persona_short": "仁爱礼治，中庸之道，以周礼为理想秩序"
  }
]
```

裁判 index 不需要 `school` 和 `period` 字段，增加 `neutral: true` 标记。

### 加载方式

复用项目已有的 `load_prompt()` 函数（来自 `trip_plan/prompts/__init__.py`）：

```python
from trip_plan.prompts import load_prompt

# 加载辩者 system prompt（.md 文件）
role_prompt = load_prompt("roles/debater/confucius")    # → prompts/roles/debater/confucius.md

# 加载裁判 system prompt（.md 文件）
judge_prompt = load_prompt("roles/judge/neutral_analyst")  # → prompts/roles/judge/neutral_analyst.md

# 加载阶段 task prompt（.md 文件）
task_prompt = load_prompt("opening")                    # → prompts/opening.md
```

---

## 注意事项

1. **角色设定质量决定辩论深度**：persona 需 100-200 字，包含核心主张、论证风格、语气特征
2. **裁判不参与辩论**：裁判只在 JUDGE_TALLY 和 JUDGE_SUMMARY 阶段发言
3. **阶段顺序不可跳**：状态机保证严格顺序，前端不能跳过阶段
4. **并行意味着消息可能乱序到达**：同一阶段内多条消息的推送顺序不保证，前端按 `timestamp` 排序显示
5. **流式生成**：`message_delta` 逐 token 推送，同一 `id` 多次推送，前端按 `id` 分组追加渲染
6. **断线重连**：前端 SSE 断开后，重新连接同一 session_id，后端从当前阶段继续推送
7. **会话过期**：辩论会话默认保留 30 分钟，超时清除