"""辩论导出服务 — Markdown / JSON / PDF 生成。

负责：
- 从 SessionStore 加载会话数据
- 构建 API 规范的完整结构化响应
- 生成 Markdown 辩论记录
- 通过 WeasyPrint 将 Markdown 转为美观 PDF
"""

from __future__ import annotations

import json
import logging
from typing import Any

from debate.api.schemas import DebateSession
from debate.session.store import SessionNotFoundError, SessionStore

logger = logging.getLogger("debate.export")


# ============================================================
# 会话响应构建器
# ============================================================


def build_session_response(session: DebateSession, store: SessionStore) -> dict[str, Any]:
    """将 DebateSession 构建为 API 规范的完整响应 dict。

    与 GET /sessions/{id} 的响应格式一致。
    """
    config = session.config
    debaters_data = _build_debaters_data(session)
    judge_data = _build_judge_data(session)

    # 按阶段组织消息
    stages = _build_stages(session)

    # 投票统计
    tally, votes_list, awards = _build_voting_data(session)

    stages["voting"] = {
        "phase": "voting",
        "label": "🗳️ 投票",
        "votes": votes_list,
        "tally": tally,
        "awards": awards,
    }

    # 裁判总结
    judge_summary_text = ""
    if session.judge_result and session.judge_result.summary:
        judge_summary_text = session.judge_result.summary
    stages["judge_summary"]["content"] = judge_summary_text

    # 预生成 Markdown
    markdown = _generate_markdown(
        session_id=session.session_id,
        question=session.config.question,
        debaters=debaters_data,
        judge=judge_data,
        created_at=session.created_at.isoformat() if session.created_at else "",
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
        stages=stages,
        tally=tally,
        awards=awards,
    )

    return {
        "session_id": session.session_id,
        "question": session.config.question,
        "status": "completed" if session.is_complete else "running",
        "created_at": session.created_at.isoformat() if session.created_at else "",
        "completed_at": (
            session.completed_at.isoformat() if session.completed_at else None
        ),
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


# ============================================================
# Markdown 生成
# ============================================================


def generate_markdown(session: DebateSession) -> str:
    """从 DebateSession 生成完整的 Markdown 辩论记录。"""
    debaters = _build_debaters_data(session)
    judge = _build_judge_data(session)
    stages = _build_stages(session)
    tally, votes_list, awards = _build_voting_data(session)

    # 补充 voting stage
    stages["voting"] = {
        "phase": "voting",
        "label": "🗳️ 投票",
        "votes": votes_list,
        "tally": tally,
        "awards": awards,
    }

    return _generate_markdown(
        session_id=session.session_id,
        question=session.config.question,
        debaters=debaters,
        judge=judge,
        created_at=session.created_at.isoformat() if session.created_at else "",
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
        stages=stages,
        tally=tally,
        awards=awards,
    )


def generate_json_export(session: DebateSession, store: SessionStore) -> str:
    """生成 JSON 导出字符串（完整的结构化数据）。"""
    response = build_session_response(session, store)
    return json.dumps(response, ensure_ascii=False, indent=2)


# ============================================================
# PDF 生成
# ============================================================


def generate_pdf(session: DebateSession, store: SessionStore) -> bytes:
    """将辩论会话渲染为美观的 PDF 文件。

    流程：Markdown → HTML（带 CSS）→ WeasyPrint → PDF bytes

    Args:
        session: 辩论会话对象
        store: 会话存储（用于 build_session_response）

    Returns:
        PDF 二进制数据
    """
    try:
        # 使用库导入，避免全局依赖检查
        import markdown
        from weasyprint import HTML
    except ImportError as e:
        raise _PdfDependencyError(
            f"PDF 生成需要安装 extra dependencies: {e}. "
            "请运行: pip install markdown weasyprint"
        )

    # 构建会话数据
    response = build_session_response(session, store)

    # 构建 HTML
    html = _build_pdf_html(response)

    # 渲染 PDF
    try:
        pdf = HTML(string=html).write_pdf()
    except Exception as e:
        logger.error(f"PDF 生成失败: {e}")
        raise _PdfGenerationError(f"PDF 生成失败: {e}")

    return pdf


class _PdfDependencyError(Exception):
    """PDF 依赖缺失。"""


class _PdfGenerationError(Exception):
    """PDF 渲染失败。"""


# ============================================================
# 内部辅助函数
# ============================================================


def _build_debaters_data(session: DebateSession) -> list[dict]:
    """构建辩者数据列表。"""
    result: list[dict] = []
    for d in session.debaters:
        result.append(
            {
                "id": d.id,
                "name": d.name,
                "school": d.school or "",
                "avatar": "🎭",
                "persona_short": d.description or "",
            }
        )
    return result


def _build_judge_data(session: DebateSession) -> dict:
    """构建裁判数据。"""
    return {
        "id": session.judge.id,
        "name": session.judge.name,
        "avatar": "⚖️",
        "persona_short": session.judge.description or "",
    }


def _build_stages(session: DebateSession) -> dict[str, dict]:
    """按阶段组织消息和质询记录。"""
    config = session.config

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
        phase_str = _phase_str(msg)

        if phase_str == "opening":
            stages["opening"]["messages"].append(_msg_to_dict(msg))
        elif phase_str == "closing":
            stages["closing"]["messages"].append(_msg_to_dict(msg))
        elif phase_str == "judge_summary":
            stages["judge_summary"]["content"] = msg.content
        # cross_ask / cross_answer → 从 session.cross_qas 构建

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

    return stages


def _build_voting_data(session: DebateSession) -> tuple[dict[str, int], list[dict], dict]:
    """从 JudgeResult 构建投票统计、投票列表和奖项。

    Returns:
        (tally, votes_list, awards)
    """
    tally: dict[str, int] = {}
    votes_list: list[dict] = []
    awards: dict[str, dict] = {}

    if not session.judge_result:
        return tally, votes_list, awards

    for vote in session.judge_result.votes:
        votes_list.append(
            {
                "voter": vote.voter_id,
                "vote_for": vote.voted_for_id,
                "reason": vote.reason,
            }
        )
        tally[vote.voted_for_id] = tally.get(vote.voted_for_id, 0) + 1

    # 最佳论点奖：得票最多者
    if tally:
        best_id = max(tally, key=lambda k: tally[k])
        name_map = {d.id: d.name for d in session.debaters}
        awards["best_argument"] = {
            "recipient": name_map.get(best_id, best_id),
            "reason": f"获得最多票数（{tally[best_id]} 票），论证最具说服力",
        }

    return tally, votes_list, awards


def _phase_str(msg) -> str:
    """从消息的 phase 字段提取字符串值。"""
    if hasattr(msg.phase, "value"):
        return msg.phase.value
    return str(msg.phase)


def _msg_to_dict(msg) -> dict:
    """将 Message 转为 API 规范 dict。"""
    return {
        "id": msg.id,
        "timestamp": msg.timestamp.isoformat() if msg.timestamp else "",
        "speaker": {
            "id": msg.speaker_id,
            "name": msg.speaker_name,
            "role": _role_str(msg.role),
            "avatar": _role_avatar(msg.role),
        },
        "target": {"id": msg.target_id, "name": msg.target_name or "所有人"},
        "content": msg.content,
    }


def _role_str(role) -> str:
    """消息角色 → 字符串。"""
    if hasattr(role, "value"):
        return role.value
    return str(role)


def _role_avatar(role) -> str:
    """消息角色 → emoji。"""
    role_str = _role_str(role)
    return {"debater": "🎭", "judge": "⚖️", "system": "🤖", "user": "👤"}.get(
        role_str, "💬"
    )


# ============================================================
# Markdown 模板
# ============================================================


def _generate_markdown(
    session_id: str,
    question: str,
    debaters: list[dict],
    judge: dict,
    created_at: str,
    completed_at: str | None,
    stages: dict,
    tally: dict[str, int],
    awards: dict,
) -> str:
    """渲染完整的 Markdown 辩论记录。"""
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
    if completed_at:
        completed_display = completed_at[:19].replace("T", " ") if completed_at else ""
        lines.append(f"**完成时间**：{completed_display}")
    lines.append("")

    # ---- 立论 ----
    opening = stages.get("opening", {})
    lines.append("## 📜 立论")
    lines.append("")
    for msg in opening.get("messages", []):
        speaker = msg.get("speaker", {})
        school = _find_school(debaters, speaker.get("id", ""))
        school_suffix = f" · {school}" if school else ""
        lines.append(
            f"### {speaker.get('avatar', '🎭')} {speaker.get('name', '')}{school_suffix}"
        )
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
            lines.append(
                f"### 第 {round_num} 轮：{asker.get('name', '')} → @{answerer.get('name', '')}"
            )
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
            lines.append(
                f"### {speaker.get('avatar', '🎭')} {speaker.get('name', '')}"
            )
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
            voters = [
                v["voter"] for v in voting["votes"] if v["vote_for"] == debater_id
            ]
            voter_names = [name_map.get(v, v) for v in voters]
            lines.append(
                f"| {name} | {count} 票 | {'、'.join(voter_names) if voter_names else '—'} |"
            )
        lines.append("")

        # 奖项
        if awards:
            for award_key, award in awards.items():
                recipient = award.get("recipient", "")
                icon = "🏆" if award_key == "best_argument" else "🎯"
                label = (
                    "最佳论点奖" if award_key == "best_argument" else "最佳质询奖"
                )
                lines.append(
                    f"**{icon} {label}**：{recipient} — {award.get('reason', '')}"
                )
                lines.append("")

    # ---- 裁判总结 ----
    judge_summary = stages.get("judge_summary", {})
    if judge_summary.get("content"):
        lines.append("## 📝 裁判总结")
        lines.append("")
        lines.append(judge_summary["content"])

    return "\n".join(lines)


def _find_school(debaters: list[dict], speaker_id: str) -> str:
    """从辩者列表中查找学派名。"""
    for d in debaters:
        if d.get("id") == speaker_id:
            return d.get("school", "")
    return ""


# ============================================================
# PDF HTML 构建
# ============================================================


def _build_pdf_html(response: dict) -> str:
    """将辩论会话数据渲染为带 CSS 样式的 HTML 文档。"""
    stages = response.get("stages", {})
    debaters = response.get("config", {}).get("debaters", [])
    question = response.get("question", "")
    created_at = response.get("created_at", "")
    config = response.get("config", {})

    # 元信息
    debater_names = "、".join(
        f'{d["name"]}（{d.get("school", "")}）' for d in debaters
    )
    judge_name = config.get("judge", {}).get("name", "")
    created_display = created_at[:19].replace("T", " ") if created_at else ""

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>多Agent辩论记录</title>",
        "<style>",
        _pdf_css(),
        "</style>",
        "</head>",
        "<body>",
        # 封面
        '<div class="cover-title">多Agent辩论</div>',
        f'<div class="cover-question">{_escape_html(question)}</div>',
        f'<div class="cover-meta">辩论时间：{_escape_html(created_display)} &nbsp;|&nbsp; 辩者：{_escape_html(debater_names)} &nbsp;|&nbsp; 裁判：{_escape_html(judge_name)}</div>',
        '<hr class="section-divider">',
    ]

    # ---- 立论 ----
    opening = stages.get("opening", {})
    if opening.get("messages"):
        html_parts.append('<div class="phase-title">📜 立论</div>')
        for msg in opening["messages"]:
            html_parts.append(_render_bubble_html(msg, debaters))

    # ---- 质询 ----
    cross = stages.get("cross_examine", {})
    if cross.get("qa_pairs"):
        html_parts.append('<div class="phase-title">⚔️ 质询</div>')
        for qa in cross["qa_pairs"]:
            round_num = qa.get("round", 1)
            asker = qa.get("asker", {})
            answerer = qa.get("answerer", {})
            school = _find_school(debaters, asker.get("id", ""))
            school_class = _school_css_class(school)

            html_parts.append(
                f'<div class="message-card {school_class}">'
                f'<div class="speaker">🎭 {_escape_html(asker.get("name", ""))}'
                f'<span class="school"> · {_escape_html(school)}</span></div>'
                f'<div class="target-label">向 @{_escape_html(answerer.get("name", ""))} 质询（第 {round_num} 轮）</div>'
                f'<div class="content">{_escape_html(qa.get("question", ""))}</div>'
                f"</div>"
            )

            answerer_school = _find_school(debaters, answerer.get("id", ""))
            answerer_class = _school_css_class(answerer_school)
            html_parts.append(
                f'<div class="message-card {answerer_class}">'
                f'<div class="speaker">🎭 {_escape_html(answerer.get("name", ""))}'
                f'<span class="school"> · {_escape_html(answerer_school)}</span></div>'
                f'<div class="target-label">回复 @{_escape_html(asker.get("name", ""))}</div>'
                f'<div class="content">{_escape_html(qa.get("answer", ""))}</div>'
                f"</div>"
            )

    # ---- 结辩 ----
    closing = stages.get("closing", {})
    if closing.get("messages"):
        html_parts.append('<div class="phase-title">🏁 结辩</div>')
        for msg in closing["messages"]:
            html_parts.append(_render_bubble_html(msg, debaters))

    # ---- 投票 ----
    voting = stages.get("voting", {})
    if voting.get("votes"):
        html_parts.append('<div class="phase-title">🗳️ 投票</div>')

        # 票数统计表
        tally = voting.get("tally", {})
        name_map = {d["id"]: d["name"] for d in debaters}

        html_parts.append('<table class="vote-table">')
        html_parts.append(
            "<thead><tr><th>辩者</th><th>得票</th><th>投票者</th></tr></thead>"
        )
        html_parts.append("<tbody>")
        for debater_id, name in name_map.items():
            count = tally.get(debater_id, 0)
            voters = [
                v["voter"]
                for v in voting["votes"]
                if v["vote_for"] == debater_id
            ]
            voter_names = [name_map.get(v, v) for v in voters]
            row_class = "winner-row" if count == max(tally.values()) else ""
            _voter_text = "、".join(voter_names) if voter_names else "—"
            html_parts.append(
                f'<tr class="{row_class}">'
                f"<td>{_escape_html(name)}</td>"
                f"<td>{count} 票</td>"
                f"<td>{_escape_html(_voter_text)}</td>"
                f"</tr>"
            )
        html_parts.append("</tbody></table>")

        # 奖项
        awards = voting.get("awards", {})
        for award_key, award in awards.items():
            icon = "🏆" if award_key == "best_argument" else "🎯"
            label = "最佳论点奖" if award_key == "best_argument" else "最佳质询奖"
            badge_class = (
                "award-best-argument"
                if award_key == "best_argument"
                else "award-best-cross"
            )
            html_parts.append(
                f'<span class="award-badge {badge_class}">{icon} {label}：'
                f'{_escape_html(award.get("recipient", ""))}</span>'
            )

    # ---- 裁判总结 ----
    judge_summary = stages.get("judge_summary", {})
    if judge_summary.get("content"):
        html_parts.append('<div class="phase-title">📝 裁判总结</div>')
        html_parts.append(
            f'<div class="judge-card">'
            f'<div class="judge-summary">'
            f"{_md_to_html(judge_summary['content'])}"
            f"</div></div>"
        )

    html_parts.append("</body></html>")
    return "\n".join(html_parts)


