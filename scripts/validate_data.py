"""Validate AgriContext-IE training and evaluation JSONL files."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

TRAIN_PATH = ROOT / "data" / "seed" / "train_seed_v0.jsonl"
EVAL_PATH = ROOT / "data" / "evaluation" / "eval_v0.jsonl"

ALLOWED_LABELS = {
    "LOW_RISK",
    "MODERATE_RISK",
    "HIGH_RISK",
    "INSUFFICIENT_CONTEXT",
}

TRAIN_REQUIRED_FIELDS = {
    "id",
    "language",
    "topic",
    "scenario_type",
    "instruction",
    "response",
    "expected_label",
    "source_ids",
    "review_status",
}

EVAL_REQUIRED_FIELDS = {
    "id",
    "language",
    "topic",
    "scenario_type",
    "instruction",
    "expected_label",
    "required_factors",
    "reference_response",
    "source_ids",
    "review_status",
}


class ValidationError(Exception):
    """Raised when a dataset fails validation."""


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSON objects from a JSONL file."""

    if not path.exists():
        raise ValidationError(f"File does not exist: {path}")

    rows: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.strip()

            if not line:
                continue

            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValidationError(
                    f"{path}:{line_number}: invalid JSON: {error}"
                ) from error

            if not isinstance(value, dict):
                raise ValidationError(
                    f"{path}:{line_number}: each row must be a JSON object"
                )

            value["_line_number"] = line_number
            rows.append(value)

    return rows


def validate_rows(
    rows: list[dict[str, Any]],
    path: Path,
    required_fields: set[str],
) -> None:
    """Validate required fields and common field types."""

    seen_ids: set[str] = set()

    for row in rows:
        line_number = row["_line_number"]
        row_id = row.get("id")

        missing = required_fields - row.keys()
        if missing:
            raise ValidationError(
                f"{path}:{line_number}: missing fields: "
                f"{', '.join(sorted(missing))}"
            )

        if not isinstance(row_id, str) or not row_id.strip():
            raise ValidationError(
                f"{path}:{line_number}: id must be a non-empty string"
            )

        if row_id in seen_ids:
            raise ValidationError(
                f"{path}:{line_number}: duplicate id: {row_id}"
            )

        seen_ids.add(row_id)

        instruction = row.get("instruction")
        if not isinstance(instruction, str) or not instruction.strip():
            raise ValidationError(
                f"{path}:{line_number}: instruction must be non-empty"
            )

        expected_label = row.get("expected_label")
        if expected_label not in ALLOWED_LABELS:
            raise ValidationError(
                f"{path}:{line_number}: unsupported expected_label "
                f"{expected_label!r}"
            )

        source_ids = row.get("source_ids")
        if not isinstance(source_ids, list):
            raise ValidationError(
                f"{path}:{line_number}: source_ids must be a list"
            )

        if row.get("review_status") not in {"draft", "reviewed"}:
            raise ValidationError(
                f"{path}:{line_number}: review_status must be "
                "'draft' or 'reviewed'"
            )


def normalise_instruction(value: str) -> str:
    """Normalise an instruction for train/evaluation overlap checks."""

    return " ".join(value.lower().split())


def validate_no_split_leakage(
    train_rows: list[dict[str, Any]],
    eval_rows: list[dict[str, Any]],
) -> None:
    """Ensure the same instruction is not present in both splits."""

    train_prompts = {
        normalise_instruction(row["instruction"])
        for row in train_rows
    }

    for row in eval_rows:
        normalised = normalise_instruction(row["instruction"])

        if normalised in train_prompts:
            raise ValidationError(
                "Train/evaluation leakage detected for evaluation row "
                f"{row['id']}"
            )


def main() -> int:
    """Run all dataset validations."""

    try:
        train_rows = load_jsonl(TRAIN_PATH)
        eval_rows = load_jsonl(EVAL_PATH)

        validate_rows(
            train_rows,
            TRAIN_PATH,
            TRAIN_REQUIRED_FIELDS,
        )
        validate_rows(
            eval_rows,
            EVAL_PATH,
            EVAL_REQUIRED_FIELDS,
        )
        validate_no_split_leakage(train_rows, eval_rows)

    except ValidationError as error:
        print(f"VALIDATION FAILED: {error}")
        return 1

    print("Validation passed.")
    print(f"Training rows: {len(train_rows)}")
    print(f"Evaluation rows: {len(eval_rows)}")
    print(f"Allowed labels: {', '.join(sorted(ALLOWED_LABELS))}")

    if eval_rows and all(
        not row["source_ids"]
        for row in eval_rows
    ):
        print(
            "Warning: all evaluation rows are still missing source IDs."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())