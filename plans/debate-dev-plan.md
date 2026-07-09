# 多 Agent 辩论 — 开发计划

按最小功能点拆分，每步可独立开发、测试、验证。完成后打钩。

---

## 阶段一：项目骨架

### 1.1 创建 debate 模块目录

```
backend/debate/
├── __init__.py
├── api/      __init__.py, routes.py, schemas.py
├── service/  __init__.py, debate_service.py
├── agent/    __init__.py, debate_agent.py
├── state/    __init__.py, machine.py
├── prompts/  __init__.py
├── config/   __init__.py, settings.py
└── session/  __init__.py, store.py
```

**验证**：`python -c "from debate import ..."` 无报错

### 1.2 注册路由到 FastAPI

在 `backend/main.py` 中挂载 debate router。

**验证**：`GET /api/debate/health` 返回 200

---

## 阶段二：角色 Prompt 文件

### 2.1 编写 3 个核心辩者 prompt

`prompts/roles/debater/` 下创建：

- `confucius.md` — 孔子
- `laozi.md` — 老子
- `hanfei.md` — 韩非

**验证**：`load_prompt("roles/debater/confucius")` 返回正确内容

### 2.2 编写 1 个裁判 prompt

`prompts/roles/judge/` 下创建：

- `neutral_analyst.md` — 中立分析者

**验证**：`load_prompt("roles/judge/neutral_analyst")` 返回正确内容

### 2.3 编写角色 index.json

`prompts/roles/debater/index.json` 和 `prompts/roles/judge/index.json`

**验证**：读取 JSON 解析成功，字段齐全

---

## 阶段三：数据模型

### 3.1 DebateConfig / DebaterRole / JudgeRole

Pydantic 模型：辩论配置、辩者、裁判。

**验证**：`DebateConfig.parse_obj(sample_json)` 成功

### 3.2 DebateSession / Message / CrossQA / VoteResult

Pydantic 模型：会话、消息、质询对、投票记录。

**验证**：各模型实例化无报错，JSON 序列化正常

---

## 阶段四：LLM Agent 封装

### 4.1 DebateAgent — 单次流式 LLM 调用

复用 `agent/base.py` 的 `BaseAgent`，增加：

- `run_stream(system_prompt, user_prompt) -> AsyncGenerator[str]` — 逐 token yield
- 超时 120 秒
- 错误时抛 `AgentError`

**验证**：手动写一段 system + user prompt，流式输出逐 token 在控制台打印

---

## 阶段五：会话存储

### 5.1 SessionStore — 内存存储

- `create(config) -> session_id`
- `get(session_id) -> DebateSession`
- `add_message(session_id, message)`
- `get_all_messages(session_id) -> list[Message]`
- `get_full_transcript(session_id) -> str`
- TTL 30 分钟自动清理

**验证**：创建会话 → 追加消息 → 查询消息 → 验证全文记录

---

## 阶段六：状态机

### 6.1 StateMachine — 状态流转

```
opening → cross_ask → cross_answer → (loop) → closing → voting → judge_tally → judge_summary → complete
```

- `next_phase(current) -> next` — 返回下一阶段
- `is_parallel(phase) -> bool` — 该阶段内部是否并行
- `speakers_for(phase, session) -> list[debater_ids]` — 该阶段谁发言
- `target_for(phase, speaker, session) -> target_id` — 谁对谁说

**验证**：手动走完一遍完整状态流转

---

## 阶段七：API 端点（逐端构建）

### 7.1 GET /api/debate/roles

读取 `index.json`，返回可选辩者 + 裁判列表。

**验证**：`curl GET /api/debate/roles` 返回 JSON

### 7.2 POST /api/debate/start

接收 `{question, debater_ids[], judge_id, cross_examination_rounds}`，创建会话，返回 `session_id` + 参与者列表。

**验证**：`curl POST /api/debate/start` → 拿到 `session_id`

### 7.3 GET /api/debate/stream/{session_id} — SSE 核心端点

这是最大的一个端点。按子步骤开发：

#### 7.3.1 单辩者立论 SSE

- 读辩者 prompt + 立论 task prompt
- 调用 `DebateAgent.run_stream()`
- 每个 token push `event: message_delta`
- 开始 push `event: message_start`，结束 push `event: message_end`

**验证**：SSE 连接后看到一条立论逐字输出

#### 7.3.2 多辩者并行立论

- 所有辩者并发 `run_stream()`
- token 到达顺序即 push 顺序（自然交错）
- 前端验证多气泡并行打字

**验证**：3 个辩者立论同时 SSE 输出

#### 7.3.3 质询阶段

- 每轮：CROSS_ASK（一个辩者生成对其他辩者的问题）→ CROSS_ANSWER（被质询者逐个回答）
- 所有 Q&A 并行

**验证**：质询 Q&A 在 SSE 中正常输出

#### 7.3.4 结辩 → 投票 → 裁判统计 → 裁判总结

依次串联，每个阶段完成后自动进入下一阶段。

**验证**：完整 6 阶段辩论通过 SSE 走完

### 7.4 GET /api/debate/sessions/{session_id}

返回完整结构化辩论记录。

**验证**：辩论结束后 `curl GET /api/debate/sessions/{id}` 返回完整 JSON

---

## 阶段八：持久化 + 导出