def _render_bubble_html(msg: dict, debaters: list[dict]) -> str:
    """渲染单条消息气泡的 HTML。"""
    speaker = msg.get("speaker", {})
    target = msg.get("target", {})
    school = _find_school(debaters, speaker.get("id", ""))
    school_class = _school_css_class(school)
    content = msg.get("content", "")

    target_html = ""
    if target.get("id") and target.get("id") != "all":
        target_html = (
            f'<div class="target-label">→ @{_escape_html(target.get("name", ""))}</div>'
        )

    return (
        f'<div class="message-card {school_class}">'
        f'<div class="speaker">{_escape_html(speaker.get("avatar", ""))} '
        f'{_escape_html(speaker.get("name", ""))}'
        f'<span class="school"> · {_escape_html(school)}</span></div>'
        f"{target_html}"
        f'<div class="content">{_escape_html(content)}</div>'
        f"</div>"
    )


def _school_css_class(school: str) -> str:
    """将学派映射为 CSS class。"""
    mapping = {
        "儒家": "school-confucian",
        "道家": "school-daoist",
        "法家": "school-legalist",
        "墨家": "school-mohist",
        "心学": "school-mind",
        "理学": "school-confucian",
        "兵家": "school-military",
        "古希腊哲学": "school-confucian",
        "德国古典哲学": "school-mind",
        "马克思主义": "school-confucian",
        "政治现实主义": "school-legalist",
        "社会契约论": "school-mohist",
        "自由主义": "school-daoist",
        "古典经济学": "school-legalist",
        "凯恩斯主义": "school-daoist",
        "奥地利学派": "school-military",
        "科学哲学": "school-mind",
        "政治哲学": "school-legalist",
        "存在主义先驱": "school-mind",
        "进化生物学": "school-daoist",
        "社会学": "school-military",
        "心理学": "school-confucian",
        "人类学": "school-military",
        "语言学": "school-mohist",
        "传播学": "school-mind",
        "政治学": "school-legalist",
    }
    return mapping.get(school, "school-mohist")


