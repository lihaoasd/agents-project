"""通用 Agent 基类。"""

from __future__ import annotations

import json
import re
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
        """调用大模型并返回 Pydantic 结构化结果。

        不走原生 response_format（DeepSeek 等兼容 API 不支持），
        改用 JSON prompt 指令 + 正则提取 + 校验的方式。
        """
        # 构建 schema 描述塞进 prompt
        fields_desc = []
        for name, field in output_schema.model_fields.items():
            fields_desc.append(f'    "{name}": {field.annotation.__name__ if hasattr(field.annotation, "__name__") else str(field.annotation)}  // {field.description or ""}')

        schema_json = json.dumps(
            {name: f"<{field.annotation.__name__ if hasattr(field.annotation, '__name__') else str(field.annotation)}>" for name, field in output_schema.model_fields.items()},
            ensure_ascii=False, indent=2,
        )

        json_instruction = (
            f'\n\n请严格按以下 JSON 格式回复（不要加 markdown 代码块标记，直接输出纯 JSON）：\n'
            f'{schema_json}'
        )

        messages = self._build_messages(user_content + json_instruction, task_prompt)
        _log_llm_input(messages, output_schema)

        try:
            raw = self.llm.invoke(messages)
            content = raw.content if hasattr(raw, "content") else str(raw)
        except Exception as exc:
            _log_llm_error(exc)
            raise AgentError("结构化大模型调用失败") from exc

        _log_llm_output(content if isinstance(content, str) else str(content), str)

        text = content if isinstance(content, str) else str(content)

        # 尝试提取 JSON（可能被 ```json 包裹）
        json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
        if json_match:
            text = json_match.group(1).strip()

        # 尝试找第一个 { 到最后一个 }
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start != -1 and brace_end != -1:
            text = text[brace_start:brace_end + 1]

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            _log_llm_error(exc)
            raise AgentError(f"大模型返回无法解析为 JSON: {text[:200]}") from exc

        return output_schema.model_validate(data)

    @abstractmethod
    def run(self, user_content: str, **kwargs: Any) -> Any:
        """由具体业务 Agent 实现专属流程。"""
