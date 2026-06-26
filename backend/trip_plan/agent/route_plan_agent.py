"""高德 MCP 路线规划 Agent。

使用 langchain.agents.create_agent + 高德 MCP 工具，让 LLM 自主决定
调用哪些高德工具（POI 搜索、地理编码、路线规划等）来生成行程路线。
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from agent.base import BaseAgent
from config.settings import LLMConfig
from logging_config import get_logger
from trip_plan.agent.models import ScenicSpot
from trip_plan.mcp.amap_mcp_client import AmapMcpClient, AmapMcpError
from trip_plan.prompts.config.prompt import PromptConfig

logger = get_logger("trip_plan.agent.route_plan")


@dataclass
class RoutePlanAgentResult:
    """路线规划 Agent 运行结果。"""

    result: dict[str, Any]
    provider: str
    model: str
    fallback: bool = False


class RoutePlanAgent:
    """使用高德 MCP 工具规划路线的 Agent。"""

    def __init__(self) -> None:
        self._mcp_client = AmapMcpClient()

    async def run(
        self,
        requirement: str,
        destination_id: str,
        destination_city: str,
        destination_province: str,
        spots: list[ScenicSpot],
        mode: str = "auto",
        origin: dict[str, Any] | None = None,
        destination: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> RoutePlanAgentResult:
        """使用高德 MCP 工具规划路线。

        Returns:
            RoutePlanAgentResult: 包含路线规划结果。
        """
        t_start = time.monotonic()

        # 1. 获取 MCP 工具
        t_tool_start = time.monotonic()
        try:
            tools = await self._mcp_client.get_tools()
        except AmapMcpError as exc:
            logger.warning("无法加载高德 MCP 工具: %s", exc)
            raise
        t_tool_elapsed = time.monotonic() - t_tool_start
        logger.info("MCP 工具加载耗时 %.2fs tool_count=%s", t_tool_elapsed, len(tools))

        if not tools:
            logger.warning("高德 MCP 返回空工具列表")
            raise AmapMcpError("高德 MCP 未返回任何工具")

        tool_names = [t.name for t in tools]
        logger.info("高德 MCP 可用工具(%s): %s", len(tools), tool_names)

        # 2. 构建 LLM + create_agent
        llm_config = LLMConfig()
        llm = BaseAgent._build_llm(llm_config)
        logger.info(
            "创建 Agent model=%s provider=%s temperature=%s max_tokens=%s",
            llm_config.model,
            llm_config.provider,
            llm_config.temperature,
            llm_config.max_tokens,
        )

        system_prompt = PromptConfig.load(PromptConfig.ROUTE_PLAN_SYSTEM)
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
        )

        # 3. 构建用户消息
        user_message = self._build_user_message(
            requirement=requirement,
            destination_id=destination_id,
            destination_city=destination_city,
            destination_province=destination_province,
            spots=spots,
            mode=mode,
            origin=origin,
            destination=destination,
            constraints=constraints,
        )
        logger.info(
            "Agent 输入: destination=%s spots=%s mode=%s origin=%s destination=%s",
            destination_id,
            len(spots),
            mode,
            origin.get("name", "N/A") if origin else "auto",
            destination.get("name", "N/A") if destination else "auto",
        )

        # 4. 调用 Agent
        t_llm_start = time.monotonic()
        try:
            result = await agent.ainvoke({"messages": [HumanMessage(content=user_message)]})
        except Exception as exc:
            t_elapsed = time.monotonic() - t_start
            logger.error(
                "MCP Agent 调用失败(总耗时%.2fs): %s",
                t_elapsed,
                exc,
            )
            raise AmapMcpError(f"路线规划 Agent 调用失败: {exc}") from exc
        t_llm_elapsed = time.monotonic() - t_llm_start
        logger.info("LLM 推理耗时 %.2fs", t_llm_elapsed)

        # 5. 解析结果 + 工具调用摘要
        final_messages = result.get("messages", [])
        self._log_tool_calls(final_messages)

        final_text = ""
        for msg in reversed(final_messages):
            if hasattr(msg, "content") and msg.content:
                final_text = msg.content
                break

        t_parse_start = time.monotonic()
        parsed = self._parse_agent_output(final_text, spots, mode, origin, destination)
        t_parse_elapsed = time.monotonic() - t_parse_start

        t_total = time.monotonic() - t_start
        logger.info(
            "MCP 路线规划完成 total=%.2fs llm=%.2fs parse=%.2fs "
            "provider=%s model=%s spots=%s segments=%s distance=%s duration=%s",
            t_total,
            t_llm_elapsed,
            t_parse_elapsed,
            llm_config.provider,
            llm_config.model,
            len(parsed.get("orderedSpots", [])),
            len(parsed.get("segments", [])),
            parsed.get("totalDistance"),
            parsed.get("totalDuration"),
        )

        return RoutePlanAgentResult(
            result=parsed,
            provider=llm_config.provider,
            model=llm_config.model,
        )

    def _build_user_message(
        self,
        requirement: str,
        destination_id: str,
        destination_city: str,
        destination_province: str,
        spots: list[ScenicSpot],
        mode: str,
        origin: dict[str, Any] | None,
        destination: dict[str, Any] | None,
        constraints: dict[str, Any] | None,
    ) -> str:
        """构建发给 Agent 的用户消息。"""
        spots_text = "\n".join(
            f"- {i + 1}. {spot.name}，地址：{spot.address}，类型：{spot.type}"
            for i, spot in enumerate(spots)
        )

        transport_mode = (
            "驾车" if mode == "driving"
            else ("公共交通" if mode == "transit" else "自动选择")
        )
        origin_text = (
            origin.get("name", "未指定")
            if origin
            else "未指定（请用目的地市中心）"
        )
        dest_text = (
            destination.get("name", "未指定")
            if destination
            else "未指定（请用目的地市中心）"
        )

        parts = [
            f"目的地：{destination_province} · {destination_city}（{destination_id}）",
            f"出行方式：{transport_mode}（mode={mode}）",
            f"起点：{origin_text}",
            f"终点：{dest_text}",
            f"用户需求：{requirement}",
        ]

        if constraints:
            parts.append(f"约束：{constraints}")

        parts.append(f"景点列表（共 {len(spots)} 个）：\n{spots_text}")
        parts.append("\n请按上述格式规划路线，直接返回 JSON。")

        return "\n\n".join(parts)

    # ---- 解析 ----

    @staticmethod
    def _parse_agent_output(
        text: str,
        spots: list[ScenicSpot],
        mode: str,
        origin: dict[str, Any] | None,
        destination: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """解析 Agent 输出的 JSON，多策略容错提取。"""
        raw = text.strip()
        parsed: dict[str, Any] = {}

        # 策略 1：直接解析整体
        parsed = _try_parse_json(raw)
        if parsed:
            return _apply_defaults(parsed, mode, origin, destination)

        # 策略 2：提取 markdown 代码块中的 JSON
        block_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", raw)
        if block_match:
            parsed = _try_parse_json(block_match.group(1).strip())
            if parsed:
                logger.info("JSON 提取成功: 策略=markdown-code-block")
                return _apply_defaults(parsed, mode, origin, destination)

        # 策略 3：提取最外层 {} 包裹的 JSON 对象
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            parsed = _try_parse_json(json_match.group(0))
            if parsed:
                logger.info("JSON 提取成功: 策略=brace-extract")
                return _apply_defaults(parsed, mode, origin, destination)

        # 策略 4：修复常见问题（尾逗号、单引号）后重试
        repaired = _repair_common_json_issues(raw)
        parsed = _try_parse_json(repaired)
        if parsed:
            logger.info("JSON 提取成功: 策略=json-repair")
            return _apply_defaults(parsed, mode, origin, destination)

        logger.warning(
            "Agent 输出无法解析为 JSON text_len=%s text_preview=%s",
            len(raw),
            raw[:500],
        )
        return _apply_defaults({}, mode, origin, destination)

    # ---- 工具调用追踪 ----

    @staticmethod
    def _log_tool_calls(messages: list[Any]) -> None:
        """记录 Agent 的工具调用详情。"""
        tool_requests: list[dict[str, Any]] = []
        tool_results: list[dict[str, Any]] = []

        for msg in messages:
            # ToolMessage：打印工具名 + 调用结果摘要
            if hasattr(msg, "content") and hasattr(msg, "name"):
                result_str = str(msg.content)
                logger.info("Agent 工具返回 tool=%s result=%s", msg.name, _safe_truncate(result_str, 300))

            # AI 消息中的 tool_calls（请求调用工具）
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_requests.append({
                        "name": tc.get("name", ""),
                        "args": _safe_truncate(tc.get("args", {}), 200),
                    })

            # ToolMessage 汇总
            if hasattr(msg, "content") and hasattr(msg, "name"):
                tool_results.append({
                    "name": msg.name,
                    "result": _safe_truncate(str(msg.content), 200),
                })

        if tool_requests:
            logger.info(
                "Agent 工具调用请求(%s): %s",
                len(tool_requests),
                tool_requests,
            )
        if tool_results:
            logger.info(
                "Agent 工具调用结果(%s): %s",
                len(tool_results),
                tool_results,
            )
        if not tool_requests and not tool_results:
            logger.info("Agent 未调用任何工具")

    async def close(self) -> None:
        """关闭 MCP 连接。"""
        await self._mcp_client.close()


def _safe_truncate(obj: Any, max_len: int) -> Any:
    """截断字符串，避免日志过长。"""
    s = str(obj)
    if len(s) <= max_len:
        return obj
    return s[:max_len] + "..."


# ---------- JSON 解析辅助 ----------


def _try_parse_json(text: str) -> dict[str, Any] | None:
    """尝试将文本解析为 JSON dict，失败返回 None。"""
    try:
        result = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
    if isinstance(result, dict):
        return result
    return None


def _repair_common_json_issues(text: str) -> str:
    """修复 LLM 输出 JSON 的常见问题：尾逗号、单引号。

    注意：不使用 look-behind 断言（Python 3.10 不支持变长 look-behind）。
    """
    # 移除对象/数组末尾多余的逗号
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    # 单引号 key/value 转双引号
    text = re.sub(r"'([^']*)'\s*:", r'"\1":', text)    # 'key': -> "key":
    text = re.sub(r":\s*'([^']*)'", r': "\1"', text)   # : 'value' -> : "value"
    text = re.sub(r"\[\s*'([^']*)'", r'["\1"', text)   # ['item' -> ["item"
    text = re.sub(r",\s*'([^']*)'", r', "\1"', text)   # , 'item' -> , "item"
    text = re.sub(r"'\s*\]", r'"]', text)               # 'item'] -> "item"]
    text = re.sub(r"'\s*}", r'"}', text)                # 'value'} -> "value"}
    return text


def _apply_defaults(
    parsed: dict[str, Any],
    mode: str,
    origin: dict[str, Any] | None,
    destination: dict[str, Any] | None,
) -> dict[str, Any]:
    """补充默认值。"""
    parsed.setdefault("orderedSpots", [])
    parsed.setdefault("segments", [])
    parsed.setdefault("totalDistance", 0)
    parsed.setdefault("totalDuration", 0)
    parsed.setdefault("mode", mode)
    parsed.setdefault("origin", origin or {})
    parsed.setdefault("destination", destination or {})
    parsed.setdefault("notices", [])
    return parsed