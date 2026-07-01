"""辩论 Agent — 流式 LLM 调用封装。

基于 BaseAgent，为辩论各阶段提供：
- invoke_text() —— 非流式文本生成
- invoke_stream() —— 流式 token 生成（供 SSE 推送）
- invoke_structured() —— 结构化输出（投票、裁判结果）
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from agent import BaseAgent, AgentError
from config import LLMConfig
from debate.prompts import load_prompt


class DebateAgent(BaseAgent):
    """辩论专用 Agent —— 以指定角色人格生成辩论内容。

    每个 DebateAgent 实例绑定一个角色（辩者或裁判），
    构造时传入角色 prompt 文件 slug，自动加载角色 persona。
    各阶段 task prompt 在调用时动态传入。

    典型用法：

        agent = DebateAgent("roles/debater/confucius")
        # 非流式
        text = agent.invoke_text(
            user_content="辩论问题：...",
            task_prompt=agent.load_task_prompt("opening"),
        )
        # 流式（SSE）
        async for token in agent.invoke_stream(
            user_content="辩论问题：...",
            task_prompt=agent.load_task_prompt("opening"),
        ):
            yield f"data: {token}\\n\\n"
    """

    def __init__(
        self,
        role_slug: str,
        llm_config: LLMConfig | None = None,
    ) -> None:
        """创建辩论 Agent。

        Args:
            role_slug: 角色 prompt slug，如 "roles/debater/confucius"
            llm_config: LLM 配置，默认使用全局配置
        """
        super().__init__(llm_config=llm_config)
        self._role_slug = role_slug
        self._role_prompt: str = load_prompt(role_slug)

    # ---- 角色 prompt ----------------------------------------------------------

    @property
    def role_prompt(self) -> str:
        return self._role_prompt

    @property
    def role_slug(self) -> str:
        return self._role_slug

    # ---- 阶段 task prompt 加载 ------------------------------------------------

    @staticmethod
    def load_task_prompt(stage: str) -> str:
        """加载阶段 task prompt。

        Args:
            stage: 阶段名，如 "opening" / "cross_ask" / "cross_answer" /
                   "closing" / "vote" / "judge_tally" / "judge_summary"

        Returns:
            对应阶段的 task prompt 文本
        """
        return load_prompt(stage)

    # ---- run() — 通用单次调用 --------------------------------------------------

    def run(
        self,
        user_content: str,
        *,
        stage: str = "opening",
        **kwargs: Any,
    ) -> str:
        """通用单次辩论调用（非流式）。

        根据传入的阶段名自动加载 task prompt 并生成文本。

        Args:
            user_content: 用户内容（辩论上下文 + 指令）
            stage: 阶段名，默认 opening
            **kwargs: 保留，兼容 BaseAgent.run 接口

        Returns:
            生成的文本
        """
        task_prompt = self.load_task_prompt(stage)
        return self.invoke_text(user_content, task_prompt)

    # ---- 非流式文本调用 -------------------------------------------------------

    def invoke_text(
        self, user_content: str, task_prompt: str | None = None
    ) -> str:
        """调用大模型并返回完整文本（非流式）。"""
        return super().invoke_text(user_content, task_prompt)

    # ---- 流式文本调用 ---------------------------------------------------------

    async def invoke_stream(
        self,
        user_content: str,
        task_prompt: str | None = None,
        *,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        """流式调用大模型，逐 token 产出文本。

        用于 SSE message_delta 推送 —— 每产出一个 token 就 yield。

        Args:
            user_content: 用户提示词（辩论上下文 + 指令）
            task_prompt: 阶段 task prompt（可选，与 role_prompt 合并为 system prompt）
            temperature: 覆盖默认 temperature（可选）

        Yields:
            每个 token 的增量文本字符串
        """
        messages = self._build_messages(user_content, task_prompt)

        # 如果需要覆盖 temperature，创建新的 llm 实例
        llm = self.llm
        if temperature is not None:
            from config.settings import LLMConfig as Cfg

            new_config = Cfg(
                provider=self.llm_config.provider,
                model=self.llm_config.model,
                api_key=self.llm_config.api_key,
                base_url=self.llm_config.base_url,
                temperature=temperature,
                max_tokens=self.llm_config.max_tokens,
                timeout_seconds=self.llm_config.timeout_seconds,
            )
            llm = self._build_llm(new_config)

        try:
            async for chunk in llm.astream(messages):
                content = chunk.content
                if isinstance(content, str) and content:
                    yield content
        except Exception as exc:
            from agent.base import _log_llm_error

            _log_llm_error(exc)
            raise AgentError("流式大模型调用失败") from exc

    # ---- 结构化输出 -----------------------------------------------------------

    def invoke_structured(
        self,
        user_content: str,
        output_schema: type[Any],
        task_prompt: str | None = None,
    ) -> Any:
        """调用大模型并返回结构化结果。"""
        return super().invoke_structured(user_content, output_schema, task_prompt)

    # ---- 上下文构建工具 -------------------------------------------------------

    @staticmethod
    def format_transcript(messages: list[dict[str, Any]] | list[Any]) -> str:
        """将消息列表格式化为大模型可读的辩论记录文本。

        Args:
            messages: Message 对象列表或 dict 列表

        Returns:
            格式化的全文记录
        """
        lines: list[str] = []
        for msg in messages:
            # 兼容 Pydantic Message 对象和 dict
            if isinstance(msg, dict):
                speaker = msg.get("speaker_name", "未知")
                role = msg.get("speaker_role", "debater")
                target = msg.get("target_name", "")
                content = msg.get("content", "")
            else:
                speaker = getattr(msg, "speaker_name", "未知")
                role = getattr(msg, "speaker_role", "debater")
                target = getattr(msg, "target_name", "")
                content = getattr(msg, "content", "")

            prefix = f"[{speaker}（{role}）]"
            if target and target != "all":
                prefix += f" → @{target}"
            lines.append(f"{prefix}：\n{content}\n")
        return "\n".join(lines)

    @staticmethod
    def build_opening_context(question: str) -> str:
        """构建立论阶段的上下文（仅数据，指令由 stage task prompt 提供）。

        Args:
            question: 辩论问题

        Returns:
            适合传入 invoke_text / invoke_stream 的 user_content
        """
        return f"""辩论问题：「{question}」

