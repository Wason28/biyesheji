#!/usr/bin/env python3
"""Export LeRobot training logs to CSV and SVG charts."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


LOG_PATTERN = re.compile(
    r"INFO (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) .*?"
    r"step:(?P<step>\S+) smpl:(?P<samples>\S+) ep:(?P<episodes>\S+) epch:(?P<epoch>\S+) "
    r"loss:(?P<loss>\S+) grdn:(?P<grad_norm>\S+) lr:(?P<lr>\S+) "
    r"updt_s:(?P<update_s>\S+) data_s:(?P<data_s>\S+)"
)
CHECKPOINT_PATTERN = re.compile(r"INFO (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?step (?P<step>\d+)")
DATASET_PATTERN = re.compile(r"dataset\.(?P<name>num_frames|num_episodes)=(?P<value>\S+)")
PARAM_PATTERN = re.compile(r"num_(?P<kind>learnable|total)_params=(?P<value>\d+)")


JOINT_NAMES = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]


@dataclass
class MetricRow:
    timestamp: str
    step: int
    samples: int
    episodes: int
    epoch_progress: float
    loss: float
    grad_norm: float
    lr: float
    update_s: float
    data_s: float


def _parse_human_number(token: str) -> int:
    token = token.strip().upper()
    if token.endswith("K"):
        return int(round(float(token[:-1]) * 1000))
    if token.endswith("M"):
        return int(round(float(token[:-1]) * 1_000_000))
    return int(float(token))


def _parse_float(token: str) -> float:
    return float(token)


def _safe_mean(rows: list[MetricRow], key: str) -> float:
    values = [getattr(row, key) for row in rows]
    return sum(values) / len(values) if values else 0.0


def parse_training_log(log_path: Path) -> tuple[list[MetricRow], list[dict[str, Any]], dict[str, Any]]:
    rows: list[MetricRow] = []
    checkpoints: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "dataset_num_frames": None,
        "dataset_num_episodes": None,
        "num_learnable_params": None,
        "num_total_params": None,
        "end_of_training": False,
    }

    for raw_line in log_path.read_text(encoding="utf-8").splitlines():
        metric_match = LOG_PATTERN.search(raw_line)
        if metric_match:
            rows.append(
                MetricRow(
                    timestamp=metric_match.group("timestamp"),
                    step=_parse_human_number(metric_match.group("step")),
                    samples=_parse_human_number(metric_match.group("samples")),
                    episodes=int(metric_match.group("episodes")),
                    epoch_progress=_parse_float(metric_match.group("epoch")),
                    loss=_parse_float(metric_match.group("loss")),
                    grad_norm=_parse_float(metric_match.group("grad_norm")),
                    lr=_parse_float(metric_match.group("lr")),
                    update_s=_parse_float(metric_match.group("update_s")),
                    data_s=_parse_float(metric_match.group("data_s")),
                )
            )
            continue

        checkpoint_match = CHECKPOINT_PATTERN.search(raw_line)
        if checkpoint_match and "Checkpoint policy after step" in raw_line:
            checkpoints.append(
                {
                    "timestamp": checkpoint_match.group("timestamp"),
                    "step": int(checkpoint_match.group("step")),
                }
            )
            continue

        dataset_match = DATASET_PATTERN.search(raw_line)
        if dataset_match:
            value_token = dataset_match.group("value")
            value = _parse_human_number(value_token.strip("()"))
            summary[f"dataset_{dataset_match.group('name')}"] = value
            continue

        param_match = PARAM_PATTERN.search(raw_line)
        if param_match:
            summary[f"num_{param_match.group('kind')}_params"] = int(param_match.group("value"))
            continue

        if "End of training" in raw_line:
            summary["end_of_training"] = True

    if rows:
        summary["started_at"] = rows[0].timestamp
        summary["ended_at"] = rows[-1].timestamp
        summary["final_step"] = rows[-1].step
        summary["final_loss"] = rows[-1].loss
        summary["final_grad_norm"] = rows[-1].grad_norm
        summary["final_lr"] = rows[-1].lr
        summary["mean_update_s"] = _safe_mean(rows, "update_s")
        summary["mean_data_s"] = _safe_mean(rows, "data_s")
        summary["best_loss"] = min(row.loss for row in rows)
        summary["max_grad_norm"] = max(row.grad_norm for row in rows)
    return rows, checkpoints, summary


def write_metrics_csv(path: Path, rows: list[MetricRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "timestamp",
                "step",
                "samples",
                "episodes",
                "epoch_progress",
                "loss",
                "grad_norm",
                "lr",
                "update_s",
                "data_s",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.timestamp,
                    row.step,
                    row.samples,
                    row.episodes,
                    row.epoch_progress,
                    row.loss,
                    row.grad_norm,
                    row.lr,
                    row.update_s,
                    row.data_s,
                ]
            )


def write_checkpoints_csv(path: Path, checkpoints: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp", "step"])
        for item in checkpoints:
            writer.writerow([item["timestamp"], item["step"]])


def _svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>',
        ".title { font: 700 22px sans-serif; fill: #1f2937; }",
        ".axis { font: 12px sans-serif; fill: #4b5563; }",
        ".legend { font: 13px sans-serif; fill: #374151; }",
        ".small { font: 11px sans-serif; fill: #6b7280; }",
        "</style>",
    ]


def _write_svg(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines + ["</svg>"]), encoding="utf-8")


def _scale(value: float, src_min: float, src_max: float, dst_min: float, dst_max: float) -> float:
    if math.isclose(src_min, src_max):
        return (dst_min + dst_max) / 2.0
    ratio = (value - src_min) / (src_max - src_min)
    return dst_min + ratio * (dst_max - dst_min)


def _series_points(
    xs: list[float],
    ys: list[float],
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    left: float,
    top: float,
    plot_width: float,
    plot_height: float,
) -> str:
    pairs: list[str] = []
    for x_value, y_value in zip(xs, ys, strict=True):
        px = _scale(x_value, x_min, x_max, left, left + plot_width)
        py = _scale(y_value, y_min, y_max, top + plot_height, top)
        pairs.append(f"{px:.2f},{py:.2f}")
    return " ".join(pairs)


def create_line_chart(
    *,
    path: Path,
    title: str,
    x_label: str,
    y_label: str,
    xs: list[float],
    series: list[tuple[str, list[float], str]],
    footer: str = "",
) -> None:
    width = 1200
    height = 720
    left = 90
    top = 80
    plot_width = 980
    plot_height = 520
    x_min = min(xs)
    x_max = max(xs)
    all_ys = [value for _, values, _ in series for value in values]
    y_min = min(all_ys)
    y_max = max(all_ys)
    pad = (y_max - y_min) * 0.08 if not math.isclose(y_min, y_max) else max(1.0, abs(y_min) * 0.1 + 1.0)
    y_min -= pad
    y_max += pad

    lines = _svg_header(width, height)
    lines.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>')
    lines.append(f'<text x="{left}" y="42" class="title">{title}</text>')
    lines.append(
        f'<rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height}" fill="#f8fafc" stroke="#cbd5e1"/>'
    )

    for tick in range(6):
        x_value = x_min + (x_max - x_min) * tick / 5 if x_max != x_min else x_min
        px = _scale(x_value, x_min, x_max, left, left + plot_width)
        lines.append(f'<line x1="{px:.2f}" y1="{top}" x2="{px:.2f}" y2="{top + plot_height}" stroke="#e5e7eb"/>')
        lines.append(f'<text x="{px:.2f}" y="{top + plot_height + 24}" text-anchor="middle" class="axis">{x_value:.0f}</text>')

    for tick in range(6):
        y_value = y_min + (y_max - y_min) * tick / 5 if y_max != y_min else y_min
        py = _scale(y_value, y_min, y_max, top + plot_height, top)
        lines.append(f'<line x1="{left}" y1="{py:.2f}" x2="{left + plot_width}" y2="{py:.2f}" stroke="#e5e7eb"/>')
        lines.append(f'<text x="{left - 12}" y="{py + 4:.2f}" text-anchor="end" class="axis">{y_value:.4g}</text>')

    lines.append(f'<text x="{left + plot_width / 2:.2f}" y="{height - 28}" text-anchor="middle" class="axis">{x_label}</text>')
    lines.append(
        f'<text x="24" y="{top + plot_height / 2:.2f}" text-anchor="middle" class="axis" transform="rotate(-90 24 {top + plot_height / 2:.2f})">{y_label}</text>'
    )

    legend_x = left
    for name, values, color in series:
        points = _series_points(xs, values, x_min, x_max, y_min, y_max, left, top, plot_width, plot_height)
        lines.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" points="{points}"/>'
        )
        lines.append(f'<rect x="{legend_x}" y="{top - 34}" width="18" height="8" fill="{color}"/>')
        lines.append(f'<text x="{legend_x + 26}" y="{top - 26}" class="legend">{name}</text>')
        legend_x += 180

    if footer:
        lines.append(f'<text x="{left}" y="{height - 8}" class="small">{footer}</text>')
    _write_svg(path, lines)


def create_bar_chart(
    *,
    path: Path,
    title: str,
    categories: list[str],
    series: list[tuple[str, list[float], str]],
    y_label: str,
    footer: str = "",
) -> None:
    width = 1200
    height = 720
    left = 100
    top = 80
    plot_width = 960
    plot_height = 520
    all_values = [value for _, values, _ in series for value in values]
    y_min = min(0.0, min(all_values))
    y_max = max(all_values)
    pad = (y_max - y_min) * 0.1 if not math.isclose(y_min, y_max) else max(1.0, abs(y_max) * 0.1 + 1.0)
    y_min -= pad * 0.2
    y_max += pad

    lines = _svg_header(width, height)
    lines.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>')
    lines.append(f'<text x="{left}" y="42" class="title">{title}</text>')
    lines.append(
        f'<rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height}" fill="#f8fafc" stroke="#cbd5e1"/>'
    )
    zero_y = _scale(0.0, y_min, y_max, top + plot_height, top)
    lines.append(f'<line x1="{left}" y1="{zero_y:.2f}" x2="{left + plot_width}" y2="{zero_y:.2f}" stroke="#9ca3af"/>')

    for tick in range(6):
        y_value = y_min + (y_max - y_min) * tick / 5 if y_max != y_min else y_min
        py = _scale(y_value, y_min, y_max, top + plot_height, top)
        lines.append(f'<line x1="{left}" y1="{py:.2f}" x2="{left + plot_width}" y2="{py:.2f}" stroke="#e5e7eb"/>')
        lines.append(f'<text x="{left - 12}" y="{py + 4:.2f}" text-anchor="end" class="axis">{y_value:.3g}</text>')

    group_width = plot_width / max(1, len(categories))
    bar_width = group_width / (len(series) + 1)
    for idx, category in enumerate(categories):
        x_center = left + group_width * (idx + 0.5)
        lines.append(f'<text x="{x_center:.2f}" y="{top + plot_height + 24}" text-anchor="middle" class="axis">{category}</text>')
        for series_idx, (_, values, color) in enumerate(series):
            value = values[idx]
            bar_x = left + group_width * idx + bar_width * (series_idx + 0.5)
            bar_y = _scale(max(value, 0.0), y_min, y_max, top + plot_height, top)
            value_y = _scale(min(value, 0.0), y_min, y_max, top + plot_height, top)
            height_px = abs(value_y - bar_y)
            lines.append(
                f'<rect x="{bar_x:.2f}" y="{min(bar_y, value_y):.2f}" width="{bar_width * 0.8:.2f}" height="{height_px:.2f}" fill="{color}"/>'
            )

    lines.append(
        f'<text x="24" y="{top + plot_height / 2:.2f}" text-anchor="middle" class="axis" transform="rotate(-90 24 {top + plot_height / 2:.2f})">{y_label}</text>'
    )

    legend_x = left
    for name, _, color in series:
        lines.append(f'<rect x="{legend_x}" y="{top - 34}" width="18" height="8" fill="{color}"/>')
        lines.append(f'<text x="{legend_x + 26}" y="{top - 26}" class="legend">{name}</text>')
        legend_x += 160

    if footer:
        lines.append(f'<text x="{left}" y="{height - 8}" class="small">{footer}</text>')
    _write_svg(path, lines)


def extract_action_chart_series(stats: dict[str, Any]) -> list[tuple[str, list[float], str]]:
    action = stats["action"]
    return [
        ("q10", [float(value) for value in action["q10"]], "#2563eb"),
        ("median", [float(value) for value in action["q50"]], "#059669"),
        ("q90", [float(value) for value in action["q90"]], "#dc2626"),
    ]


def build_summary(
    summary: dict[str, Any],
    checkpoints: list[dict[str, Any]],
    stats: dict[str, Any],
) -> dict[str, Any]:
    action = stats["action"]
    return {
        **summary,
        "checkpoint_steps": [item["step"] for item in checkpoints],
        "dataset_action_mean": dict(zip(JOINT_NAMES, action["mean"], strict=True)),
        "dataset_action_std": dict(zip(JOINT_NAMES, action["std"], strict=True)),
    }


def build_figure_manifest(output_dir: Path) -> list[dict[str, str]]:
    return [
        {
            "file": str(output_dir / "loss_vs_step.svg"),
            "title": "SmolVLA Training Loss vs Step",
            "caption": "训练损失随步数下降，反映策略在示教数据上的拟合过程。",
        },
        {
            "file": str(output_dir / "grad_norm_vs_step.svg"),
            "title": "Gradient Norm vs Step",
            "caption": "梯度范数曲线用于观察优化过程是否平稳，是否出现梯度爆炸或异常抖动。",
        },
        {
            "file": str(output_dir / "learning_rate_vs_step.svg"),
            "title": "Learning Rate vs Step",
            "caption": "学习率衰减曲线，对应本次训练使用的 cosine decay with warmup 调度策略。",
        },
        {
            "file": str(output_dir / "timing_vs_step.svg"),
            "title": "Training Timing vs Step",
            "caption": "展示每步参数更新耗时和数据加载耗时，可用于分析训练吞吐和 I/O 开销。",
        },
        {
            "file": str(output_dir / "action_quantiles.svg"),
            "title": "Dataset Action Quantiles by Joint",
            "caption": "展示各关节动作在数据集中的 q10 / q50 / q90 分位值，用于说明示教动作分布。",
        },
    ]


def write_markdown_report(
    *,
    path: Path,
    summary: dict[str, Any],
    figure_manifest: list[dict[str, str]],
) -> None:
    lines = [
        "# SmolVLA Training Report",
        "",
        "## Experiment Summary",
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- Training start: `{summary.get('started_at', '')}`",
        f"- Training end: `{summary.get('ended_at', '')}`",
        f"- Final step: `{summary.get('final_step', '')}`",
        f"- Final loss: `{summary.get('final_loss', '')}`",
        f"- Best loss: `{summary.get('best_loss', '')}`",
        f"- Final grad norm: `{summary.get('final_grad_norm', '')}`",
        f"- Final learning rate: `{summary.get('final_lr', '')}`",
        f"- Mean update time per step: `{summary.get('mean_update_s', '')}` s",
        f"- Mean data loading time per step: `{summary.get('mean_data_s', '')}` s",
        f"- Dataset frames: `{summary.get('dataset_num_frames', '')}`",
        f"- Dataset episodes: `{summary.get('dataset_num_episodes', '')}`",
        f"- Learnable parameters: `{summary.get('num_learnable_params', '')}`",
        f"- Total parameters: `{summary.get('num_total_params', '')}`",
        f"- Checkpoints: `{summary.get('checkpoint_steps', [])}`",
        "",
        "## Dataset Action Statistics",
        "",
        "| Joint | Mean | Std |",
        "| --- | ---: | ---: |",
    ]
    for joint in JOINT_NAMES:
        lines.append(
            f"| {joint} | {summary['dataset_action_mean'][joint]:.4f} | {summary['dataset_action_std'][joint]:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Figures",
            "",
        ]
    )
    for item in figure_manifest:
        file_name = Path(item["file"]).name
        lines.extend(
            [
                f"### {item['title']}",
                "",
                f"- File: `{file_name}`",
                f"- Caption: {item['caption']}",
                "",
            ]
        )

    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export training CSV and SVG charts from a LeRobot train log")
    parser.add_argument("--log", type=Path, required=True, help="path to the training log file")
    parser.add_argument("--stats-json", type=Path, required=True, help="path to dataset stats.json")
    parser.add_argument("--output-dir", type=Path, required=True, help="directory to write CSV/SVG outputs")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows, checkpoints, summary = parse_training_log(args.log)
    if not rows:
        raise SystemExit(f"no metric rows found in log: {args.log}")

    stats = json.loads(args.stats_json.read_text(encoding="utf-8"))

    write_metrics_csv(args.output_dir / "training_metrics.csv", rows)
    write_checkpoints_csv(args.output_dir / "checkpoints.csv", checkpoints)

    xs = [row.step for row in rows]
    create_line_chart(
        path=args.output_dir / "loss_vs_step.svg",
        title="SmolVLA Training Loss vs Step",
        x_label="Training Step",
        y_label="Loss",
        xs=xs,
        series=[("loss", [row.loss for row in rows], "#dc2626")],
        footer=f"log={args.log.name}",
    )
    create_line_chart(
        path=args.output_dir / "grad_norm_vs_step.svg",
        title="Gradient Norm vs Step",
        x_label="Training Step",
        y_label="Grad Norm",
        xs=xs,
        series=[("grad_norm", [row.grad_norm for row in rows], "#7c3aed")],
        footer=f"log={args.log.name}",
    )
    create_line_chart(
        path=args.output_dir / "learning_rate_vs_step.svg",
        title="Learning Rate vs Step",
        x_label="Training Step",
        y_label="Learning Rate",
        xs=xs,
        series=[("lr", [row.lr for row in rows], "#2563eb")],
        footer=f"log={args.log.name}",
    )
    create_line_chart(
        path=args.output_dir / "timing_vs_step.svg",
        title="Training Timing vs Step",
        x_label="Training Step",
        y_label="Seconds",
        xs=xs,
        series=[
            ("update_s", [row.update_s for row in rows], "#059669"),
            ("data_s", [row.data_s for row in rows], "#ea580c"),
        ],
        footer=f"log={args.log.name}",
    )
    create_bar_chart(
        path=args.output_dir / "action_quantiles.svg",
        title="Dataset Action Quantiles by Joint",
        categories=JOINT_NAMES,
        series=extract_action_chart_series(stats),
        y_label="Action Value",
        footer=f"stats={args.stats_json.name}",
    )

    report_summary = build_summary(summary, checkpoints, stats)
    report_summary["generated_at"] = datetime.now().isoformat()
    figure_manifest = build_figure_manifest(args.output_dir)
    (args.output_dir / "summary.json").write_text(
        json.dumps(report_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.output_dir / "figure_manifest.json").write_text(
        json.dumps(figure_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_markdown_report(
        path=args.output_dir / "report.md",
        summary=report_summary,
        figure_manifest=figure_manifest,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