### 8.1 SessionStore.persist()

辩论完成后，将会话序列化为 JSON 存入 `session/archive/{id}.json`。

**验证**：辩论结束后检查磁盘文件存在且内容完整

### 8.2 GET /api/debate/sessions/{id}/export?format=json

返回 JSON 文件下载。

**验证**：浏览器触发 `.json` 下载

### 8.3 GET /api/debate/sessions/{id}/export?format=md

将存档 JSON 渲染为 Markdown，返回 `.md` 下载。

**验证**：浏览器触发 `.md` 下载，内容排版正确

### 8.4 GET /api/debate/sessions/{id}/export?format=pdf

Markdown → HTML（WeasyPrint）→ PDF。单页长滚动，中文排版。

**验证**：浏览器触发 `.pdf` 下载/预览，排版美观

---

## 阶段九：前端

### 9.1 项目初始化

- Vue 3 + Vite，挂载到现有 frontend 或新建子目录
- 安装依赖：`marked`（Markdown 渲染）
- 路由配置：`/`、`/debate/:id`、`/debate/:id/result`

**验证**：三个路由切换正常

### 9.2 DebateSetupView — 辩论配置页

- 从 `GET /api/debate/roles` 加载角色列表
- 角色选择器：分类折叠 + 搜索 + 多选
- 裁判选择器：单选
- 问题输入 + 质询轮次
- "开始辩论"按钮 → `POST /api/debate/start` → 跳转聊天室

**验证**：选择 3 个辩者 + 裁判 + 输入问题 → 拿到 session_id → 跳转成功

### 9.3 DebateChatView — 聊天室（核心）

#### 9.3.1 SSE 连接 + 基础消息渲染

- `EventSource` 连接 `/api/debate/stream/{id}`
- `message_start` → 创建气泡
- `message_delta` → 追加文字
- `message_end` → 标记完成

**验证**：SSE 消息逐字渲染在页面上

#### 9.3.2 并行打字机效果

- 多气泡各自独立追加 delta
- `id` 分组管理
- 自动滚动

**验证**：3 个辩者同时发言，3 个气泡同时逐字增长

#### 9.3.3 阶段分隔条 + 定向发言标注

- `phase_change` → 插入分隔条
- `target != "all"` → 气泡显示 `@目标名`

**验证**：完整辩论中分隔条和 @标注 正确渲染

#### 9.3.4 辩论结束

- `done` 事件 → 显示获胜者横幅 + 导出按钮

**验证**：辩论结束横幅正确展示

### 9.4 DebateResultView — 结果摘要页

- 从 `GET /api/debate/sessions/{id}` 加载数据
- 获胜者卡片 + 票数统计 + 获奖
- 裁判总结（Markdown 渲染）
- 导出按钮（PDF / Markdown / JSON）

**验证**：结果页完整渲染，导出按钮触发下载

---

## 阶段十：完善

### 10.1 断线重连

- 前端 SSE 断开 → 指数退避重连
- 重连时带 `last_msg_id` → 后端补发错过的消息

**验证**：手动断开网络 → 重连后消息不丢失

### 10.2 补充剩余角色 prompt

- 孟子、庄子、荀子、朱熹、王阳明、孙子
- 西方哲学家（苏格拉底、柏拉图、亚里士多德、康德、尼采、马克思）
- 经济学家（亚当·斯密、凯恩斯、哈耶克）
- 社会科学（涂尔干、弗洛伊德、列维-斯特劳斯等）
- 学科集大成者
- 自定义组合角色

### 10.3 错误处理完善

- 单个辩者 LLM 超时 → 跳过该辩者，推送 error 事件
- 裁判 LLM 超时 → 降级为静态统计
- 会话不存在 → 404
- 辩论进行中导出 → 409

**验证**：模拟超时场景，辩论不崩溃

### 10.4 端到端测试

- 完整辩论：3 辩者 + 裁判，1 轮质询
- 验证 SSE 输出顺序正确
- 验证导出文件内容完整
- 验证 PDF 排版美观

---

## 依赖关系

```
阶段一 ──→ 阶段三 ──→ 阶段五 ──→ 阶段六 ──→ 阶段七 ──→ 阶段八
           │                          │
阶段二 ──→ 阶段四 ──────────────────→ 阶段七.3
                                      │
                                      阶段九 ←── 阶段七完成
                                      │
                                      阶段十 ←── 全部完成
```

## 并行建议

- 阶段二（prompt 文件）和阶段三（数据模型）可并行
- 阶段五（会话存储）和阶段六（状态机）可并行
- 阶段八（导出）和阶段九（前端）可并行
- 阶段九内部：`9.1` 先行，`9.2` 和 `9.3` 可部分并行

## 总功能点

| 阶段 | 功能点数 | 预估耗时 |
|------|---------|---------|
| 一·骨架 | 2 | 小 |
| 二·Prompt | 3 | 小 |
| 三·数据模型 | 2 | 小 |
| 四·Agent | 1 | 中 |
| 五·存储 | 1 | 中 |
| 六·状态机 | 1 | 中 |
| 七·API | 3+4 | 大 |
| 八·导出 | 4 | 中 |
| 九·前端 | 4+4 | 大 |
| 十·完善 | 4 | 小 |
| **合计** | **29** | — |