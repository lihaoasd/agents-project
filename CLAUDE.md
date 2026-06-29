# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## 5. 项目专用规则

**环境配置**

- 密钥通过 `.env` 文件和环境变量注入，**不能硬编码**
- `backend/.env` 已被 `.gitignore` 忽略，真实密钥不可提交
- 配置命名规范：后端 `AMAP_*`、`LLM_*` 前缀，前端 `VITE_*` 前缀
- 新增密钥必须同步更新 `.env.example`（不含真实值）

**Prompt 模板**

- 所有 Agent prompt 存储在 `trip_plan/prompts/` 目录，**不在代码中内联大段文本**
- 使用 `load_prompt(name, lang="zh")` 加载，不要手工 `open().read()`
- 新增 prompt 常量注册到 `trip_plan/prompts/config/prompt.py`

**路线规划**

- 路线规划使用三级降级：MCP Agent → 高德 Web API → 静态路线兜底
- 总距离/总时间**由前端根据 segments 累加计算**，不依赖 LLM 输出
- 前端格式化函数统一放在 `<script setup>` 中的 computed / function

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
