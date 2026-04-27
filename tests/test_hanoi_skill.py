from embodied_agent.skills.hanoi import (
    HanoiProblem,
    build_hanoi_skill_card,
    looks_like_hanoi_instruction,
    render_hanoi_task_prompts,
    solve_hanoi,
)


def test_solve_default_hanoi_generates_seven_moves() -> None:
    moves = solve_hanoi()

    assert len(moves) == 7
    assert moves[0].ring_key == "pink_small"
    assert moves[0].source_peg == "A"
    assert moves[0].target_peg == "C"
    assert moves[-1].ring_key == "pink_small"
    assert moves[-1].source_peg == "A"
    assert moves[-1].target_peg == "C"


def test_render_hanoi_task_prompts_are_human_readable() -> None:
    prompts = render_hanoi_task_prompts(HanoiProblem())

    assert prompts[0] == "第1步：把粉色小圆环从A柱移动到C柱"
    assert prompts[3] == "第4步：把红色大圆环从A柱移动到C柱"
    assert prompts[-1] == "第7步：把粉色小圆环从A柱移动到C柱"


def test_build_hanoi_skill_card_contains_prompt_and_constraints() -> None:
    card = build_hanoi_skill_card()

    assert card["skill_id"] == "hanoi_task_skill"
    assert card["generated_step_count"] == 7
    assert "汉诺塔" in str(card["name"])
    assert "source_peg" in str(card["system_prompt"])
    assert len(card["execution_constraints"]) == 4


def test_looks_like_hanoi_instruction() -> None:
    assert looks_like_hanoi_instruction("请完成汉诺塔任务")
    assert looks_like_hanoi_instruction("Move the Hanoi rings from A柱 to C柱")
    assert not looks_like_hanoi_instruction("把1号舵机左转15度")