请发表你的立论。"""

    @staticmethod
    def build_cross_ask_context(
        question: str, openings: dict[str, str]
    ) -> str:
        """构建质询提问阶段的上下文（仅数据，指令由 stage task prompt 提供）。

        Args:
            question: 辩论问题
            openings: {debater_name: opening_text} 所有辩者的立论内容

        Returns:
            适合传入 invoke_text / invoke_stream 的 user_content
        """
        openings_text = ""
        for name, text in openings.items():
            openings_text += f"\n### {name} 的立论\n{text}\n"

        return f"""辩论问题：「{question}」

以下是所有辩者的立论观点：
{openings_text}"""

    @staticmethod
    def build_cross_answer_context(
        question: str,
        my_opening: str,
        asker_name: str,
        ask_question: str,
    ) -> str:
        """构建质询回答阶段的上下文（仅数据，指令由 stage task prompt 提供）。

        Args:
            question: 辩论问题
            my_opening: 自己的立论内容
            asker_name: 提问者名称
            ask_question: 质询问题

        Returns:
            适合传入 invoke_text / invoke_stream 的 user_content
        """
        return f"""辩论问题：「{question}」

你的立论：
{my_opening}

对方 @{asker_name} 质询：
{ask_question}

请回答。"""

    @staticmethod
    def build_closing_context(
        question: str,
        my_opening: str,
        cross_examinations: str,
    ) -> str:
        """构建结辩阶段的上下文（仅数据，指令由 stage task prompt 提供）。

        Args:
            question: 辩论问题
            my_opening: 自己的立论内容
            cross_examinations: 与自己相关的质询记录摘要

        Returns:
            适合传入 invoke_text / invoke_stream 的 user_content
        """
        return f"""辩论问题：「{question}」

你的立论：
{my_opening}

质询过程：
{cross_examinations}

请发表结辩。"""

    @staticmethod
    def build_vote_context(
        question: str,
        full_transcript: str,
        exclude_name: str,
        candidate_names: list[str],
    ) -> str:
        """构建投票阶段的上下文（仅数据，指令由 stage task prompt 提供）。

        Args:
            question: 辩论问题
            full_transcript: 完整辩论记录
            exclude_name: 不能投票给自己的辩者名
            candidate_names: 可投候选人列表

        Returns:
            适合传入 invoke_text / invoke_stream 的 user_content
        """
        candidates = "、".join(candidate_names)
        return f"""辩论问题：「{question}」

完整辩论记录：
{full_transcript}

可投票候选人：{candidates}
你不能投票给：「{exclude_name}」（你自己）。

请投票。"""

    @staticmethod
    def build_judge_tally_context(
        question: str,
        full_transcript: str,
        votes_text: str,
    ) -> str:
        """构建裁判统计阶段的上下文（仅数据，指令由 stage task prompt 提供）。

        Args:
            question: 辩论问题
            full_transcript: 完整辩论记录
            votes_text: 投票记录文本

        Returns:
            适合传入 invoke_text / invoke_stream 的 user_content
        """
        return f"""辩论问题：「{question}」

完整辩论记录：
{full_transcript}

投票记录：
{votes_text}

请统计结果。"""

    @staticmethod
    def build_judge_summary_context(
        question: str,
        full_transcript: str,
        tally_result: str,
    ) -> str:
        """构建裁判总结阶段的上下文（仅数据，指令由 stage task prompt 提供）。

        Args:
            question: 辩论问题
            full_transcript: 完整辩论记录
            tally_result: 票数统计结果

        Returns:
            适合传入 invoke_text / invoke_stream 的 user_content
        """
        return f"""辩论问题：「{question}」

完整辩论记录：
{full_transcript}

投票与统计：
{tally_result}

请做综合总结。"""


__all__ = ["DebateAgent"]