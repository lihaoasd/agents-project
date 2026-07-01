"""辩论会话存储 — 内存级 CRUD。

每场辩论用一个 DebateSession 对象管理全部消息和状态。
"""

from __future__ import annotations

import threading
import uuid

from debate.api.schemas import (
    CrossQA,
    DebateSession,
    JudgeResult,
    Message,
    VoteEntry,
)


class SessionNotFoundError(Exception):
    """会话不存在异常。"""


class SessionStore:
    """线程安全的内存会话存储。"""

    def __init__(self) -> None:
        self._sessions: dict[str, DebateSession] = {}
        self._lock = threading.Lock()

    # ---- CRUD ----------------------------------------------------------------

    def create(self, session: DebateSession) -> DebateSession:
        """保存新会话（session_id 必须已设置）。"""
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> DebateSession:
        """获取会话，不存在时抛异常。"""
        with self._lock:
            if session_id not in self._sessions:
                raise SessionNotFoundError(f"会话不存在: {session_id}")
            return self._sessions[session_id]

    def get_or_none(self, session_id: str) -> DebateSession | None:
        """获取会话，不存在返回 None。"""
        with self._lock:
            return self._sessions.get(session_id)

    def list_all(self) -> list[DebateSession]:
        """列出所有会话。"""
        with self._lock:
            return list(self._sessions.values())

    def delete(self, session_id: str) -> None:
        """删除会话，不存在时抛异常。"""
        with self._lock:
            if session_id not in self._sessions:
                raise SessionNotFoundError(f"会话不存在: {session_id}")
            del self._sessions[session_id]

    # ---- 消息追加 ------------------------------------------------------------

    def add_message(self, session_id: str, message: Message) -> DebateSession:
        """向会话追加一条消息。"""
        session = self.get(session_id)
        with self._lock:
            session.messages.append(message)
        return session

    # ---- 交叉质询 ------------------------------------------------------------

    def add_cross_qa(self, session_id: str, qa: CrossQA) -> DebateSession:
        """向会话追加一对交叉质询问答。"""
        session = self.get(session_id)
        with self._lock:
            session.cross_qas.append(qa)
        return session

    # ---- 裁判结果 ------------------------------------------------------------

    def set_judge_result(self, session_id: str, result: JudgeResult) -> DebateSession:
        """设置裁判结果。"""
        session = self.get(session_id)
        with self._lock:
            session.judge_result = result
        return session

    # ---- 阶段更新 ------------------------------------------------------------

    def update_phase(self, session_id: str, phase: str, round_num: int) -> DebateSession:
        """更新会话的当前阶段和轮次。"""
        from debate.api.schemas import DebatePhase

        session = self.get(session_id)
        with self._lock:
            session.current_phase = DebatePhase(phase)
            session.current_round = round_num
        return session

    def mark_complete(self, session_id: str) -> DebateSession:
        """标记会话完成。"""
        from datetime import datetime

        from debate.api.schemas import DebatePhase

        session = self.get(session_id)
        with self._lock:
            session.current_phase = DebatePhase.COMPLETE
            if not session.completed_at:
                session.completed_at = datetime.utcnow()
        return session

    # ---- 工具 ----------------------------------------------------------------

    @staticmethod
    def new_session_id() -> str:
        """生成新的会话 ID。"""
        return f"debate_{uuid.uuid4().hex[:12]}"

    def exists(self, session_id: str) -> bool:
        """检查会话是否存在。"""
        with self._lock:
            return session_id in self._sessions


__all__ = ["SessionStore", "SessionNotFoundError"]