"""通用 Agent 基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from config import LLMConfig

T = TypeVar("T", bound=BaseModel)


class AgentError(RuntimeError):
    """Agent 运行异常。"""


def _log_llm_input(messages: list[BaseMessage], _output_schema: type) -> None:
    """记录大模型输入。"""

    from logging_config import get_logger

    logger = get_logger("agent.llm")
    for idx, msg in enumerate(messages):
        logger.debug("大模型输入[%s/%s]: type=%s", idx + 1, len(messages), msg.__class__.__name__)
        content = msg.content
        if isinstance(content, str):
            logger.debug("大模型输入内容[%s/%s]: %s", idx + 1, len(messages), content[:2000])
        else:
            logger.debug("大模型输入内容[%s/%s]: %s", idx + 1, len(messages), str(content)[:2000])


def _log_llm_output(result: Any, _output_schema: type) -> None:
    """记录大模型输出。"""

    from logging_config import get_logger

    logger = get_logger("agent.llm")
    if isinstance(result, BaseModel):
        logger.debug("大模型输出: %s", result.model_dump_json()[:2000])
    elif isinstance(result, dict):
        import json

        logger.debug("大模型输出: %s", json.dumps(result, ensure_ascii=False)[:2000])
    else:
        logger.debug("大模型输出: %s", str(result)[:2000])


def _log_llm_error(exc: Exception) -> None:
    """记录大模型错误。"""

    from logging_config import get_logger

    logger = get_logger("agent.llm")
    logger.warning("大模型调用出错: %s", exc)


class BaseAgent(ABC):
    """基于 LangChain 的通用 Agent 抽象。

    负责通用能力：
    - 根据 LLMConfig 创建 LangChain ChatModel
    - 绑定未来 MCP 工具
    - 组合 Agent 角色 prompt 和任务 prompt
    - 文本调用
    - 结构化输出调用
    """

    def __init__(
        self,
        llm_config: LLMConfig | None = None,
        tools: Sequence[Any] | None = None,
    ) -> None:
        self.llm_config = llm_config or LLMConfig()
        self.llm: BaseChatModel = self._build_llm(self.llm_config)
        self.llm = self._bind_tools(self.llm, tools)

    @property
    @abstractmethod
    def role_prompt(self) -> str:
        """具体 Agent 自己的角色设定。"""

    @staticmethod
    def _build_llm(config: LLMConfig) -> BaseChatModel:
        if config.provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
            except ImportError as exc:
                raise AgentError("缺少 langchain-anthropic，请先安装依赖") from exc

            return ChatAnthropic(
                model=config.model,
                anthropic_api_key=config.api_key.get_secret_value(),
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=config.timeout_seconds,
                base_url=config.base_url,
            )

        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise AgentError("缺少 langchain-openai，请先安装依赖") from exc

        return ChatOpenAI(
            model=config.model,
            openai_api_key=config.api_key.get_secret_value(),
            base_url=config.base_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout_seconds,
        )

    @staticmethod
    def _bind_tools(llm: BaseChatModel, tools: Sequence[Any] | None) -> BaseChatModel:
        if not tools:
            return llm
        try:
            return llm.bind_tools(list(tools))
        except Exception as exc:
            raise AgentError("绑定 Agent 工具失败") from exc

    def _build_system_content(self, task_prompt: str | None = None) -> str | None:
        parts: list[str] = []
        if self.role_prompt:
            parts.append(self.role_prompt)
        if task_prompt:
            parts.append(task_prompt)
        if not parts:
            return None
        return "\n\n".join(parts)

    def _build_messages(self, user_content: str, task_prompt: str | None = None) -> list[BaseMessage]:
        messages: list[BaseMessage] = []
        system_content = self._build_system_content(task_prompt)
        if system_content:
            messages.append(SystemMessage(content=system_content))
        messages.append(HumanMessage(content=user_content))
        return messages

    def invoke_text(self, user_content: str, task_prompt: str | None = None) -> str:
        """调用大模型并返回文本。"""

        messages = self._build_messages(user_content, task_prompt)
        _log_llm_input(messages, str)
        try:
            response = self.llm.invoke(messages)
        except Exception as exc:
            _log_llm_error(exc)
            raise AgentError("大模型调用失败") from exc

        content = response.content
        if isinstance(content, str):
            result = content
        elif isinstance(content, Sequence):
            result = "".join(str(part) for part in content)
        else:
            result = str(content)
        _log_llm_output(result, str)
        return result

    def invoke_structured(self, user_content: str, output_schema: type[T], task_prompt: str | None = None) -> T:
        """调用大模型并返回 Pydantic 结构化结果。"""

        messages = self._build_messages(user_content, task_prompt)
        _log_llm_input(messages, output_schema)
        try:
            structured_llm = self.llm.with_structured_output(output_schema)
            result = structured_llm.invoke(messages)
        except Exception as exc:
            _log_llm_error(exc)
            raise AgentError("结构化大模型调用失败") from exc
        _log_llm_output(result, output_schema)

        if isinstance(result, output_schema):
            return result
        if isinstance(result, dict):
            return output_schema.model_validate(result)
        if isinstance(result, BaseModel):
            return output_schema.model_validate(result.model_dump())
        raise AgentError(f"大模型返回结果类型不受支持：{type(result)}")

    @abstractmethod
    def run(self, user_content: str, **kwargs: Any) -> Any:
        """由具体业务 Agent 实现专属流程。"""
