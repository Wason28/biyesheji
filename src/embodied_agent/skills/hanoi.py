"""Hanoi task skill asset for planning, prompting, and dataset preparation."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from embodied_agent.shared.prompts import DECISION_HANOI_SKILL_SYSTEM_PROMPT

DEFAULT_HANOI_RING_ORDER = ("pink_small", "yellow_medium", "red_large")
HANOI_RING_LABELS = {
    "pink_small": "粉色小圆环",
    "yellow_medium": "黄色中圆环",
    "red_large": "红色大圆环",
}
HANOI_PEG_LABELS = {
    "A": "A柱",
    "B": "B柱",
    "C": "C柱",
}


@dataclass(frozen=True, slots=True)
class HanoiMove:
    """Single legal move in a Hanoi sequence."""

    ring_key: str
    source_peg: str
    target_peg: str
    step_index: int


@dataclass(frozen=True, slots=True)
class HanoiProblem:
    """Minimal structured representation of a three-peg Hanoi task."""

    num_disks: int = 3
    source_peg: str = "A"
    target_peg: str = "C"
    auxiliary_peg: str = "B"
    ring_order: tuple[str, ...] = DEFAULT_HANOI_RING_ORDER

    def validate(self) -> None:
        if self.num_disks <= 0:
            raise ValueError("num_disks must be positive")
        if self.num_disks > len(self.ring_order):
            raise ValueError("num_disks exceeds available ring labels")
        pegs = {self.source_peg, self.target_peg, self.auxiliary_peg}
        if len(pegs) != 3:
            raise ValueError("source_peg, target_peg, auxiliary_peg must be distinct")

    @property
    def active_rings(self) -> tuple[str, ...]:
        return self.ring_order[: self.num_disks]


def looks_like_hanoi_instruction(text: str) -> bool:
    normalized = text.strip().lower()
    if not normalized:
        return False
    return any(keyword in normalized for keyword in ("汉诺塔", "hanoi", "圆环", "a柱", "b柱", "c柱"))


def solve_hanoi(problem: HanoiProblem | None = None) -> list[HanoiMove]:
    resolved = problem or HanoiProblem()
    resolved.validate()

    moves: list[HanoiMove] = []
    active_rings = resolved.active_rings

    def _solve(
        level: int,
        source: str,
        target: str,
        auxiliary: str,
    ) -> None:
        if level == 0:
            return
        _solve(level - 1, source, auxiliary, target)
        ring_key = active_rings[level - 1]
        moves.append(
            HanoiMove(
                ring_key=ring_key,
                source_peg=source,
                target_peg=target,
                step_index=len(moves) + 1,
            )
        )
        _solve(level - 1, auxiliary, target, source)

    _solve(
        resolved.num_disks,
        resolved.source_peg,
        resolved.target_peg,
        resolved.auxiliary_peg,
    )
    return moves


def render_hanoi_move_prompt(move: HanoiMove) -> str:
    ring_label = HANOI_RING_LABELS.get(move.ring_key, move.ring_key)
    source_label = HANOI_PEG_LABELS.get(move.source_peg, move.source_peg)
    target_label = HANOI_PEG_LABELS.get(move.target_peg, move.target_peg)
    return f"第{move.step_index}步：把{ring_label}从{source_label}移动到{target_label}"


def render_hanoi_task_prompts(problem: HanoiProblem | None = None) -> list[str]:
    return [render_hanoi_move_prompt(move) for move in solve_hanoi(problem)]


def build_hanoi_skill_card(problem: HanoiProblem | None = None) -> dict[str, object]:
    resolved = problem or HanoiProblem()
    resolved.validate()
    moves = solve_hanoi(resolved)
    return {
        "skill_id": "hanoi_task_skill",
        "name": "汉诺塔任务技能",
        "category": "long_horizon_task",
        "description": "将三柱汉诺塔问题转化为一组合法、可执行、可追踪的原子移动序列。",
        "problem": asdict(resolved),
        "system_prompt": DECISION_HANOI_SKILL_SYSTEM_PROMPT,
        "supports_instruction_keywords": ["汉诺塔", "hanoi", "圆环", "A柱", "B柱", "C柱"],
        "execution_constraints": [
            "一次只允许移动一个圆环",
            "大圆环不能放在小圆环上方",
            "每一步必须显式给出源柱和目标柱",
            "默认使用三柱三环桌面场景",
        ],
        "generated_step_count": len(moves),
        "generated_steps": [render_hanoi_move_prompt(move) for move in moves],
    }
