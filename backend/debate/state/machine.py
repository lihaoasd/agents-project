"""辩论状态机 — 阶段定义与流转逻辑。

状态机负责：
- 定义阶段流转顺序
- 验证阶段间跳转是否合法
- 管理交叉质询的轮次循环
"""

from __future__ import annotations

from dataclasses import dataclass, field

from debate.api.schemas import DebatePhase


# ============================================================
# 阶段流转规则
# ============================================================

# 标准辩论阶段顺序（不含 COMPLETE，COMPLETE 只能从 JUDGE_SUMMARY 进入）
_PHASE_ORDER: tuple[DebatePhase, ...] = (
    DebatePhase.OPENING,
    DebatePhase.CROSS_ASK,
    DebatePhase.CROSS_ANSWER,
    DebatePhase.CLOSING,
    DebatePhase.VOTING,
    DebatePhase.JUDGE_TALLY,
    DebatePhase.JUDGE_SUMMARY,
)

# 每个阶段允许跳转到的下一个阶段
_ALLOWED_TRANSITIONS: dict[DebatePhase, list[DebatePhase]] = {
    DebatePhase.OPENING: [DebatePhase.CROSS_ASK],
    DebatePhase.CROSS_ASK: [DebatePhase.CROSS_ANSWER],
    DebatePhase.CROSS_ANSWER: [
        DebatePhase.CROSS_ASK,  # 继续下一轮质询
        DebatePhase.CLOSING,  # 质询全部完成 → 结辩
    ],
    DebatePhase.CLOSING: [DebatePhase.VOTING],
    DebatePhase.VOTING: [DebatePhase.JUDGE_TALLY],
    DebatePhase.JUDGE_TALLY: [DebatePhase.JUDGE_SUMMARY],
    DebatePhase.JUDGE_SUMMARY: [DebatePhase.COMPLETE],
    DebatePhase.COMPLETE: [],  # 终态，无法继续流转
}


@dataclass
class PhaseResult:
    """阶段结果 —— 状态机执行的返回值。"""

    success: bool
    current_phase: DebatePhase
    current_round: int = 0
    message: str = ""


@dataclass
class DebateState:
    """辩论运行时状态，轻量级追踪对象。

    不持久化数据本身（数据在 DebateSession 中），只追踪：
    - 当前阶段
    - 当前质询轮次
    - 交叉质询的完成状态
    """

    current_phase: DebatePhase = DebatePhase.OPENING
    current_round: int = 0
    _cross_completed: bool = False

    # 交叉质询追踪：{(asker_id, answerer_id): True}
    _cross_pairs_seen: set[tuple[str, str]] = field(default_factory=set)

    # ---- 阶段流转 ----------------------------------------------------------

    def can_transition_to(self, target: DebatePhase) -> bool:
        """检查从当前阶段到 target 阶段是否合法。"""
        return target in _ALLOWED_TRANSITIONS.get(self.current_phase, [])

    def transition_to(self, target: DebatePhase) -> PhaseResult:
        """尝试流转到 target 阶段。

        Returns:
            PhaseResult — 成功时 success=True，失败时 success=False + 原因
        """
        # 同阶段重入为 no-op
        if target == self.current_phase:
            return PhaseResult(
                success=True,
                current_phase=self.current_phase,
                current_round=self.current_round,
                message=f"已在 {target.value} 阶段，无需流转",
            )

        if not self.can_transition_to(target):
            return PhaseResult(
                success=False,
                current_phase=self.current_phase,
                current_round=self.current_round,
                message=f"不允许从 {self.current_phase.value} 直接跳转到 {target.value}",
            )

        old_phase = self.current_phase
        self.current_phase = target

        # 首次进入 CROSS_ASK 时递增加轮次计数
        if target == DebatePhase.CROSS_ASK and old_phase != DebatePhase.CROSS_ANSWER:
            self.current_round += 1

        return PhaseResult(
            success=True,
            current_phase=target,
            current_round=self.current_round,
            message=f"阶段流转: {old_phase.value} → {target.value}",
        )

    # ---- 交叉质询轮次管理 ---------------------------------------------------

    def advance_cross_round(self, total_rounds: int) -> PhaseResult:
        """推进交叉质询轮次。

        质询逻辑：
        - 每轮：所有 CROSS_ASK → CROSS_ANSWER 完成后 → 判断是否进入下一轮
        - 如果 current_round >= total_rounds → 进入 CLOSING
        - 否则 → 回到 CROSS_ASK 开始下一轮

        Args:
            total_rounds: 配置的总质询轮数

        Returns:
            PhaseResult
        """
        if self.current_phase != DebatePhase.CROSS_ANSWER:
            return PhaseResult(
                success=False,
                current_phase=self.current_phase,
                current_round=self.current_round,
                message=f"当前不在 CROSS_ANSWER 阶段（当前: {self.current_phase.value}），无法推进轮次",
            )

        if self.current_round >= total_rounds:
            # 所有轮次完成 → 结辩
            self._cross_completed = True
            self.current_phase = DebatePhase.CLOSING
            return PhaseResult(
                success=True,
                current_phase=DebatePhase.CLOSING,
                current_round=self.current_round,
                message=f"交叉质询全部完成（共 {total_rounds} 轮），进入结辩",
            )
        else:
            # 继续下一轮
            self.current_phase = DebatePhase.CROSS_ASK
            self._cross_pairs_seen.clear()
            return PhaseResult(
                success=True,
                current_phase=DebatePhase.CROSS_ASK,
                current_round=self.current_round,
                message=f"进入第 {self.current_round + 1} 轮质询",
            )

    # ---- 交叉质询配对追踪 ---------------------------------------------------

    def register_cross_pair(self, asker_id: str, answerer_id: str) -> None:
        """记录一对质询已完成。"""
        self._cross_pairs_seen.add((asker_id, answerer_id))

    def has_cross_pair(self, asker_id: str, answerer_id: str) -> bool:
        """检查这对质询是否已完成。"""
        return (asker_id, answerer_id) in self._cross_pairs_seen

    def clear_cross_pairs(self) -> None:
        """清空本轮质询配对记录（进入新轮次时调用）。"""
        self._cross_pairs_seen.clear()

    # ---- 查询 ---------------------------------------------------------------

    @property
    def is_complete(self) -> bool:
        return self.current_phase == DebatePhase.COMPLETE

    @property
    def is_cross_phase(self) -> bool:
        """是否处于交叉质询阶段。"""
        return self.current_phase in (DebatePhase.CROSS_ASK, DebatePhase.CROSS_ANSWER)

    @property
    def is_finished(self) -> bool:
        """辩论是否已结束（裁判总结之后）。"""
        return self.is_complete


def get_phase_order() -> list[DebatePhase]:
    """获取标准阶段顺序列表。"""
    return list(_PHASE_ORDER)


def get_next_phase(phase: DebatePhase) -> DebatePhase | None:
    """获取标准顺序中的下一个阶段（不考虑质询循环）。"""
    try:
        idx = _PHASE_ORDER.index(phase)
        if idx + 1 < len(_PHASE_ORDER):
            return _PHASE_ORDER[idx + 1]
    except ValueError:
        pass
    return None


__all__ = [
    "DebateState",
    "PhaseResult",
    "get_phase_order",
    "get_next_phase",
]