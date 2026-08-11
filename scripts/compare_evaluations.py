"""Compare baseline and adapted AgriContext evaluation metrics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


METRICS = (
    ("Risk-label accuracy", ("automatic_metrics", "accuracy"), "higher"),
    ("Macro F1", ("automatic_metrics", "macro_f1"), "higher"),
    ("Contrastive-pair accuracy", ("automatic_metrics", "contrastive_pair_accuracy"), "higher"),
    ("Missing-context recall", ("automatic_metrics", "missing_context", "recall"), "higher"),
    ("Format compliance", ("automatic_metrics", "format_compliance"), "higher"),
    ("Required-factor coverage", ("human_review_metrics", "required_factor_coverage"), "higher"),
    ("Unsupported-claim case rate", ("human_review_metrics", "unsupported_claim_case_rate"), "lower"),
    ("Mean clarity rating", ("human_review_metrics", "mean_clarity_rating"), "higher"),
)


def nested(data: dict[str, Any], path: tuple[str, ...]) -> float | None:
    value: Any = data
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return float(value) if isinstance(value, (int, float)) else None


def compare_value(
    baseline: float | None, adapted: float | None, direction: str
) -> tuple[float | None, float | None]:
    if baseline is None or adapted is None:
        return None, None
    absolute = adapted - baseline
    signed_change = absolute if direction == "higher" else -absolute
    relative = signed_change / baseline if baseline != 0 else None
    return absolute, relative


def display(value: float | None, percentage: bool = False) -> str:
    if value is None:
        return "Not scored"
    return f"{value * 100:.1f}%" if percentage else f"{value:.3f}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two evaluation reports.")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--adapted", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        adapted = json.loads(args.adapted.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"COMPARISON FAILED: {error}")
        return 1

    rows: list[dict[str, Any]] = []
    for name, path, direction in METRICS:
        before = nested(baseline, path)
        after = nested(adapted, path)
        absolute, relative = compare_value(before, after, direction)
        rows.append(
            {
                "metric": name,
                "baseline": before,
                "adapted": after,
                "absolute_change": absolute,
                "relative_improvement": relative,
            }
        )

    lines = [
        "# Baseline vs adapted model",
        "",
        "| Metric | Baseline | Adapted | Absolute change | Relative improvement |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {metric} | {baseline} | {adapted} | {absolute} | {relative} |".format(
                metric=row["metric"],
                baseline=display(row["baseline"]),
                adapted=display(row["adapted"]),
                absolute=display(row["absolute_change"]),
                relative=display(row["relative_improvement"], percentage=True),
            )
        )
    lines.extend(
        [
            "",
            "For unsupported-claim rate, a decrease is positive improvement.",
            "Relative improvement is omitted when the baseline is zero or a score is missing.",
            "",
        ]
    )
    report = "\n".join(lines)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