def _escape_html(text: str) -> str:
    """HTML 转义。"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _md_to_html(md_text: str) -> str:
    """简单 Markdown → HTML（粗体、标题、列表、段落）。"""
    try:
        import markdown

        return markdown.markdown(md_text, extensions=["extra", "nl2br"])
    except ImportError:
        # 无 markdown 库时的简单处理
        lines = md_text.split("\n")
        result: list[str] = []
        for line in lines:
            line = line.strip()
            if not line:
                result.append("<br>")
            elif line.startswith("# "):
                result.append(f"<h2>{_escape_html(line[2:])}</h2>")
            elif line.startswith("## "):
                result.append(f"<h3>{_escape_html(line[3:])}</h3>")
            elif line.startswith("- "):
                result.append(f"<li>{_escape_html(line[2:])}</li>")
            else:
                result.append(f"<p>{_escape_html(line)}</p>")
        return "\n".join(result)


# ============================================================
# PDF CSS 样式
# ============================================================


def _pdf_css() -> str:
    """PDF 排版 CSS 样式表（与设计规范一致）。"""
    return """
@page {
    margin: 24px 32px;
}

body {
    font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 12px;
    line-height: 1.7;
    color: #2c3e50;
}

/* 封面标题 */
.cover-title {
    text-align: center;
    margin: 16px 0 10px;
    font-size: 22px;
    font-weight: 700;
    color: #1a1a2e;
}

