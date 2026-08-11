"""Create a reproducible, answer-free evaluation run directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = ROOT / "data" / "evaluation" / "eval_v0.jsonl"
DEFAULT_BLUEPRINT = ROOT / "docs" / "blueprint.md"


def sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: {error}") from error
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare prompts and metadata for one evaluation run."
    )
    parser.add_argument("--run-id", required=True, help="Unique run name")
    parser.add_argument(
        "--run-type", choices=("baseline", "adapted"), default="baseline"
    )
    parser.add_argument("--model", required=True, help="Exact model ID")
    parser.add_argument(
        "--model-revision",
        default="unspecified",
        help="Model revision, checkpoint, or adapter ID",
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-output-tokens", type=int, default=600)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--blueprint", type=Path, default=DEFAULT_BLUEPRINT)
    parser.add_argument(
        "--output-root", type=Path, default=ROOT / "results" / "runs"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    benchmark = args.benchmark.resolve()
    blueprint = args.blueprint.resolve()
    run_dir = args.output_root.resolve() / args.run_id

    if run_dir.exists():
        print(f"ERROR: run directory already exists: {run_dir}")
        return 1
    if not benchmark.exists() or not blueprint.exists():
        print("ERROR: benchmark or blueprint file does not exist")
        return 1

    try:
        rows = load_jsonl(benchmark)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1

    if not rows:
        print("ERROR: benchmark contains no cases")
        return 1

    prompts: list[dict[str, Any]] = []
    annotations: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for row in rows:
        case_id = row.get("id")
        instruction = row.get("instruction")
        if not isinstance(case_id, str) or not isinstance(instruction, str):
            print("ERROR: every benchmark row needs string id and instruction")
            return 1
        if case_id in seen_ids:
            print(f"ERROR: duplicate case id: {case_id}")
            return 1
        seen_ids.add(case_id)
        prompts.append(
            {
                "id": case_id,
                "system": blueprint.read_text(encoding="utf-8").strip(),
                "instruction": instruction,
            }
        )
        annotations.append(
            {
                "id": case_id,
                "review_status": "pending",
                "required_factors_found": [],
                "unsupported_claims": [],
                "clarity_rating": None,
                "reviewer_notes": "",
            }
        )

    run_dir.mkdir(parents=True)
    write_jsonl(run_dir / "prompts.jsonl", prompts)
    write_jsonl(run_dir / "annotations_template.jsonl", annotations)
    write_jsonl(
        run_dir / "predictions_template.jsonl",
        [{"id": row["id"], "response": ""} for row in rows],
    )

    manifest = {
        "schema_version": 1,
        "run_id": args.run_id,
        "run_type": args.run_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "model_revision": args.model_revision,
        "benchmark": {
            "path": str(benchmark.relative_to(ROOT))
            if benchmark.is_relative_to(ROOT)
            else str(benchmark),
            "sha256": sha256(benchmark),
            "case_count": len(rows),
        },
        "blueprint": {
            "path": str(blueprint.relative_to(ROOT))
            if blueprint.is_relative_to(ROOT)
            else str(blueprint),
            "sha256": sha256(blueprint),
        },
        "decoding": {
            "temperature": args.temperature,
            "top_p": args.top_p,
            "max_output_tokens": args.max_output_tokens,
            "seed": args.seed,
        },
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Prepared {len(rows)} cases in {run_dir}")
    print("Write model responses to predictions.jsonl, then run score_evaluation.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
