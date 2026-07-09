"""辩论会话存储 — 内存级 CRUD + 持久化 + TTL 清理。

每场辩论用一个 DebateSession 对象管理全部消息和状态。
辩论完成后自动持久化到 JSON 文件，内存会话在 30 分钟后自动清理。
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path

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
    """线程安全的内存会话存储，含持久化和 TTL 清理。"""

    _ttl_seconds: int = 1800  # 30 分钟
    _archive_dir: str = ""  # 由 __init__ 设置

    def __init__(self, archive_dir: str = "") -> None:
        self._sessions: dict[str, DebateSession] = {}
        self._lock = threading.Lock()
        # 存档目录默认在 backend/debate/sessions/archive/
        if not archive_dir:
            archive_dir = str(Path(__file__).resolve().parent / "archive")
        self._archive_dir = archive_dir

    # ---- CRUD ----------------------------------------------------------------

    def create(self, session: DebateSession) -> DebateSession:
        """保存新会话（session_id 必须已设置），触发宽松的过期清理。"""
        with self._lock:
            self._maybe_cleanup()
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
        """列出所有活跃内存会话。"""
        with self._lock:
            return list(self._sessions.values())

    def delete(self, session_id: str) -> None:
        """删除内存会话，不存在时抛异常。"""
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
        """标记会话完成并自动持久化。"""
        from datetime import datetime

        from debate.api.schemas import DebatePhase

        session = self.get(session_id)
        with self._lock:
            session.current_phase = DebatePhase.COMPLETE
            if not session.completed_at:
                session.completed_at = datetime.utcnow()
        # 完成后自动持久化
        self.persist(session_id)
        return session

    # ---- 工具 ----------------------------------------------------------------

    @staticmethod
    def new_session_id() -> str:
        """生成新的会话 ID。"""
        return f"debate_{uuid.uuid4().hex[:12]}"

    def exists(self, session_id: str) -> bool:
        """检查会话是否存在于内存中。"""
        with self._lock:
            return session_id in self._sessions

    # ---- TTL 过期清理 --------------------------------------------------------

    def _maybe_cleanup(self) -> None:
        """宽松的过期清理：每次 create() 时触发一次。"""
        now = time.time()
        expired = [
            sid
            for sid, s in self._sessions.items()
            if now - s.created_at.timestamp() > self._ttl_seconds
        ]
        for sid in expired:
            del self._sessions[sid]

    def cleanup_expired(self) -> int:
        """强制清理所有过期会话，返回清理数量。"""
        now = time.time()
        with self._lock:
            expired = [
                sid
                for sid, s in self._sessions.items()
                if now - s.created_at.timestamp() > self._ttl_seconds
            ]
            for sid in expired:
                del self._sessions[sid]
        return len(expired)

    # ---- 持久化 --------------------------------------------------------------

    def persist(self, session_id: str) -> str:
        """将完成后的会话序列化到磁盘 JSON 文件，返回文件路径。

        如果会话尚未完成，仍可持久化（用于异常处理等场景）。
        """
        session = self.get_or_none(session_id)
        if not session:
            raise SessionNotFoundError(f"会话不存在: {session_id}")

        data = self._serialize_session(session)
        path = os.path.join(self._archive_dir, f"{session_id}.json")
        os.makedirs(self._archive_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    def load_archived(self, session_id: str) -> dict | None:
        """从磁盘加载已存档会话（用于导出接口）。

        Returns:
            序列化的会话数据 dict，或 None（文件不存在时）。
        """
        path = os.path.join(self._archive_dir, f"{session_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_archived(self, limit: int = 50) -> list[dict]:
        """列出最近存档的会话摘要。

        Returns:
            摘要列表，每项含 session_id / question / status / created_at / debater_count / judge。
        """
        summaries: list[dict] = []
        archive_dir = Path(self._archive_dir)
        if not archive_dir.exists():
            return summaries

        files = sorted(
            archive_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:limit]

        for f in files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
            except (json.JSONDecodeError, OSError):
                continue

            summaries.append(
                {
                    "session_id": data.get("session_id", f.stem),
                    "question": data.get("config", {}).get("question", ""),
                    "status": data.get("status", "unknown"),
                    "created_at": data.get("created_at", ""),
                    "debater_count": len(data.get("config", {}).get("debaters", [])),
                    "judge": data.get("config", {}).get("judge", {}).get("name", ""),
                }
            )
        return summaries

    def is_archived(self, session_id: str) -> bool:
        """检查会话是否已持久化到磁盘。"""
        path = os.path.join(self._archive_dir, f"{session_id}.json")
        return os.path.exists(path)

    # ---- 序列化 --------------------------------------------------------------

    @staticmethod
    def _serialize_session(session: DebateSession) -> dict:
        """将 DebateSession 转为可 JSON 序列化的 dict。

        生成的 JSON 结构与 API 规范中的 GET /sessions/{id} 响应一致。
        """
        config = session.config
        debaters_data = []
        for d in session.debaters:
            debaters_data.append(
                {
                    "id": d.id,
                    "name": d.name,
                    "school": d.school or "",
                    "avatar": "🎭",
                    "persona_short": d.description or "",
                }
            )

        judge_data = {
            "id": session.judge.id,
            "name": session.judge.name,
            "avatar": "⚖️",
            "persona_short": session.judge.description or "",
        }

        # 按阶段组织消息
        stages: dict[str, dict] = {
            "opening": {"phase": "opening", "label": "📜 立论", "messages": []},
            "cross_examine": {
                "phase": "cross_examine",
                "label": "⚔️ 质询",
                "rounds": config.cross_examination_rounds,
                "qa_pairs": [],
            },
            "closing": {"phase": "closing", "label": "🏁 结辩", "messages": []},
            "voting": {"phase": "voting", "label": "🗳️ 投票", "votes": []},
            "judge_summary": {
                "phase": "judge_summary",
                "label": "📝 裁判总结",
                "content": "",
            },
        }

        for msg in session.messages:
            phase_str = msg.phase.value if hasattr(msg.phase, "value") else str(msg.phase)

            if phase_str == "opening":
                stages["opening"]["messages"].append(
                    _serialize_message(msg)
                )
            elif phase_str in ("cross_ask", "cross_answer"):
                pass  # CrossQA 从 session.cross_qas 生成
            elif phase_str == "closing":
                stages["closing"]["messages"].append(
                    _serialize_message(msg)
                )
            elif phase_str == "voting":
                pass  # votes 从 session.judge_result 生成
            elif phase_str in ("judge_tally", "judge_summary"):
                stages["judge_summary"]["content"] = msg.content

        # 质询问答对
        for qa in session.cross_qas:
            stages["cross_examine"]["qa_pairs"].append(
                {
                    "round": qa.round,
                    "asker": {"id": qa.asker_id, "name": qa.asker_name},
                    "answerer": {"id": qa.answerer_id, "name": qa.answerer_name},
                    "question": qa.question.content if qa.question else "",
                    "answer": qa.answer.content if qa.answer else "",
                }
            )

        # 投票记录与统计
        tally: dict[str, int] = {}
        votes_list: list[dict] = []

        if session.judge_result:
            for vote in session.judge_result.votes:
                votes_list.append(
                    {
                        "voter": vote.voter_id,
                        "vote_for": vote.voted_for_id,
                        "reason": vote.reason,
                    }
                )
                tally[vote.voted_for_id] = tally.get(vote.voted_for_id, 0) + 1

        # 奖项
        awards: dict[str, dict] = {}
        # 最佳论点奖：得票最多者
        if tally:
            best_id = max(tally, key=lambda k: tally[k])
            best_name = ""
            for d in session.debaters:
                if d.id == best_id:
                    best_name = d.name
                    break
            awards["best_argument"] = {
                "recipient": best_id,
                "reason": f"获得最多票数（{tally[best_id]} 票），论证最具说服力",
            }

        stages["voting"] = {
            "phase": "voting",
            "label": "🗳️ 投票",
            "votes": votes_list,
            "tally": tally,
            "awards": awards,
        }

        # 裁判总结文本
        judge_summary_text = ""
        if session.judge_result:
            judge_summary_text = session.judge_result.summary or ""
        stages["judge_summary"]["content"] = judge_summary_text

        # Markdown 导出内容（预生成）
        markdown = _generate_markdown(
            session_id=session.session_id,
            question=session.config.question,
            debaters=debaters_data,
            judge=judge_data,
            created_at=session.created_at.isoformat() if session.created_at else "",
            stages=stages,
            tally=tally,
            awards=awards,
        )

        return {
            "session_id": session.session_id,
            "question": session.config.question,
            "status": "completed" if session.is_complete else "running",
            "created_at": session.created_at.isoformat() if session.created_at else "",
            "completed_at": session.completed_at.isoformat()
            if session.completed_at
            else None,
            "duration_seconds": (
                (session.completed_at - session.created_at).total_seconds()
                if session.completed_at and session.created_at
                else None
            ),
            "config": {
                "debaters": debaters_data,
                "judge": judge_data,
                "cross_examination_rounds": config.cross_examination_rounds,
            },
            "stages": stages,
            "export": {
                "markdown": markdown,
                "markdown_url": f"/api/debate/sessions/{session.session_id}/export?format=md",
                "json_url": f"/api/debate/sessions/{session.session_id}/export?format=json",
                "pdf_url": f"/api/debate/sessions/{session.session_id}/export?format=pdf",
            },
        }


# ---- 序列化辅助函数 ----------------------------------------------------------


def _serialize_message(msg: Message) -> dict:
    """将单条消息序列化为 API 规范的 dict 格式。"""
    return {
        "id": msg.id,
        "timestamp": msg.timestamp.isoformat() if msg.timestamp else "",
        "speaker": {
            "id": msg.speaker_id,
            "name": msg.speaker_name,
            "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
            "avatar": _avatar_for_role(msg.role),
        },
        "target": {"id": msg.target_id, "name": msg.target_name or "所有人"},
        "content": msg.content,
    }


def _avatar_for_role(role) -> str:
    """根据消息角色返回 emoji 头像。"""
    if hasattr(role, "value"):
        role_str = role.value
    else:
        role_str = str(role)

    mapping = {
        "debater": "🎭",
        "judge": "⚖️",
        "system": "🤖",
        "user": "👤",
    }
    return mapping.get(role_str, "💬")


# ---- Markdown 生成 -----------------------------------------------------------


def _generate_markdown(
    session_id: str,
    question: str,
    debaters: list[dict],
    judge: dict,
    created_at: str,
    stages: dict,
    tally: dict[str, int],
    awards: dict,
) -> str:
    """将辩论会话数据渲染为完整的 Markdown 记录。

    Returns:
        格式化的 Markdown 字符串，供前端展示和 PDF 导出用。
    """
    lines: list[str] = []

    # 标题
    lines.append(f"# 多Agent辩论：{question}")
    lines.append("")

    # 元信息
    created_display = created_at[:19].replace("T", " ") if created_at else ""
    lines.append(f"**辩论ID**：`{session_id}`")
    lines.append(f"**辩论时间**：{created_display}")
    _names = '、'.join(f'{d["name"]}（{d.get("school", "")}）' for d in debaters)
    lines.append(f"**辩者**：{_names}")
    lines.append(f"**裁判**：{judge.get('name', '')}")
    lines.append("")

    # ---- 立论 ----
    opening = stages.get("opening", {})
    lines.append("## 📜 立论")
    lines.append("")
    for msg in opening.get("messages", []):
        speaker = msg.get("speaker", {})
        school_info = ""
        for d in debaters:
            if d["id"] == speaker.get("id"):
                school_info = d.get("school", "")
                break
        school_suffix = f" · {school_info}" if school_info else ""
        lines.append(f"### {speaker.get('avatar', '🎭')} {speaker.get('name', '')}{school_suffix}")
        lines.append("")
        lines.append(msg.get("content", ""))
        lines.append("")

    # ---- 质询 ----
    cross = stages.get("cross_examine", {})
    if cross.get("qa_pairs"):
        lines.append("## ⚔️ 质询")
        lines.append("")
        for qa in cross.get("qa_pairs", []):
            round_num = qa.get("round", 1)
            asker = qa.get("asker", {})
            answerer = qa.get("answerer", {})
            lines.append(f"### 第 {round_num} 轮：{asker.get('name', '')} → @{answerer.get('name', '')}")
            lines.append("")
            lines.append(f"**问**：{qa.get('question', '')}")
            lines.append("")
            lines.append(f"**答**：{qa.get('answer', '')}")
            lines.append("")

    # ---- 结辩 ----
    closing = stages.get("closing", {})
    if closing.get("messages"):
        lines.append("## 🏁 结辩")
        lines.append("")
        for msg in closing.get("messages", []):
            speaker = msg.get("speaker", {})
            lines.append(f"### {speaker.get('avatar', '🎭')} {speaker.get('name', '')}")
            lines.append("")
            lines.append(msg.get("content", ""))
            lines.append("")

    # ---- 投票 ----
    voting = stages.get("voting", {})
    if voting.get("votes"):
        lines.append("## 🗳️ 投票")
        lines.append("")
        # 票数统计表
        lines.append("| 辩者 | 得票 | 投票者 |")
        lines.append("|------|------|--------|")
        name_map = {d["id"]: d["name"] for d in debaters}
        for debater_id, name in name_map.items():
            count = tally.get(debater_id, 0)
            voters = [v["voter"] for v in voting["votes"] if v["vote_for"] == debater_id]
            voter_names = [name_map.get(v, v) for v in voters]
            lines.append(f"| {name} | {count} 票 | {'、'.join(voter_names) if voter_names else '—'} |")
        lines.append("")

        # 奖项
        if awards:
            for award_key, award in awards.items():
                recipient_id = award.get("recipient", "")
                recipient_name = name_map.get(recipient_id, recipient_id)
                icon = "🏆" if award_key == "best_argument" else "🎯"
                label = "最佳论点奖" if award_key == "best_argument" else "最佳质询奖"
                lines.append(f"**{icon} {label}**：{recipient_name} — {award.get('reason', '')}")
                lines.append("")

    # ---- 裁判总结 ----
    judge_summary = stages.get("judge_summary", {})
    if judge_summary.get("content"):
        lines.append("## 📝 裁判总结")
        lines.append("")
        lines.append(judge_summary["content"])
        lines.append("")

    return "\n".join(lines)


__all__ = ["SessionStore", "SessionNotFoundError"]