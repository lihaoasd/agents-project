"""高德 MCP SSE 客户端。

通过 langchain_mcp_adapters 连接高德 MCP 服务，获取 LangChain 兼容工具列表。
"""

from __future__ import annotations

from typing import Any

from config.settings import AmapConfig
from langchain_mcp_adapters.client import MultiServerMCPClient
from logging_config import get_logger

logger = get_logger("trip_plan.service.amap_mcp")


class AmapMcpClient:
    """高德 MCP SSE 客户端。

    用法::

        client = AmapMcpClient()
        tools = await client.get_tools()
        # 将 tools 传给 LangGraph create_react_agent
        await client.close()
    """

    def __init__(self) -> None:
        self._config = AmapConfig()
        self._client: MultiServerMCPClient | None = None
        self._tools: list[Any] | None = None

    def _build_client(self) -> MultiServerMCPClient:
        mcp_key = self._config.mcp_key
        if not mcp_key:
            raise AmapMcpError(
                "缺少 AMAP_MCP_KEY，请在 backend/.env 中配置高德 MCP 密钥"
            )
        url = f"https://mcp.amap.com/sse?key={mcp_key[:8]}***"
        logger.info("构建高德 MCP 客户端 url=%s", url)
        return MultiServerMCPClient(
            {
                "amap": {
                    "url": f"https://mcp.amap.com/sse?key={mcp_key}",
                    "transport": "sse",
                }
            }
        )

    async def get_tools(self) -> list[Any]:
        """获取高德 MCP 提供的 LangChain 兼容工具列表。"""
        if self._tools is not None:
            logger.debug("高德 MCP 工具缓存命中 tool_count=%s", len(self._tools))
            return self._tools

        if self._client is None:
            logger.info("正在初始化高德 MCP 客户端...")
            self._client = self._build_client()

        try:
            logger.info("开始加载高德 MCP 工具列表...")
            self._tools = await self._client.get_tools()
            tool_names = [t.name for t in self._tools]
            logger.info(
                "高德 MCP 工具加载完成 tool_count=%s tools=%s",
                len(self._tools),
                tool_names,
            )
        except Exception as exc:
            logger.error("高德 MCP 工具加载失败: %s", exc)
            raise AmapMcpError(f"高德 MCP 工具加载失败: {exc}") from exc

        return self._tools

    async def close(self) -> None:
        """关闭 MCP 客户端连接。"""
        if self._client is not None:
            logger.info("正在关闭高德 MCP 客户端...")
            try:
                # MultiServerMCPClient 内部管理 session 生命周期
                pass
            except Exception:
                pass
            self._client = None
            self._tools = None
            logger.info("高德 MCP 客户端已关闭")


class AmapMcpError(Exception):
    """高德 MCP 客户端异常。"""