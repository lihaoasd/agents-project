"""辩论 API 路由。

端点：
- GET  /health                    健康检查
- GET  /roles                     获取可选角色列表
- POST /start                     创建辩论会话
- GET  /stream/{session_id}       SSE 实时辩论流
- GET  /sessions/{session_id}     获取完整辩论记录
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from debate.agent import DebateAgent
from debate.api.schemas import (
    DebateConfig,
    DebatePhase,
    JudgeResult,
    Message,
    MessageRole,
    VoteEntry,
)
from debate.prompts import load_index
from debate.service.debate_service import (
    DebateService,
    _TallyOutput,
    _VoteOutput,
)
from debate.session.store import SessionNotFoundError

router = APIRouter(prefix="/api/debate", tags=["debate"])

# 模块级服务单例
_service = DebateService()


# ============================================================
# 请求模型
# ============================================================


class StartRequest(BaseModel):
    """POST /start 请求体。"""

    question: str = Field(..., min_length=1, max_length=2000, description="辩论问题")
    debater_ids: list[str] = Field(
        ..., min_length=2, max_length=6, description="辩者 ID 列表"
    )
    judge_id: str = Field(..., description="裁判 ID")
    cross_examination_rounds: int = Field(
        default=1, ge=1, le=5, description="交叉质询轮次"
    )


# ============================================================
# 7.0: Health
# ============================================================


@router.get("/health", summary="辩论模块健康检查")
async def health() -> dict[str, str | bool]:
    """返回辩论模块健康状态。"""
    return {"status": "ok", "module": "debate"}


# ============================================================
# 7.1: GET /api/debate/roles
# ============================================================


@router.get("/roles", summary="获取可选角色列表")
async def get_roles() -> dict[str, list[dict[str, Any]]]:
    """返回可选辩者 + 裁判列表。"""
    debaters = load_index("roles/debater")
    judges = load_index("roles/judge")
    return {"debaters": debaters, "judges": judges}


# ============================================================
# 7.2: POST /api/debate/start
# ============================================================


@router.post("/start", summary="创建辩论会话")
async def start_debate(req: StartRequest) -> dict[str, Any]:
    """创建新辩论会话并返回 session_id 与参与者列表。"""
    try:
        config = DebateConfig(
            question=req.question,
            debater_ids=req.debater_ids,
            judge_id=req.judge_id,
            cross_examination_rounds=req.cross_examination_rounds,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        session = _service.create_session(config)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "session_id": session.session_id,
        "question": session.config.question,
        "debaters": [d.model_dump() for d in session.debaters],
        "judge": session.judge.model_dump(),
        "cross_examination_rounds": session.config.cross_examination_rounds,
    }


# ============================================================
# SSE 工具函数
# ============================================================


def _sse_line(event: str, data: dict[str, Any] | str) -> str:
    """构建一条 SSE 消息行。"""
    if isinstance(data, dict):
        data_str = json.dumps(data, ensure_ascii=False)
    else:
        data_str = data
    return f"event: {event}\ndata: {data_str}\n\n"


def _store_message(
    session_id: str,
    phase: DebatePhase,
    role: MessageRole,
    speaker: Any,
    content: str,
    target: Any | None = None,
) -> None:
    """将消息存入 SessionStore。"""
    msg = Message(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        phase=phase,
        role=role,
        speaker_id=speaker.id,
        speaker_name=speaker.name,
        target_id=target.id if target else "all",
        target_name=target.name if target else "",
        content=content,
        timestamp=datetime.utcnow(),
        sequence=0,
    )
    _service._store.add_message(session_id, msg)


async def _stream_parallel_speakers(
    session_id: str,
    phase: DebatePhase,
    speakers: list[Any],
    build_context: Any,
    stage: str,
) -> AsyncIterator[str]:
    """并行流式输出多个发言者。

    使用 asyncio.Queue 实现真正的并行：
    所有发言者同时调用 LLM，token 到达顺序即为推送顺序。
    """
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def stream_one(speaker: Any) -> str:
        agent = DebateService._make_debater_agent(speaker.id)
        user_content = build_context(speaker)
        task_prompt = agent.load_task_prompt(stage)

        await queue.put(
            {
                "type": "speaker_start",
                "speaker_id": speaker.id,
                "speaker_name": speaker.name,
                "phase": phase.value,
            }
        )

        tokens: list[str] = []
        try:
            async for token in agent.invoke_stream(user_content, task_prompt):
                tokens.append(token)
                await queue.put(
                    {
                        "type": "token",
                        "speaker_id": speaker.id,
                        "speaker_name": speaker.name,
                        "phase": phase.value,
                        "token": token,
                    }
                )
        except Exception as exc:
            await queue.put(
                {
                    "type": "error",
                    "speaker_id": speaker.id,
                    "message": str(exc),
                }
            )

        content = "".join(tokens)
        _store_message(
            session_id=session_id,
            phase=phase,
            role=MessageRole.DEBATER,
            speaker=speaker,
            content=content,
        )

        await queue.put(
            {
                "type": "speaker_end",
                "speaker_id": speaker.id,
                "speaker_name": speaker.name,
                "full_content": content,
            }
        )
        return content

    tasks = [asyncio.create_task(stream_one(s)) for s in speakers]
    completed = 0

    while completed < len(speakers):
        item = await queue.get()
        event_type = item.pop("type")
        if event_type == "token":
            yield _sse_line("message_delta", item)
        elif event_type == "speaker_start":
            yield _sse_line("speaker_start", item)
        elif event_type == "speaker_end":
            completed += 1
            yield _sse_line("speaker_end", item)
        elif event_type == "error":
            yield _sse_line("error", item)

    await asyncio.gather(*tasks, return_exceptions=True)


async def _replay_all_messages(session: Any) -> AsyncIterator[str]:
    """补发所有已完成的消息。"""
    yield _sse_line(
        "status",
        {
            "message": f"辩论已进行到 {session.current_phase.value} 阶段",
            "phase": session.current_phase.value,
            "replay": True,
        },
    )

    for msg in session.messages:
        yield _sse_line(
            "message_replay",
            {
                "msg_id": msg.id,
                "speaker_id": msg.speaker_id,
                "speaker_name": msg.speaker_name,
                "target_id": msg.target_id,
                "target_name": msg.target_name,
                "phase": msg.phase.value,
                "role": msg.role.value,
                "full_content": msg.content,
            },
        )


async def _replay_messages(session: Any, resume_from: str) -> AsyncIterator[str]:
    """从指定消息之后补发消息（断线重连）。"""
    found = False
    for msg in session.messages:
        if not found:
            if msg.id == resume_from:
                found = True
            continue
        yield _sse_line(
            "message_replay",
            {
                "msg_id": msg.id,
                "speaker_id": msg.speaker_id,
                "speaker_name": msg.speaker_name,
                "target_id": msg.target_id,
                "target_name": msg.target_name,
                "phase": msg.phase.value,
                "role": msg.role.value,
                "full_content": msg.content,
            },
        )


# ============================================================
# 7.3: GET /api/debate/stream/{session_id} — SSE 核心端点
# ============================================================


@router.get("/stream/{session_id}", summary="SSE 实时辩论流")
async def stream_debate(
    session_id: str,
    resume_from: str = Query(default="", description="断线重连的最后一个 msg_id"),
):
    """连接 SSE 实时辩论流，自动运行完整辩论流程。

    事件类型：
        - phase_start / phase_complete: 阶段开始/结束
        - speaker_start / speaker_end: 发言者开始/结束
        - message_delta: 增量 token
        - message_replay: 历史消息补发
        - vote_start / vote_complete: 投票
        - judge_tally_start / judge_tally_complete: 裁判统计
        - done: 辩论完成
        - error: 错误
    """
    return StreamingResponse(
        _stream_full_debate(session_id, resume_from),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _stream_full_debate(
    session_id: str, resume_from: str = ""
) -> AsyncIterator[str]:
    """运行完整辩论并生成 SSE 事件流。"""
    try:
        session = _service.get_session(session_id)
    except SessionNotFoundError:
        yield _sse_line("error", {"message": f"会话不存在: {session_id}"})
        return

    total_rounds = session.config.cross_examination_rounds
    question = session.config.question
    debaters = session.debaters
    judge = session.judge

    # 断线重连：补发错过的消息
    if resume_from:
        async for line in _replay_messages(session, resume_from):
            yield line
        if session.is_complete:
            jr = session.judge_result
            yield _sse_line(
                "done",
                {
                    "session_id": session_id,
                    "winner_id": jr.winner_id if jr else "",
                    "winner_name": jr.winner_name if jr else "",
                    "replay": True,
                },
            )
            return
    elif session.messages:
        async for line in _replay_all_messages(session):
            yield line

    if session.is_complete:
        jr = session.judge_result
        yield _sse_line(
            "done",
            {
                "session_id": session_id,
                "winner_id": jr.winner_id if jr else "",
                "winner_name": jr.winner_name if jr else "",
            },
        )
        return

    # ============================================================
    # Phase 1: Opening — 并行立论
    # ============================================================
    _service._store.update_phase(session_id, "opening", 0)
    yield _sse_line("phase_start", {"phase": "opening", "label": "立论陈词"})
    async for line in _stream_parallel_speakers(
        session_id=session_id,
        phase=DebatePhase.OPENING,
        speakers=debaters,
        build_context=lambda d: DebateAgent.build_opening_context(question),
        stage="opening",
    ):
        yield line
    _service._store.update_phase(session_id, "cross_examination", round_num=0)
    yield _sse_line("phase_complete", {"phase": "opening"})
    print("openings")
    # ============================================================
    # Phase 2-3: Cross-Examination — 逐对质询
    # ============================================================
    openings: dict[str, str] = {}
    for msg in _service.get_session(session_id).messages:
        if msg.phase == DebatePhase.OPENING:
            openings[msg.speaker_id] = msg.content
    print(openings)
    pairs: list[tuple[Any, Any]] = []
    for asker in debaters:
        for answerer in debaters:
            if asker.id != answerer.id:
                pairs.append((asker, answerer))

    for round_num in range(1, total_rounds + 1):
        _service._store.update_phase(
            session_id, "cross_examination", round_num=round_num
        )
        yield _sse_line(
            "phase_start",
            {
                "phase": "cross_examination",
                "round": round_num,
                "label": f"交叉质询 第{round_num}轮",
            },
        )

        for asker, answerer in pairs:
            # Cross Ask
            ask_agent = DebateService._make_debater_agent(asker.id)
            ask_context = DebateAgent.build_cross_ask_context(question, openings)

            yield _sse_line(
                "speaker_start",
                {
                    "speaker_id": asker.id,
                    "speaker_name": asker.name,
                    "target_id": answerer.id,
                    "target_name": answerer.name,
                    "phase": "cross_ask",
                    "round": round_num,
                },
            )

            ask_tokens: list[str] = []
            try:
                async for token in ask_agent.invoke_stream(
                    ask_context, ask_agent.load_task_prompt("cross_ask")
                ):
                    ask_tokens.append(token)
                    yield _sse_line(
                        "message_delta",
                        {
                            "speaker_id": asker.id,
                            "speaker_name": asker.name,
                            "target_id": answerer.id,
                            "phase": "cross_ask",
                            "round": round_num,
                            "token": token,
                        },
                    )
            except Exception as exc:
                yield _sse_line(
                    "error",
                    {
                        "speaker_id": asker.id,
                        "message": str(exc),
                    },
                )

            ask_content = "".join(ask_tokens)
            _store_message(
                session_id=session_id,
                phase=DebatePhase.CROSS_ASK,
                role=MessageRole.DEBATER,
                speaker=asker,
                content=ask_content,
                target=answerer,
            )
            yield _sse_line(
                "speaker_end",
                {
                    "speaker_id": asker.id,
                    "phase": "cross_ask",
                    "full_content": ask_content,
                },
            )

            # Cross Answer
            ans_agent = DebateService._make_debater_agent(answerer.id)
            ans_context = DebateAgent.build_cross_answer_context(
                question=question,
                my_opening=openings.get(answerer.id, ""),
                asker_name=asker.name,
                ask_question=ask_content,
            )

            yield _sse_line(
                "speaker_start",
                {
                    "speaker_id": answerer.id,
                    "speaker_name": answerer.name,
                    "target_id": asker.id,
                    "target_name": asker.name,
                    "phase": "cross_answer",
                    "round": round_num,
                },
            )

            ans_tokens: list[str] = []
            try:
                async for token in ans_agent.invoke_stream(
                    ans_context, ans_agent.load_task_prompt("cross_answer")
                ):
                    ans_tokens.append(token)
                    yield _sse_line(
                        "message_delta",
                        {
                            "speaker_id": answerer.id,
                            "speaker_name": answerer.name,
                            "target_id": asker.id,
                            "phase": "cross_answer",
                            "round": round_num,
                            "token": token,
                        },
                    )
            except Exception as exc:
                yield _sse_line(
                    "error",
                    {
                        "speaker_id": answerer.id,
                        "message": str(exc),
                    },
                )

            ans_content = "".join(ans_tokens)
            _store_message(
                session_id=session_id,
                phase=DebatePhase.CROSS_ANSWER,
                role=MessageRole.DEBATER,
                speaker=answerer,
                content=ans_content,
                target=asker,
            )
            yield _sse_line(
                "speaker_end",
                {
                    "speaker_id": answerer.id,
                    "phase": "cross_answer",
                    "full_content": ans_content,
                },
            )

        _service._store.update_phase(session_id, "closing", total_rounds)
        yield _sse_line(
            "phase_complete",
            {
                "phase": "cross_examination",
                "round": round_num,
            },
        )

    # ============================================================
    # Phase 4: Closing — 并行结辩
    # ============================================================
    yield _sse_line("phase_start", {"phase": "closing", "label": "结辩陈词"})

    latest_session = _service.get_session(session_id)
    cross_qas_map: dict[str, list[str]] = {}
    for qa in latest_session.cross_qas:
        if qa.answerer_id not in cross_qas_map:
            cross_qas_map[qa.answerer_id] = []
        q_text = qa.question.content if qa.question else ""
        a_text = qa.answer.content if qa.answer else ""
        cross_qas_map[qa.answerer_id].append(
            f"轮次{qa.round} | {qa.asker_name} 问：{q_text}\n"
            f"轮次{qa.round} | 你答：{a_text}"
        )

    async for line in _stream_parallel_speakers(
        session_id=session_id,
        phase=DebatePhase.CLOSING,
        speakers=debaters,
        build_context=lambda d: DebateAgent.build_closing_context(
            question=question,
            my_opening=openings.get(d.id, ""),
            cross_examinations="\n".join(
                cross_qas_map.get(d.id, ["（无相关质询记录）"])
            ),
        ),
        stage="closing",
    ):
        yield line
    _service._store.update_phase(session_id, "voting", total_rounds)
    yield _sse_line("phase_complete", {"phase": "closing"})

    # ============================================================
    # Phase 5: Voting — 投票
    # ============================================================
    yield _sse_line("phase_start", {"phase": "voting", "label": "投票"})

    transcript = DebateAgent.format_transcript(
        _service.get_session(session_id).messages
    )
    all_votes: list[dict[str, Any]] = []

    for debater in debaters:
        candidates = [d for d in debaters if d.id != debater.id]
        agent = DebateService._make_debater_agent(debater.id)
        context = DebateAgent.build_vote_context(
            question=question,
            full_transcript=transcript,
            exclude_name=debater.name,
            candidate_names=[d.name for d in candidates],
        )

        yield _sse_line(
            "vote_start",
            {
                "voter_id": debater.id,
                "voter_name": debater.name,
            },
        )

        try:
            vote_output = agent.invoke_structured(
                context, _VoteOutput, agent.load_task_prompt("vote")
            )
            vote_data: dict[str, Any] = {
                "voter_id": debater.id,
                "voter_name": debater.name,
                "voted_for_id": vote_output.voted_for_id,
                "voted_for_name": vote_output.voted_for_name,
                "scores": vote_output.scores,
                "reason": vote_output.reason,
            }
        except Exception as exc:
            fallback = candidates[0]
            vote_data = {
                "voter_id": debater.id,
                "voter_name": debater.name,
                "voted_for_id": fallback.id,
                "voted_for_name": fallback.name,
                "scores": {},
                "reason": f"[投票生成失败: {exc}]",
            }

        all_votes.append(vote_data)
        yield _sse_line("vote_complete", vote_data)

    latest = _service.get_session(session_id)
    if latest.judge_result is None:
        latest.judge_result = JudgeResult(winner_id="", winner_name="", summary="")
    latest.judge_result.votes = [VoteEntry(**v) for v in all_votes]
    _service._store.update_phase(session_id, "judge_tally", total_rounds)

    yield _sse_line("phase_complete", {"phase": "voting"})

    # ============================================================
    # Phase 6: Judge Tally — 裁判统计
    # ============================================================
    yield _sse_line("phase_start", {"phase": "judge_tally", "label": "裁判统计"})

    votes_text = "\n".join(
        f"- {v['voter_name']} 投票给 {v['voted_for_name']}，"
        f"理由：{v['reason']}，评分：{v['scores']}"
        for v in all_votes
    )

    judge_agent = DebateService._make_judge_agent(session.config.judge_id)
    tally_context = DebateAgent.build_judge_tally_context(
        question=question,
        full_transcript=transcript,
        votes_text=votes_text,
    )

    yield _sse_line("judge_tally_start", {})

    try:
        tally_output = judge_agent.invoke_structured(
            tally_context, _TallyOutput, judge_agent.load_task_prompt("judge_tally")
        )
        winner_id = tally_output.winner_id
        winner_name = tally_output.winner_name
        scores_summary = tally_output.votes_summary
    except Exception:
        # 降级：票数最多的辩者获胜
        vote_count: dict[str, int] = {}
        for v in all_votes:
            vid: str = v["voted_for_id"]
            vote_count[vid] = vote_count.get(vid, 0) + 1
        if vote_count:
            winner_id = max(vote_count, key=lambda k: vote_count[k])
        else:
            winner_id = ""
        winner_name = next((d.name for d in debaters if d.id == winner_id), "未知")
        scores_summary = {}

    latest = _service.get_session(session_id)
    if latest.judge_result is None:
        latest.judge_result = JudgeResult(winner_id="", winner_name="", summary="")
    latest.judge_result.winner_id = winner_id
    latest.judge_result.winner_name = winner_name
    latest.judge_result.scores_summary = scores_summary

    yield _sse_line(
        "judge_tally_complete",
        {
            "winner_id": winner_id,
            "winner_name": winner_name,
            "scores_summary": scores_summary,
        },
    )
    yield _sse_line("phase_complete", {"phase": "judge_tally"})

    # ============================================================
    # Phase 7: Judge Summary — 裁判总结（流式）
    # ============================================================
    _service._store.update_phase(session_id, "judge_summary", total_rounds)
    yield _sse_line("phase_start", {"phase": "judge_summary", "label": "裁判总结"})

    tally_info = (
        f"获胜者: {winner_name}\n"
        f"投票详情: {json.dumps(scores_summary, ensure_ascii=False)}"
    )
    summary_context = DebateAgent.build_judge_summary_context(
        question=question,
        full_transcript=transcript,
        tally_result=tally_info,
    )

    yield _sse_line(
        "speaker_start",
        {
            "speaker_id": judge.id,
            "speaker_name": judge.name,
            "phase": "judge_summary",
        },
    )

    summary_tokens: list[str] = []
    try:
        async for token in judge_agent.invoke_stream(
            summary_context, judge_agent.load_task_prompt("judge_summary")
        ):
            summary_tokens.append(token)
            yield _sse_line(
                "message_delta",
                {
                    "speaker_id": judge.id,
                    "speaker_name": judge.name,
                    "phase": "judge_summary",
                    "token": token,
                },
            )
    except Exception as exc:
        yield _sse_line(
            "error",
            {
                "speaker_id": judge.id,
                "message": str(exc),
            },
        )

    summary_text = "".join(summary_tokens)
    latest = _service.get_session(session_id)
    if latest.judge_result:
        latest.judge_result.summary = summary_text

    _store_message(
        session_id=session_id,
        phase=DebatePhase.JUDGE_SUMMARY,
        role=MessageRole.JUDGE,
        speaker=judge,
        content=summary_text,
    )

    yield _sse_line(
        "speaker_end",
        {
            "speaker_id": judge.id,
            "phase": "judge_summary",
            "full_content": summary_text,
        },
    )
    yield _sse_line("phase_complete", {"phase": "judge_summary"})

    # ============================================================
    # Done
    # ============================================================
    _service._store.mark_complete(session_id)
    yield _sse_line(
        "done",
        {
            "session_id": session_id,
            "winner_id": winner_id,
            "winner_name": winner_name,
        },
    )


# ============================================================
# 7.4: GET /api/debate/sessions/{session_id}
# ============================================================


@router.get("/sessions/{session_id}", summary="获取完整辩论记录")
async def get_session(session_id: str) -> dict[str, Any]:
    """返回完整结构化辩论记录。"""
    try:
        session = _service.get_session(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

    return session.model_dump()
