"""辩论 API Pydantic 数据模型。"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================
# 枚举
# ============================================================

class DebatePhase(str, Enum):
    """辩论阶段。"""

    OPENING = "opening"  # 立论陈述
    CROSS_ASK = "cross_ask"  # 质询问
    CROSS_ANSWER = "cross_answer"  # 质询答
    CLOSING = "closing"  # 结辩
    VOTING = "voting"  # 投票
    JUDGE_TALLY = "judge_tally"  # 裁判统计
    JUDGE_SUMMARY = "judge_summary"  # 裁判总结
    COMPLETE = "complete"  # 结束


class MessageRole(str, Enum):
    """消息来源角色。"""

    DEBATER = "debater"
    JUDGE = "judge"
    SYSTEM = "system"


# ============================================================
# 3.1 DebateConfig / DebaterRole / JudgeRole
# ============================================================

class DebaterRole(BaseModel):
    """辩者角色定义。"""

    id: str = Field(..., description="角色唯一标识，如 'confucius'")
    name: str = Field(..., description="角色中文名，如 '孔子'")
    description: str = Field(..., description="角色简要描述")
    school: str = Field(default="", description="学派，如 '儒家'")
    era: str = Field(default="", description="所处时代，如 '春秋末期'")
    file: str = Field(..., description="对应 prompt 文件名，如 'confucius.md'")


class JudgeRole(BaseModel):
    """裁判角色定义。"""

    id: str = Field(..., description="裁判唯一标识，如 'neutral_analyst'")
    name: str = Field(..., description="裁判中文名，如 '中立分析者'")
    description: str = Field(..., description="裁判简要描述")
    style: str = Field(default="", description="裁判风格描述")
    file: str = Field(..., description="对应 prompt 文件名，如 'neutral_analyst.md'")


class DebateConfig(BaseModel):
    """辩论配置。"""

    question: str = Field(..., min_length=1, max_length=2000, description="辩论问题")
    debater_ids: list[str] = Field(
        ..., min_length=2, max_length=6, description="参与辩论的辩者 ID 列表"
    )
    judge_id: str = Field(..., description="裁判 ID")
    cross_examination_rounds: int = Field(
        default=1, ge=1, le=5, description="交叉质询轮次"
    )


# ============================================================
# 3.2 DebateSession / Message / CrossQA / VoteResult
# ============================================================

class Message(BaseModel):
    """单条辩论消息。"""

    id: str = Field(..., description="消息唯一 ID")
    phase: DebatePhase = Field(..., description="所属辩论阶段")
    role: MessageRole = Field(..., description="消息来源角色")
    speaker_id: str = Field(..., description="发言者 ID（辩者/裁判/系统）")
    speaker_name: str = Field(..., description="发言者名称")
    target_id: str = Field(
        default="all", description="消息目标 ID（'all' 或特定辩者 ID）"
    )
    target_name: str = Field(default="", description="消息目标名称")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="消息时间戳")
    sequence: int = Field(default=0, description="消息序号")


class CrossQA(BaseModel):
    """一对交叉质询问答。"""

    round: int = Field(..., ge=1, description="质询轮次")
    asker_id: str = Field(..., description="提问者 ID")
    asker_name: str = Field(..., description="提问者名称")
    answerer_id: str = Field(..., description="回答者 ID")
    answerer_name: str = Field(..., description="回答者名称")
    question: Message | None = Field(default=None, description="提问消息")
    answer: Message | None = Field(default=None, description="回答消息")


class VoteEntry(BaseModel):
    """单条投票记录。"""

    voter_id: str = Field(..., description="投票者 ID")
    voter_name: str = Field(..., description="投票者名称")
    voted_for_id: str = Field(..., description="被投的辩者 ID")
    voted_for_name: str = Field(..., description="被投的辩者名称")
    scores: dict[str, float] = Field(
        default_factory=dict,
        description="分维度评分，如 {'logic': 8.5, 'evidence': 7.0, 'response': 7.5}",
    )
    reason: str = Field(default="", description="投票理由")


class JudgeResult(BaseModel):
    """裁判评判结果。"""

    winner_id: str = Field(..., description="获胜辩者 ID")
    winner_name: str = Field(..., description="获胜辩者名称")
    votes: list[VoteEntry] = Field(default_factory=list, description="投票详情")
    scores_summary: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="各辩者分维度总分，如 {'confucius': {'logic': 25.0, ...}}",
    )
    summary: str = Field(default="", description="裁判总结文本")


class DebateSession(BaseModel):
    """辩论会话（完整状态）。"""

    session_id: str = Field(..., description="会话唯一 ID")
    config: DebateConfig = Field(..., description="辩论配置")
    debaters: list[DebaterRole] = Field(..., description="参与辩者详细信息")
    judge: JudgeRole = Field(..., description="裁判详细信息")
    messages: list[Message] = Field(default_factory=list, description="全部消息记录")
    cross_qas: list[CrossQA] = Field(default_factory=list, description="质询问答记录")
    current_phase: DebatePhase = Field(
        default=DebatePhase.OPENING, description="当前阶段"
    )
    current_round: int = Field(default=0, description="当前质询轮次（0 = 未开始质询）")
    judge_result: JudgeResult | None = Field(
        default=None, description="裁判评判结果（辩论结束后填充）"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    completed_at: datetime | None = Field(default=None, description="完成时间")

    @property
    def is_complete(self) -> bool:
        """辩论是否已结束。"""
        return self.current_phase == DebatePhase.COMPLETE

    @property
    def full_transcript(self) -> str:
        """生成纯文本辩论全文记录。"""
        lines: list[str] = []
        lines.append(f"辩论主题：{self.config.question}")
        lines.append(f"辩者：{'、'.join(d.name for d in self.debaters)}")
        lines.append(f"裁判：{self.judge.name}")
        lines.append("")
        for msg in self.messages:
            prefix = f"[{msg.phase}] {msg.speaker_name}"
            if msg.target_id != "all":
                prefix += f" → {msg.target_name}"
            lines.append(f"{prefix}: {msg.content}")
            lines.append("")
        if self.judge_result:
            lines.append("=" * 40)
            lines.append(f"获胜者：{self.judge_result.winner_name}")
            lines.append(f"裁判总结：\n{self.judge_result.summary}")
        return "\n".join(lines)