.cover-question {
    text-align: center;
    font-size: 15px;
    color: #34495e;
    margin-bottom: 16px;
    padding: 12px;
    border-top: 2px solid #f1c40f;
    border-bottom: 2px solid #f1c40f;
}

.cover-meta {
    text-align: center;
    font-size: 11px;
    color: #7f8c8d;
    margin-bottom: 20px;
}

/* 阶段标题 */
.phase-title {
    font-size: 16px;
    font-weight: 700;
    color: #1a1a2e;
    margin: 18px 0 10px;
    padding-bottom: 4px;
    border-bottom: 2px solid #f1c40f;
}

/* 消息卡片 */
.message-card {
    background: #f8f9fa;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 6px 0;
    border-left: 4px solid #3498db;
}

.message-card .speaker {
    font-weight: 700;
    font-size: 13px;
    color: #2c3e50;
    margin-bottom: 4px;
}

.message-card .speaker .school {
    font-weight: 400;
    font-size: 10px;
    color: #95a5a6;
    margin-left: 6px;
}

.message-card .target-label {
    font-size: 10px;
    color: #e74c3c;
    margin-bottom: 2px;
}

.message-card .content {
    font-size: 12px;
    line-height: 1.8;
}

.message-card .content p {
    margin: 2px 0;
}

