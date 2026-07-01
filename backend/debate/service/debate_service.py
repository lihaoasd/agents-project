"""辩论业务服务 — 辩论流程编排。

负责：
- 创建辩论会话（加载角色、初始化状态）
- 按阶段推进辩论流程
- 管理交叉质询的配对循环
- 同步和流式（SSE）两种调用模式
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from agent import AgentError
from debate.agent import DebateAgent
from debate.api.schemas import (
    CrossQA,
    DebateConfig,
    DebatePhase,
    DebaterRole,
    DebateSession,
    JudgeResult,
    JudgeRole,
    Message,
    MessageRole,
    VoteEntry,
)
from debate.prompts import load_prompt
from debate.session.store import SessionNotFoundError, SessionStore
from debate.state.machine import DebateState, PhaseResult
from logging_config import get_logger

logger = get_logger("debate.service")


# ============================================================
# LLM 结构化输出辅助模型（内部使用）
# ============================================================

class _VoteOutput(BaseModel):
    """LLM 投票结构化输出。"""

    voted_for_id: str = Field(..., description="被投票的辩者 ID")
    voted_for_name: str = Field(default="", description="被投票的辩者名称")
    scores: dict[str, float] = Field(
        default_factory=dict,
        description="分维度评分，如 {'logic': 8.5, 'evidence': 7.0, 'response': 7.5}",
    )
    reason: str = Field(default="", description="投票理由（一句话）")


class _TallyOutput(BaseModel):
    """LLM 裁判统计结构化输出。"""

    winner_id: str = Field(..., description="获胜辩者 ID")
    winner_name: str = Field(..., description="获胜辩者名称")
    votes_summary: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="各辩者分维度总分",
    )


# ============================================================
# 角色加载工具
# ============================================================

def _load_debater_roles(debater_ids: list[str]) -> list[DebaterRole]:
    """从 prompts/roles/debater/index.json 加载辩者角色信息。"""
    import json as _json
    from pathlib import Path as _Path

    index_path = _Path(__file__).resolve().parent.parent / "prompts" / "roles" / "debater" / "index.json"
    with open(index_path, encoding="utf-8") as f:
        catalog: list[dict[str, Any]] = _json.load(f)

    role_map: dict[str, DebaterRole] = {}
    for entry in catalog:
        role = DebaterRole(**entry)
        role_map[role.id] = role

    result: list[DebaterRole] = []
    for did in debater_ids:
        if did not in role_map:
            raise ValueError(f"未知辩者角色: {did}")
        result.append(role_map[did])
    return result


def _load_judge_role(judge_id: str) -> JudgeRole:
    """从 prompts/roles/judge/index.json 加载裁判角色信息。"""
    import json as _json
    from pathlib import Path as _Path

    index_path = _Path(__file__).resolve().parent.parent / "prompts" / "roles" / "judge" / "index.json"
    with open(index_path, encoding="utf-8") as f:
        catalog: list[dict[str, Any]] = _json.load(f)

    for entry in catalog:
        if entry["id"] == judge_id:
            return JudgeRole(**entry)
    raise ValueError(f"未知裁判角色: {judge_id}")


# ============================================================
# DebateService
# ============================================================

class DebateService:
    """辩论编排服务。

    持有：
    - SessionStore（共享存储）
    - DebateState（每场辩论的状态机）
    - DebateAgent 实例（按需创建）

    用法：
        service = DebateService()
        session = service.create_session(config)
        service.run_opening(session.session_id)
        service.run_cross_examination(session.session_id, round_num=1)
        service.run_closing(session.session_id)
        service.run_voting(session.session_id)
        service.run_judge(session.session_id)
    """

    def __init__(self, store: SessionStore | None = None) -> None:
        self._store = store or SessionStore()
        # 每场辩论对应一个状态机
        self._states: dict[str, DebateState] = {}

    # ---- 会话管理 ------------------------------------------------------------

    def create_session(self, config: DebateConfig) -> DebateSession:
        """创建新辩论会话。

        Args:
            config: 辩论配置（问题、辩者列表、裁判、质询轮数）

        Returns:
            初始化后的 DebateSession（阶段 = OPENING）
        """
        debaters = _load_debater_roles(config.debater_ids)
        judge = _load_judge_role(config.judge_id)

        session = DebateSession(
            session_id=SessionStore.new_session_id(),
            config=config,
            debaters=debaters,
            judge=judge,
            current_phase=DebatePhase.OPENING,
            current_round=0,
        )

        self._store.create(session)
        self._states[session.session_id] = DebateState(current_phase=DebatePhase.OPENING)

        logger.info(
            "辩论会话创建完成 session_id=%s question=%s debaters=%s rounds=%s",
            session.session_id,
            config.question[:60],
            config.debater_ids,
            config.cross_examination_rounds,
        )
        return session

    def get_session(self, session_id: str) -> DebateSession:
        """获取辩论会话。"""
        return self._store.get(session_id)

    def _get_state(self, session_id: str) -> DebateState:
        """获取辩论状态机。"""
        if session_id not in self._states:
            raise SessionNotFoundError(f"辩论状态不存在: {session_id}")
        return self._states[session_id]

    # ---- Agent 工厂 ----------------------------------------------------------

    @staticmethod
    def _make_debater_agent(debater_id: str) -> DebateAgent:
        """创建辩者 Agent。"""
        slug = f"roles/debater/{debater_id}"
        return DebateAgent(slug)

    @staticmethod
    def _make_judge_agent(judge_id: str) -> DebateAgent:
        """创建裁判 Agent。"""
        slug = f"roles/judge/{judge_id}"
        return DebateAgent(slug)

    # ---- 消息构建工具 --------------------------------------------------------

    @staticmethod
    def _new_message(
        phase: DebatePhase,
        role: MessageRole,
        speaker_id: str,
        speaker_name: str,
        content: str,
        target_id: str = "all",
        target_name: str = "",
        sequence: int = 0,
    ) -> Message:
        return Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            phase=phase,
            role=role,
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            target_id=target_id,
            target_name=target_name,
            content=content,
            timestamp=datetime.utcnow(),
            sequence=sequence,
        )

    # ================================================================
    # Phase 1: Opening（立论陈词）
    # ================================================================

    def run_opening(self, session_id: str) -> DebateSession:
        """执行立论阶段 —— 所有辩者同时发表立论。

        Returns:
            更新后的 DebateSession
        """
        session = self.get_session(session_id)
        state = self._get_state(session_id)

        result = state.transition_to(DebatePhase.OPENING)
        if not result.success:
            raise ValueError(result.message)

        question = session.config.question

        logger.info("开始立论阶段 session_id=%s", session_id)

        for idx, debater in enumerate(session.debaters):
            agent = self._make_debater_agent(debater.id)
            user_content = DebateAgent.build_opening_context(question)

            try:
                content = agent.invoke_text(user_content, agent.load_task_prompt("opening"))
            except AgentError as exc:
                logger.error("辩者 %s 立论失败: %s", debater.name, exc)
                content = f"[{debater.name} 立论生成失败，请稍后重试]"

            msg = self._new_message(
                phase=DebatePhase.OPENING,
                role=MessageRole.DEBATER,
                speaker_id=debater.id,
                speaker_name=debater.name,
                content=content,
                sequence=idx + 1,
            )
            self._store.add_message(session_id, msg)
            logger.info("立论完成: %s (%s chars)", debater.name, len(content))

        self._store.update_phase(session_id, "opening", 0)
        logger.info("立论阶段结束 session_id=%s messages=%s", session_id, len(self._store.get(session_id).messages))

        return self._store.get(session_id)

    async def stream_opening(self, session_id: str) -> AsyncIterator[dict[str, Any]]:
        """流式执行立论阶段 —— 每个辩者的 token 逐条 SSE 推送。

        Yields:
            SSE 事件 dict：{"event": "message_delta", "data": {"speaker_id": ..., "token": ...}}
            以及阶段结束事件：{"event": "phase_complete", "data": {...}}
        """
        session = self.get_session(session_id)
        state = self._get_state(session_id)

        result = state.transition_to(DebatePhase.OPENING)
        if not result.success:
            yield {"event": "error", "data": {"message": result.message}}
            return

        question = session.config.question

        for idx, debater in enumerate(session.debaters):
            agent = self._make_debater_agent(debater.id)
            user_content = DebateAgent.build_opening_context(question)

            # 发送发言人开始事件
            yield {
                "event": "speaker_start",
                "data": {
                    "speaker_id": debater.id,
                    "speaker_name": debater.name,
                    "phase": "opening",
                    "sequence": idx + 1,
                },
            }

            # 流式推送 token
            full_content: list[str] = []
            try:
                async for token in agent.invoke_stream(
                    user_content,
                    agent.load_task_prompt("opening"),
                ):
                    full_content.append(token)
                    yield {
                        "event": "message_delta",
                        "data": {
                            "speaker_id": debater.id,
                            "speaker_name": debater.name,
                            "token": token,
                            "phase": "opening",
                            "sequence": idx + 1,
                        },
                    }
            except AgentError as exc:
                logger.error("辩者 %s 流式立论失败: %s", debater.name, exc)
                yield {
                    "event": "error",
                    "data": {"speaker_id": debater.id, "message": str(exc)},
                }

            content = "".join(full_content)
            msg = self._new_message(
                phase=DebatePhase.OPENING,
                role=MessageRole.DEBATER,
                speaker_id=debater.id,
                speaker_name=debater.name,
                content=content,
                sequence=idx + 1,
            )
            self._store.add_message(session_id, msg)

            # 发送发言人结束事件
            yield {
                "event": "speaker_end",
                "data": {
                    "speaker_id": debater.id,
                    "speaker_name": debater.name,
                    "full_content": content,
                },
            }

        self._store.update_phase(session_id, "opening", 0)
        yield {"event": "phase_complete", "data": {"phase": "opening", "session_id": session_id}}

    # ================================================================
    # Phase 2-3: Cross-Examination（交叉质询）
    # ================================================================

    def run_cross_examination(self, session_id: str, round_num: int | None = None) -> DebateSession:
        """执行一轮完整的交叉质询。

        每轮中，每个辩者对每个其他辩者提出一个问题，对方回答。
        即 N 个辩者产生 N*(N-1) 对 Q&A。

        Args:
            session_id: 会话 ID
            round_num: 轮次号（None 时自动从状态机获取）

        Returns:
            更新后的 DebateSession
        """
        session = self.get_session(session_id)
        state = self._get_state(session_id)

        if round_num is None:
            round_num = state.current_round + 1

        question = session.config.question
        debaters = session.debaters

        # 收集目前已产生的立论内容
        openings: dict[str, str] = {}
        for msg in session.messages:
            if msg.phase == DebatePhase.OPENING:
                openings[msg.speaker_id] = msg.content

        # 生成所有 Q&A 配对
        pairs: list[tuple[DebaterRole, DebaterRole]] = []
        for asker in debaters:
            for answerer in debaters:
                if asker.id != answerer.id:
                    pairs.append((asker, answerer))

        logger.info(
            "开始第 %s 轮交叉质询 session_id=%s pairs=%s",
            round_num,
            session_id,
            len(pairs),
        )

        seq = len(session.messages)

        for asker, answerer in pairs:
            # --- CROSS_ASK ---
            state.transition_to(DebatePhase.CROSS_ASK)
            ask_agent = self._make_debater_agent(asker.id)

            # 构建质询提问上下文：问题 + 所有人的立论
            ask_context = DebateAgent.build_cross_ask_context(question, openings)
            try:
                ask_content = ask_agent.invoke_text(ask_context, ask_agent.load_task_prompt("cross_ask"))
            except AgentError as exc:
                logger.error("辩者 %s 质询提问失败: %s", asker.name, exc)
                ask_content = f"[{asker.name} 质询提问生成失败]"

            seq += 1
            ask_msg = self._new_message(
                phase=DebatePhase.CROSS_ASK,
                role=MessageRole.DEBATER,
                speaker_id=asker.id,
                speaker_name=asker.name,
                content=ask_content,
                target_id=answerer.id,
                target_name=answerer.name,
                sequence=seq,
            )
            self._store.add_message(session_id, ask_msg)

            # --- CROSS_ANSWER ---
            state.transition_to(DebatePhase.CROSS_ANSWER)
            ans_agent = self._make_debater_agent(answerer.id)

            my_opening = openings.get(answerer.id, "")
            ans_context = DebateAgent.build_cross_answer_context(
                question=question,
                my_opening=my_opening,
                asker_name=asker.name,
                ask_question=ask_content,
            )
            try:
                ans_content = ans_agent.invoke_text(ans_context, ans_agent.load_task_prompt("cross_answer"))
            except AgentError as exc:
                logger.error("辩者 %s 质询回答失败: %s", answerer.name, exc)
                ans_content = f"[{answerer.name} 质询回答生成失败]"

            seq += 1
            ans_msg = self._new_message(
                phase=DebatePhase.CROSS_ANSWER,
                role=MessageRole.DEBATER,
                speaker_id=answerer.id,
                speaker_name=answerer.name,
                content=ans_content,
                target_id=asker.id,
                target_name=asker.name,
                sequence=seq,
            )
            self._store.add_message(session_id, ans_msg)

            # 记录 CrossQA
            qa = CrossQA(
                round=round_num,
                asker_id=asker.id,
                asker_name=asker.name,
                answerer_id=answerer.id,
                answerer_name=answerer.name,
                question=ask_msg,
                answer=ans_msg,
            )
            self._store.add_cross_qa(session_id, qa)
            state.register_cross_pair(asker.id, answerer.id)

        # 判断是否继续下一轮
        total_rounds = session.config.cross_examination_rounds
        state.current_round = round_num
        advance_result = state.advance_cross_round(total_rounds)
        logger.info("交叉质询推进: %s", advance_result.message)

        self._store.update_phase(session_id, state.current_phase.value, state.current_round)

        return self._store.get(session_id)

    async def stream_cross_examination(
        self, session_id: str, round_num: int | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """流式执行一轮交叉质询 —— 每个 token 逐条 SSE 推送。"""
        session = self.get_session(session_id)
        state = self._get_state(session_id)

        if round_num is None:
            round_num = state.current_round + 1

        question = session.config.question
        debaters = session.debaters

        openings: dict[str, str] = {}
        for msg in session.messages:
            if msg.phase == DebatePhase.OPENING:
                openings[msg.speaker_id] = msg.content

        pairs: list[tuple[DebaterRole, DebaterRole]] = []
        for asker in debaters:
            for answerer in debaters:
                if asker.id != answerer.id:
                    pairs.append((asker, answerer))

        seq = len(session.messages)

        for asker, answerer in pairs:
            # --- 流式提问 ---
            state.transition_to(DebatePhase.CROSS_ASK)
            ask_agent = self._make_debater_agent(asker.id)

            yield {
                "event": "speaker_start",
                "data": {
                    "speaker_id": asker.id,
                    "speaker_name": asker.name,
                    "target_id": answerer.id,
                    "target_name": answerer.name,
                    "phase": "cross_ask",
                    "round": round_num,
                },
            }

            ask_context = DebateAgent.build_cross_ask_context(question, openings)
            ask_tokens: list[str] = []
            try:
                async for token in ask_agent.invoke_stream(
                    ask_context, ask_agent.load_task_prompt("cross_ask"),
                ):
                    ask_tokens.append(token)
                    yield {
                        "event": "message_delta",
                        "data": {
                            "speaker_id": asker.id,
                            "speaker_name": asker.name,
                            "target_id": answerer.id,
                            "phase": "cross_ask",
                            "round": round_num,
                            "token": token,
                        },
                    }
            except AgentError as exc:
                logger.error("辩者 %s 流式质询提问失败: %s", asker.name, exc)
                yield {"event": "error", "data": {"speaker_id": asker.id, "message": str(exc)}}

            ask_content = "".join(ask_tokens)
            seq += 1
            ask_msg = self._new_message(
                phase=DebatePhase.CROSS_ASK,
                role=MessageRole.DEBATER,
                speaker_id=asker.id,
                speaker_name=asker.name,
                content=ask_content,
                target_id=answerer.id,
                target_name=answerer.name,
                sequence=seq,
            )
            self._store.add_message(session_id, ask_msg)

            yield {
                "event": "speaker_end",
                "data": {"speaker_id": asker.id, "phase": "cross_ask", "full_content": ask_content},
            }

            # --- 流式回答 ---
            state.transition_to(DebatePhase.CROSS_ANSWER)
            ans_agent = self._make_debater_agent(answerer.id)

            yield {
                "event": "speaker_start",
                "data": {
                    "speaker_id": answerer.id,
                    "speaker_name": answerer.name,
                    "target_id": asker.id,
                    "target_name": asker.name,
                    "phase": "cross_answer",
                    "round": round_num,
                },
            }

            my_opening = openings.get(answerer.id, "")
            ans_context = DebateAgent.build_cross_answer_context(
                question=question,
                my_opening=my_opening,
                asker_name=asker.name,
                ask_question=ask_content,
            )
            ans_tokens: list[str] = []
            try:
                async for token in ans_agent.invoke_stream(
                    ans_context, ans_agent.load_task_prompt("cross_answer"),
                ):
                    ans_tokens.append(token)
                    yield {
                        "event": "message_delta",
                        "data": {
                            "speaker_id": answerer.id,
                            "speaker_name": answerer.name,
                            "target_id": asker.id,
                            "phase": "cross_answer",
                            "round": round_num,
                            "token": token,
                        },
                    }
            except AgentError as exc:
                logger.error("辩者 %s 流式质询回答失败: %s", answerer.name, exc)
                yield {"event": "error", "data": {"speaker_id": answerer.id, "message": str(exc)}}

            ans_content = "".join(ans_tokens)
            seq += 1
            ans_msg = self._new_message(
                phase=DebatePhase.CROSS_ANSWER,
                role=MessageRole.DEBATER,
                speaker_id=answerer.id,
                speaker_name=answerer.name,
                content=ans_content,
                target_id=asker.id,
                target_name=asker.name,
                sequence=seq,
            )
            self._store.add_message(session_id, ans_msg)

            yield {
                "event": "speaker_end",
                "data": {"speaker_id": answerer.id, "phase": "cross_answer", "full_content": ans_content},
            }

            qa = CrossQA(
                round=round_num,
                asker_id=asker.id,
                asker_name=asker.name,
                answerer_id=answerer.id,
                answerer_name=answerer.name,
                question=ask_msg,
                answer=ans_msg,
            )
            self._store.add_cross_qa(session_id, qa)
            state.register_cross_pair(asker.id, answerer.id)

        total_rounds = session.config.cross_examination_rounds
        state.current_round = round_num
        advance_result = state.advance_cross_round(total_rounds)

        self._store.update_phase(session_id, state.current_phase.value, state.current_round)
        yield {
            "event": "phase_complete",
            "data": {"phase": "cross_examination", "round": round_num, "next_phase": state.current_phase.value},
        }

    # ================================================================
    # Phase 4: Closing（结辩陈词）
    # ================================================================

    def run_closing(self, session_id: str) -> DebateSession:
        """执行结辩阶段 —— 所有辩者发表结辩。"""
        session = self.get_session(session_id)
        state = self._get_state(session_id)

        result = state.transition_to(DebatePhase.CLOSING)
        if not result.success:
            raise ValueError(result.message)

        question = session.config.question

        # 为每个辩者收集相关质询记录
        openings: dict[str, str] = {}
        for msg in session.messages:
            if msg.phase == DebatePhase.OPENING:
                openings[msg.speaker_id] = msg.content

        logger.info("开始结辩阶段 session_id=%s", session_id)

        for idx, debater in enumerate(session.debaters):
            # 收集与该辩者相关的质询记录
            cross_lines: list[str] = []
            for qa in session.cross_qas:
                if qa.answerer_id == debater.id:
                    cross_lines.append(
                        f"轮次{qa.round} | {qa.asker_name} 问：{qa.question.content if qa.question else ''}"
                    )
                    cross_lines.append(
                        f"轮次{qa.round} | 你答：{qa.answer.content if qa.answer else ''}"
                    )
            cross_text = "\n".join(cross_lines) if cross_lines else "（无相关质询记录）"

            agent = self._make_debater_agent(debater.id)
            context = DebateAgent.build_closing_context(
                question=question,
                my_opening=openings.get(debater.id, ""),
                cross_examinations=cross_text,
            )

            try:
                content = agent.invoke_text(context, agent.load_task_prompt("closing"))
            except AgentError as exc:
                logger.error("辩者 %s 结辩失败: %s", debater.name, exc)
                content = f"[{debater.name} 结辩生成失败]"

            msg = self._new_message(
                phase=DebatePhase.CLOSING,
                role=MessageRole.DEBATER,
                speaker_id=debater.id,
                speaker_name=debater.name,
                content=content,
                sequence=len(session.messages) + 1,
            )
            self._store.add_message(session_id, msg)
            logger.info("结辩完成: %s (%s chars)", debater.name, len(content))

        self._store.update_phase(session_id, "closing", state.current_round)
        return self._store.get(session_id)

    async def stream_closing(self, session_id: str) -> AsyncIterator[dict[str, Any]]:
        """流式执行结辩阶段。"""
        session = self.get_session(session_id)
        state = self._get_state(session_id)

        result = state.transition_to(DebatePhase.CLOSING)
        if not result.success:
            yield {"event": "error", "data": {"message": result.message}}
            return

        question = session.config.question

        openings: dict[str, str] = {}
        for msg in session.messages:
            if msg.phase == DebatePhase.OPENING:
                openings[msg.speaker_id] = msg.content

        for debater in session.debaters:
            cross_lines: list[str] = []
            for qa in session.cross_qas:
                if qa.answerer_id == debater.id:
                    cross_lines.append(
                        f"轮次{qa.round} | {qa.asker_name} 问：{qa.question.content if qa.question else ''}"
                    )
                    cross_lines.append(
                        f"轮次{qa.round} | 你答：{qa.answer.content if qa.answer else ''}"
                    )
            cross_text = "\n".join(cross_lines) if cross_lines else "（无相关质询记录）"

            agent = self._make_debater_agent(debater.id)
            context = DebateAgent.build_closing_context(
                question=question,
                my_opening=openings.get(debater.id, ""),
                cross_examinations=cross_text,
            )

            yield {
                "event": "speaker_start",
                "data": {"speaker_id": debater.id, "speaker_name": debater.name, "phase": "closing"},
            }

            tokens: list[str] = []
            try:
                async for token in agent.invoke_stream(context, agent.load_task_prompt("closing")):
                    tokens.append(token)
                    yield {
                        "event": "message_delta",
                        "data": {
                            "speaker_id": debater.id,
                            "speaker_name": debater.name,
                            "phase": "closing",
                            "token": token,
                        },
                    }
            except AgentError as exc:
                logger.error("辩者 %s 流式结辩失败: %s", debater.name, exc)
                yield {"event": "error", "data": {"speaker_id": debater.id, "message": str(exc)}}

            content = "".join(tokens)
            msg = self._new_message(
                phase=DebatePhase.CLOSING,
                role=MessageRole.DEBATER,
                speaker_id=debater.id,
                speaker_name=debater.name,
                content=content,
                sequence=len(session.messages) + 1,
            )
            self._store.add_message(session_id, msg)

            yield {
                "event": "speaker_end",
                "data": {"speaker_id": debater.id, "phase": "closing", "full_content": content},
            }

        self._store.update_phase(session_id, "closing", state.current_round)
        yield {"event": "phase_complete", "data": {"phase": "closing", "session_id": session_id}}

    # ================================================================
    # Phase 5: Voting（投票）
    # ================================================================

    def run_voting(self, session_id: str) -> DebateSession:
        """执行投票阶段 —— 每个辩者投票给另一个辩者（不能投自己）。"""
        session = self.get_session(session_id)
        state = self._get_state(session_id)

        result = state.transition_to(DebatePhase.VOTING)
        if not result.success:
            raise ValueError(result.message)

        question = session.config.question
        transcript = DebateAgent.format_transcript(session.messages)
        candidate_names = [d.name for d in session.debaters]

        logger.info("开始投票阶段 session_id=%s", session_id)
        votes: list[VoteEntry] = []

        for debater in session.debaters:
            exclude_name = debater.name
            candidates = [d.id for d in session.debaters if d.id != debater.id]

            agent = self._make_debater_agent(debater.id)
            context = DebateAgent.build_vote_context(
                question=question,
                full_transcript=transcript,
                exclude_name=exclude_name,
                candidate_names=candidates,
            )

            try:
                vote_output = agent.invoke_structured(
                    context, _VoteOutput, agent.load_task_prompt("vote"),
                )
                vote_entry = VoteEntry(
                    voter_id=debater.id,
                    voter_name=debater.name,
                    voted_for_id=vote_output.voted_for_id,
                    voted_for_name=vote_output.voted_for_name,
                    scores=vote_output.scores,
                    reason=vote_output.reason,
                )
            except AgentError as exc:
                logger.error("辩者 %s 投票失败: %s", debater.name, exc)
                # 投票失败时投给第一个合法候选人
                fallback_id = candidates[0] if candidates else ""
                fallback_name = next((d.name for d in session.debaters if d.id == fallback_id), "")
                vote_entry = VoteEntry(
                    voter_id=debater.id,
                    voter_name=debater.name,
                    voted_for_id=fallback_id,
                    voted_for_name=fallback_name,
                    scores={},
                    reason=f"[投票生成失败: {exc}]",
                )

            votes.append(vote_entry)
            logger.info("投票完成: %s → %s", debater.name, vote_entry.voted_for_name)

        # 存储投票结果到 session 中
        if session.judge_result is None:
            session.judge_result = JudgeResult(winner_id="", winner_name="", summary="")
        session.judge_result.votes = votes
        self._store.update_phase(session_id, "voting", state.current_round)
        return self._store.get(session_id)

    async def stream_voting(self, session_id: str) -> AsyncIterator[dict[str, Any]]:
        """流式执行投票阶段。"""
        session = self.get_session(session_id)
        state = self._get_state(session_id)

        result = state.transition_to(DebatePhase.VOTING)
        if not result.success:
            yield {"event": "error", "data": {"message": result.message}}
            return

        question = session.config.question
        transcript = DebateAgent.format_transcript(session.messages)

        for debater in session.debaters:
            candidates = [d.id for d in session.debaters if d.id != debater.id]
            agent = self._make_debater_agent(debater.id)
            context = DebateAgent.build_vote_context(
                question=question,
                full_transcript=transcript,
                exclude_name=debater.name,
                candidate_names=[d.name for d in session.debaters if d.id != debater.id],
            )

            yield {
                "event": "vote_start",
                "data": {"voter_id": debater.id, "voter_name": debater.name},
            }

            try:
                vote_output = agent.invoke_structured(
                    context, _VoteOutput, agent.load_task_prompt("vote"),
                )
                vote_entry = VoteEntry(
                    voter_id=debater.id,
                    voter_name=debater.name,
                    voted_for_id=vote_output.voted_for_id,
                    voted_for_name=vote_output.voted_for_name,
                    scores=vote_output.scores,
                    reason=vote_output.reason,
                )
                yield {
                    "event": "vote_complete",
                    "data": vote_entry.model_dump(),
                }
            except AgentError as exc:
                logger.error("辩者 %s 投票失败: %s", debater.name, exc)
                fallback_id = candidates[0] if candidates else ""
                fallback_name = next((d.name for d in session.debaters if d.id == fallback_id), "")
                vote_entry = VoteEntry(
                    voter_id=debater.id,
                    voter_name=debater.name,
                    voted_for_id=fallback_id,
                    voted_for_name=fallback_name,
                    scores={},
                    reason=f"[投票生成失败]",
                )
                yield {
                    "event": "vote_complete",
                    "data": {"voter_id": debater.id, "error": str(exc)},
                }

            # 将投票结果存入 session（通过临时存储）
            if session.judge_result is None:
                session.judge_result = JudgeResult(
                    winner_id="",
                    winner_name="",
                    votes=[],
                    summary="",
                )
            session.judge_result.votes.append(vote_entry)

        self._store.update_phase(session_id, "voting", state.current_round)
        yield {"event": "phase_complete", "data": {"phase": "voting", "session_id": session_id}}

    # ================================================================
    # Phase 6-7: Judge（裁判评判）
    # ================================================================

    def run_judge_tally(self, session_id: str) -> DebateSession:
        """执行裁判统计阶段 —— 裁判统计投票结果。"""
        session = self.get_session(session_id)
        state = self._get_state(session_id)

        # 确保投票已完成（在流转之前，因为投票阶段在 JUDGE_TALLY 之前）
        if session.judge_result is None or not session.judge_result.votes:
            if state.current_phase not in (DebatePhase.VOTING, DebatePhase.JUDGE_TALLY,
                                           DebatePhase.JUDGE_SUMMARY, DebatePhase.COMPLETE):
                self.run_voting(session_id)
                session = self.get_session(session_id)

        result = state.transition_to(DebatePhase.JUDGE_TALLY)
        if not result.success:
            raise ValueError(result.message)

        question = session.config.question
        transcript = DebateAgent.format_transcript(session.messages)

        votes = session.judge_result.votes if session.judge_result else []
        votes_text = "\n".join(
            f"- {v.voter_name} 投票给 {v.voted_for_name}，理由：{v.reason}，评分：{v.scores}"
            for v in votes
        )

        logger.info("开始裁判统计阶段 session_id=%s", session_id)

        judge = self._make_judge_agent(session.config.judge_id)
        context = DebateAgent.build_judge_tally_context(
            question=question,
            full_transcript=transcript,
            votes_text=votes_text,
        )

        try:
            tally_output = judge.invoke_structured(
                context, _TallyOutput, judge.load_task_prompt("judge_tally"),
            )
            # 合并投票结果
            if session.judge_result is None:
                session.judge_result = JudgeResult(winner_id="", winner_name="", summary="")
            session.judge_result.winner_id = tally_output.winner_id
            session.judge_result.winner_name = tally_output.winner_name
            session.judge_result.scores_summary = tally_output.votes_summary
        except AgentError as exc:
            logger.error("裁判统计失败: %s", exc)
            if session.judge_result is None:
                session.judge_result = JudgeResult(winner_id="", winner_name="", summary="")
            session.judge_result.winner_name = f"[裁判统计失败: {exc}]"

        self._store.update_phase(session_id, "judge_tally", state.current_round)
        logger.info("裁判统计完成 winner=%s", session.judge_result.winner_name)

        return self._store.get(session_id)

    def run_judge_summary(self, session_id: str) -> DebateSession:
        """执行裁判总结阶段 —— 裁判做综合总结。"""
        session = self.get_session(session_id)
        state = self._get_state(session_id)

        result = state.transition_to(DebatePhase.JUDGE_SUMMARY)
        if not result.success:
            raise ValueError(result.message)

        # 确保裁判统计已完成
        if session.judge_result is None:
            self.run_judge_tally(session_id)
            session = self.get_session(session_id)

        question = session.config.question
        transcript = DebateAgent.format_transcript(session.messages)
        tally_result = (
            f"获胜者: {session.judge_result.winner_name}\n"
            f"投票详情: {json.dumps(session.judge_result.scores_summary, ensure_ascii=False)}"
        )

        logger.info("开始裁判总结阶段 session_id=%s", session_id)

        judge = self._make_judge_agent(session.config.judge_id)
        context = DebateAgent.build_judge_summary_context(
            question=question,
            full_transcript=transcript,
            tally_result=tally_result,
        )

        try:
            summary_text = judge.invoke_text(context, judge.load_task_prompt("judge_summary"))
        except AgentError as exc:
            logger.error("裁判总结失败: %s", exc)
            summary_text = f"[裁判总结生成失败: {exc}]"

        session.judge_result.summary = summary_text

        # 添加裁判消息
        msg = self._new_message(
            phase=DebatePhase.JUDGE_SUMMARY,
            role=MessageRole.JUDGE,
            speaker_id=session.judge.id,
            speaker_name=session.judge.name,
            content=summary_text,
            sequence=len(session.messages) + 1,
        )
        self._store.add_message(session_id, msg)

        # 标记完成
        self._store.mark_complete(session_id)
        state.transition_to(DebatePhase.COMPLETE)

        logger.info("裁判总结完成 session_id=%s", session_id)
        return self._store.get(session_id)

    async def stream_judge(self, session_id: str) -> AsyncIterator[dict[str, Any]]:
        """流式执行裁判阶段（统计 + 总结）。"""
        session = self.get_session(session_id)
        state = self._get_state(session_id)

        # Judge Tally
        result = state.transition_to(DebatePhase.JUDGE_TALLY)
        if not result.success:
            yield {"event": "error", "data": {"message": result.message}}
            return

        question = session.config.question
        transcript = DebateAgent.format_transcript(session.messages)

        if session.judge_result is None or not session.judge_result.votes:
            yield {"event": "status", "data": {"message": "等待投票结果..."}}

        votes = session.judge_result.votes if session.judge_result else []
        votes_text = "\n".join(
            f"- {v.voter_name} 投票给 {v.voted_for_name}，理由：{v.reason}，评分：{v.scores}"
            for v in votes
        )

        yield {"event": "judge_tally_start", "data": {}}

        judge = self._make_judge_agent(session.config.judge_id)
        context = DebateAgent.build_judge_tally_context(
            question=question,
            full_transcript=transcript,
            votes_text=votes_text,
        )

        try:
            tally_output = judge.invoke_structured(
                context, _TallyOutput, judge.load_task_prompt("judge_tally"),
            )
            if session.judge_result is None:
                session.judge_result = JudgeResult(winner_id="", winner_name="", summary="")
            session.judge_result.winner_id = tally_output.winner_id
            session.judge_result.winner_name = tally_output.winner_name
            session.judge_result.scores_summary = tally_output.votes_summary
            yield {
                "event": "judge_tally_complete",
                "data": {
                    "winner_id": tally_output.winner_id,
                    "winner_name": tally_output.winner_name,
                    "scores_summary": tally_output.votes_summary,
                },
            }
        except AgentError as exc:
            logger.error("裁判统计失败: %s", exc)
            yield {"event": "error", "data": {"message": str(exc)}}

        self._store.update_phase(session_id, "judge_tally", state.current_round)

        # Judge Summary
        state.transition_to(DebatePhase.JUDGE_SUMMARY)

        tally_info = (
            f"获胜者: {session.judge_result.winner_name}\n"
            f"投票详情: {json.dumps(session.judge_result.scores_summary, ensure_ascii=False)}"
        )
        summary_context = DebateAgent.build_judge_summary_context(
            question=question,
            full_transcript=transcript,
            tally_result=tally_info,
        )

        yield {
            "event": "judge_summary_start",
            "data": {"judge_name": session.judge.name},
        }

        full_summary: list[str] = []
        try:
            async for token in judge.invoke_stream(
                summary_context, judge.load_task_prompt("judge_summary"),
            ):
                full_summary.append(token)
                yield {
                    "event": "message_delta",
                    "data": {
                        "speaker_id": session.judge.id,
                        "speaker_name": session.judge.name,
                        "phase": "judge_summary",
                        "token": token,
                    },
                }
        except AgentError as exc:
            logger.error("裁判总结流式失败: %s", exc)
            yield {"event": "error", "data": {"message": str(exc)}}

        summary_text = "".join(full_summary)
        session.judge_result.summary = summary_text

        msg = self._new_message(
            phase=DebatePhase.JUDGE_SUMMARY,
            role=MessageRole.JUDGE,
            speaker_id=session.judge.id,
            speaker_name=session.judge.name,
            content=summary_text,
            sequence=len(session.messages) + 1,
        )
        self._store.add_message(session_id, msg)

        self._store.mark_complete(session_id)
        state.transition_to(DebatePhase.COMPLETE)

        yield {
            "event": "phase_complete",
            "data": {"phase": "judge", "session_id": session_id, "winner": session.judge_result.winner_name},
        }

    # ================================================================
    # Full Debate（一键运行）
    # ================================================================

    def run_full_debate(self, session_id: str) -> DebateSession:
        """一键运行完整辩论流程（同步版）。

        按顺序执行：OPENING → CROSS_EXAMINATION (所有轮次) → CLOSING → VOTING → JUDGE

        Returns:
            包含完整辩论结果的 DebateSession
        """
        session = self.get_session(session_id)
        total_rounds = session.config.cross_examination_rounds

        logger.info("开始完整辩论 session_id=%s rounds=%s", session_id, total_rounds)

        # 1. 立论
        self.run_opening(session_id)

        # 2. 交叉质询（所有轮次）
        for rnd in range(1, total_rounds + 1):
            self.run_cross_examination(session_id, round_num=rnd)

        # 3. 结辩
        self.run_closing(session_id)

        # 4. 投票
        self.run_voting(session_id)

        # 5. 裁判统计 + 总结
        self.run_judge_tally(session_id)
        self.run_judge_summary(session_id)

        final_session = self.get_session(session_id)
        logger.info(
            "完整辩论结束 session_id=%s winner=%s messages=%s",
            session_id,
            final_session.judge_result.winner_name if final_session.judge_result else "N/A",
            len(final_session.messages),
        )
        return final_session


__all__ = ["DebateService"]