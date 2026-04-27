from embodied_agent.collection.hanoi_demo_collection import (
    DEFAULT_TASKS,
    DEFAULT_TEMPLATES,
    _normalize_recording_decision,
    build_collection_plan,
)


def test_default_templates_cover_all_tasks() -> None:
    plan = build_collection_plan(episodes_per_group=2)

    assert len(plan) == len(DEFAULT_TASKS) * 2
    assert plan[0].task.prompt == "把粉色小圆环放到A柱"
    assert plan[-1].task.prompt == "把红色大圆环放到C柱"

    for item in plan:
        assert item.template.supports(item.task)
        assert item.source_peg != item.task.target_peg


def test_each_task_has_at_least_one_template() -> None:
    for task in DEFAULT_TASKS:
        candidates = [template for template in DEFAULT_TEMPLATES if template.supports(task)]
        assert candidates, task.short_name


def test_normalize_recording_decision() -> None:
    assert _normalize_recording_decision("") == "save"
    assert _normalize_recording_decision("s") == "save"
    assert _normalize_recording_decision("R") == "rerecord"
    assert _normalize_recording_decision("q") == "quit"
    assert _normalize_recording_decision("x") is None
