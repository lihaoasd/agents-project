"""辩论状态机 — 阶段流转控制。"""

from debate.state.machine import (
    DebateState,
    PhaseResult,
    get_next_phase,
    get_phase_order,
    is_parallel,
    speakers_for,
    target_for,
)

__all__ = [
    "DebateState",
    "PhaseResult",
    "get_next_phase",
    "get_phase_order",
    "is_parallel",
    "speakers_for",
    "target_for",
]