"""Score AgriContext-IE model responses against the frozen benchmark."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = ROOT / "data" / "evaluation" / "eval_v0.jsonl"
LABELS = ("LOW_RISK", "MODERATE_RISK", "HIGH_RISK", "INSUFFICIENT_CONTEXT")
SECTIONS = (
    "RISK",
    "ASSESSMENT",
    "RELEVANT FACTORS",
    "MISSING INFORMATION",
    "NEXT STEP",
    "CONFIDENCE",
)


class EvaluationError(Exception):
    """Raised for invalid evaluation inputs."""


def sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise EvaluationError(str(error)) from error
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise EvaluationError(f"{path}:{line_number}: {error}") from error
        if not isinstance(row, dict):
            raise EvaluationError(f"{path}:{line_number}: expected JSON object")
        rows.append(row)
    return rows


def index_unique(rows: list[dict[str, Any]], path: Path) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        case_id = row.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise EvaluationError(f"{path}: every row needs a non-empty string id")
        if case_id in indexed:
            raise EvaluationError(f"{path}: duplicate id {case_id}")
        indexed[case_id] = row
    return indexed


def parse_label(response: str) -> str | None:
    match = re.search(r"(?mi)^\s*RISK:\s*([A-Z_]+)\s*$", response)
    return match.group(1) if match and match.group(1) in LABELS else None


def strict_format_compliance(response: str) -> bool:
    positions: list[int] = []
    for section in SECTIONS:
        matches = list(re.finditer(rf"(?mi)^\s*{re.escape(section)}:\s*", response))
        if len(matches) != 1:
            return False
        positions.append(matches[0].start())
    if positions != sorted(positions):
        return False
    confidence = re.search(
        r"(?mi)^\s*CONFIDENCE:\s*(LOW|MEDIUM|HIGH)\s*$", response
    )
    return parse_label(response) is not None and confidence is not None


def safe_divide(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def rounded(value: float | None) -> float | None:
    return round(value, 4) if value is not None else None


def classification_metrics(
    expected: list[str], predicted: list[str | None]
) -> dict[str, Any]:
    per_label: dict[str, dict[str, float | int | None]] = {}
    f1_values: list[float] = []
    for label in LABELS:
        tp = sum(e == label and p == label for e, p in zip(expected, predicted))
        fp = sum(e != label and p == label for e, p in zip(expected, predicted))
        fn = sum(e == label and p != label for e, p in zip(expected, predicted))
        precision = safe_divide(tp, tp + fp)
        recall = safe_divide(tp, tp + fn)
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision is not None and recall is not None and precision + recall
            else 0.0
        )
        f1_values.append(f1)
        per_label[label] = {
            "support": sum(e == label for e in expected),
            "precision": rounded(precision),
            "recall": rounded(recall),
            "f1": rounded(f1),
        }
    return {
        "accuracy": rounded(sum(e == p for e, p in zip(expected, predicted)) / len(expected)),
        "macro_f1": rounded(sum(f1_values) / len(f1_values)),
        "per_label": per_label,
    }


def validate_annotations(
    annotations: dict[str, dict[str, Any]], benchmark: dict[str, dict[str, Any]]
) -> None:
    unknown = set(annotations) - set(benchmark)
    if unknown:
        raise EvaluationError(f"annotations contain unknown IDs: {sorted(unknown)}")
    for case_id, row in annotations.items():
        if row.get("review_status") != "reviewed":
            raise EvaluationError(
                f"{case_id}: annotation review_status must be 'reviewed'"
            )
        found = row.get("required_factors_found")
        claims = row.get("unsupported_claims")
        clarity = row.get("clarity_rating")
        if not isinstance(found, list) or not all(isinstance(x, str) for x in found):
            raise EvaluationError(f"{case_id}: required_factors_found must be a list of strings")
        allowed = set(benchmark[case_id]["required_factors"])
        invalid = set(found) - allowed
        if invalid:
            raise EvaluationError(
                f"{case_id}: factors must exactly match benchmark values: {sorted(invalid)}"
            )
        if not isinstance(claims, list) or not all(isinstance(x, str) for x in claims):
            raise EvaluationError(f"{case_id}: unsupported_claims must be a list of strings")
        if clarity is not None and (
            isinstance(clarity, bool) or not isinstance(clarity, int) or not 1 <= clarity <= 5
        ):
            raise EvaluationError(f"{case_id}: clarity_rating must be null or an integer 1-5")


def score(
    benchmark_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    annotation_rows: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    benchmark = index_unique(benchmark_rows, Path("benchmark"))
    predictions = index_unique(prediction_rows, Path("predictions"))
    expected_ids = set(benchmark)
    if set(predictions) != expected_ids:
        missing = sorted(expected_ids - set(predictions))
        extra = sorted(set(predictions) - expected_ids)
        raise EvaluationError(f"prediction IDs mismatch; missing={missing}, extra={extra}")

    annotations = (
        index_unique(annotation_rows, Path("annotations")) if annotation_rows is not None else {}
    )
    if annotations:
        validate_annotations(annotations, benchmark)

    details: list[dict[str, Any]] = []
    for case_id, case in benchmark.items():
        response = predictions[case_id].get("response")
        if not isinstance(response, str) or not response.strip():
            raise EvaluationError(f"{case_id}: response must be a non-empty string")
        predicted = parse_label(response)
        annotation = annotations.get(case_id)
        factor_coverage = None
        unsupported_count = None
        clarity_rating = None
        if annotation is not None:
            factor_coverage = safe_divide(
                len(annotation["required_factors_found"]), len(case["required_factors"])
            )
            unsupported_count = len(annotation["unsupported_claims"])
            clarity_rating = annotation["clarity_rating"]
        details.append(
            {
                "id": case_id,
                "pair_id": case.get("pair_id"),
                "topic": case.get("topic"),
                "scenario_type": case.get("scenario_type"),
                "expected_label": case["expected_label"],
                "predicted_label": predicted,
                "label_correct": predicted == case["expected_label"],
                "format_compliant": strict_format_compliance(response),
                "required_factor_coverage": rounded(factor_coverage),
                "unsupported_claim_count": unsupported_count,
                "clarity_rating": clarity_rating,
            }
        )

    expected = [row["expected_label"] for row in details]
    predicted = [row["predicted_label"] for row in details]
    automatic = classification_metrics(expected, predicted)
    automatic["label_correct_count"] = sum(
        row["label_correct"] for row in details
    )
    automatic["format_compliance"] = rounded(
        sum(row["format_compliant"] for row in details) / len(details)
    )
    automatic["format_compliant_count"] = sum(
        row["format_compliant"] for row in details
    )

    missing_cases = [row for row in details if row["expected_label"] == "INSUFFICIENT_CONTEXT"]
    predicted_missing = [row for row in details if row["predicted_label"] == "INSUFFICIENT_CONTEXT"]
    missing_tp = sum(row["label_correct"] for row in missing_cases)
    missing_precision = safe_divide(missing_tp, len(predicted_missing))
    missing_recall = safe_divide(missing_tp, len(missing_cases))
    automatic["missing_context"] = {
        "precision": rounded(missing_precision),
        "recall": rounded(missing_recall),
        "true_positive_count": missing_tp,
        "expected_count": len(missing_cases),
        "predicted_count": len(predicted_missing),
    }

    pair_ids = sorted({row["pair_id"] for row in details if row["pair_id"]})
    pair_results = {
        pair_id: all(row["label_correct"] for row in details if row["pair_id"] == pair_id)
        for pair_id in pair_ids
    }
    automatic["contrastive_pair_accuracy"] = rounded(
        safe_divide(sum(pair_results.values()), len(pair_results))
    )
    automatic["contrastive_pair_pass_count"] = sum(pair_results.values())
    automatic["contrastive_pair_count"] = len(pair_results)
    automatic["contrastive_pairs"] = pair_results

    human: dict[str, Any] = {"annotated_cases": len(annotations)}
    factor_values = [
        row["required_factor_coverage"]
        for row in details
        if row["required_factor_coverage"] is not None
    ]
    unsupported_values = [
        row["unsupported_claim_count"]
        for row in details
        if row["unsupported_claim_count"] is not None
    ]
    clarity_values = [
        row["clarity_rating"] for row in details if row["clarity_rating"] is not None
    ]
    human["required_factor_coverage"] = rounded(
        safe_divide(sum(factor_values), len(factor_values))
    )
    human["unsupported_claim_case_rate"] = rounded(
        safe_divide(sum(value > 0 for value in unsupported_values), len(unsupported_values))
    )
    human["unsupported_claim_count"] = (
        sum(unsupported_values) if unsupported_values else None
    )
    human["mean_clarity_rating"] = rounded(
        safe_divide(sum(clarity_values), len(clarity_values))
    )

    metrics = {
        "schema_version": 1,
        "case_count": len(details),
        "label_distribution": dict(Counter(expected)),
        "automatic_metrics": automatic,
        "human_review_metrics": human,
    }
    return metrics, details


def percent(value: float | None) -> str:
    return "Not scored" if value is None else f"{value * 100:.1f}%"


def render_report(metrics: dict[str, Any], run_id: str) -> str:
    auto = metrics["automatic_metrics"]
    human = metrics["human_review_metrics"]
    lines = [
        f"# Evaluation report: {run_id}",
        "",
        f"Cases scored: {metrics['case_count']}",
        "",
        "## Automatic metrics",
        "",
        "| Metric | Score |",
        "| --- | ---: |",
        f"| Risk-label accuracy | {percent(auto['accuracy'])} ({auto['label_correct_count']}/{metrics['case_count']}) |",
        f"| Macro F1 | {percent(auto['macro_f1'])} |",
        f"| Contrastive-pair accuracy | {percent(auto['contrastive_pair_accuracy'])} ({auto['contrastive_pair_pass_count']}/{auto['contrastive_pair_count']}) |",
        f"| Missing-context recall | {percent(auto['missing_context']['recall'])} ({auto['missing_context']['true_positive_count']}/{auto['missing_context']['expected_count']}) |",
        f"| Missing-context precision | {percent(auto['missing_context']['precision'])} |",
        f"| Format compliance | {percent(auto['format_compliance'])} ({auto['format_compliant_count']}/{metrics['case_count']}) |",
        "",
        "## Human-review metrics",
        "",
        f"Annotated cases: {human['annotated_cases']}",
        "",
        "| Metric | Score |",
        "| --- | ---: |",
        f"| Required-factor coverage | {percent(human['required_factor_coverage'])} |",
        f"| Unsupported-claim case rate | {percent(human['unsupported_claim_case_rate'])} |",
        f"| Unsupported claims | {human['unsupported_claim_count'] if human['unsupported_claim_count'] is not None else 'Not scored'} |",
        f"| Mean clarity (1–5) | {human['mean_clarity_rating'] if human['mean_clarity_rating'] is not None else 'Not scored'} |",
    ]
    if human["annotated_cases"] == 0:
        lines.extend(
            ["", "Human-review metrics require reviewer annotations."]
        )
    lines.append("")
    return "\n".join(lines)


def write_details(path: Path, details: list[dict[str, Any]]) -> None:
    fields = list(details[0])
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(details)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score an AgriContext evaluation run.")
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--annotations", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--run-id", default="evaluation-run")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir or args.predictions.parent
    try:
        metrics, details = score(
            load_jsonl(args.benchmark),
            load_jsonl(args.predictions),
            load_jsonl(args.annotations) if args.annotations else None,
        )
    except EvaluationError as error:
        print(f"SCORING FAILED: {error}")
        return 1

    metrics["inputs"] = {
        "benchmark_path": str(args.benchmark),
        "benchmark_sha256": sha256(args.benchmark),
        "predictions_path": str(args.predictions),
        "predictions_sha256": sha256(args.predictions),
        "annotations_path": str(args.annotations) if args.annotations else None,
        "annotations_sha256": sha256(args.annotations) if args.annotations else None,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    write_details(output_dir / "case_results.csv", details)
    (output_dir / "report.md").write_text(
        render_report(metrics, args.run_id), encoding="utf-8"
    )
    print(render_report(metrics, args.run_id))
    print(f"Saved metrics and case results to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