/* 不同学派左边框颜色 */
.school-confucian  { border-left-color: #e74c3c; }
.school-daoist     { border-left-color: #2ecc71; }
.school-legalist   { border-left-color: #7f8c8d; }
.school-mohist     { border-left-color: #3498db; }
.school-mind       { border-left-color: #9b59b6; }
.school-military   { border-left-color: #e67e22; }
.school-synthesizer { border-left-color: #f1c40f; }

/* 裁判卡片特殊样式 */
.judge-card {
    background: linear-gradient(135deg, #fef9e7, #fdf2d0);
    border: 2px solid #f1c40f;
    border-radius: 6px;
    padding: 12px 16px;
    margin: 10px 0;
}

/* 票数统计表格 */
.vote-table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 12px;
}

.vote-table th {
    background: #f1c40f;
    color: #1a1a2e;
    padding: 6px 10px;
    text-align: left;
    font-weight: 700;
}

.vote-table td {
    padding: 6px 10px;
    border-bottom: 1px solid #ecf0f1;
}

.vote-table .winner-row {
    background: #fef9e7;
    font-weight: 700;
}

/* 获奖徽章 */
.award-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 11px;
    font-weight: 700;
    margin: 2px;
}

.award-best-argument {
    background: #f1c40f;
    color: #1a1a2e;
}

.award-best-cross {
    background: #3498db;
    color: white;
}

/* 裁判总结 */
.judge-summary {
    margin: 14px 0;
}

.judge-summary h2 {
    font-size: 15px;
    color: #1a1a2e;
    margin: 12px 0 6px;
}

.judge-summary table {
    width: 100%;
    border-collapse: collapse;
    margin: 6px 0;
}

.judge-summary table th,
.judge-summary table td {
    border: 1px solid #ddd;
    padding: 4px 8px;
    font-size: 11px;
}

/* 页脚分隔线 */
.section-divider {
    border: none;
    border-top: 1px dashed #bdc3c7;
    margin: 16px 0;
}
"""