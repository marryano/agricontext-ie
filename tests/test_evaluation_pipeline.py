"""Tests for deterministic AgriContext evaluation scoring."""

from __future__ import annotations

import unittest

from scripts.score_evaluation import EvaluationError, parse_label, score, strict_format_compliance


RESPONSE = """RISK: HIGH_RISK

ASSESSMENT:
High risk.

RELEVANT FACTORS:
- Wet soil

MISSING INFORMATION:
- None essential

NEXT STEP:
Delay access.

CONFIDENCE:
HIGH"""


class ScoringTests(unittest.TestCase):
    def test_parses_risk_label(self) -> None:
        self.assertEqual(parse_label(RESPONSE), "HIGH_RISK")
        self.assertIsNone(parse_label("RISK: UNKNOWN"))

    def test_enforces_complete_ordered_format(self) -> None:
        self.assertTrue(strict_format_compliance(RESPONSE))
        self.assertFalse(strict_format_compliance(RESPONSE.replace("NEXT STEP:", "")))

    def test_scores_perfect_pair_and_human_annotations(self) -> None:
        benchmark = [
            {"id": "a", "pair_id": "PAIR-1", "topic": "test", "scenario_type": "contrastive", "expected_label": "HIGH_RISK", "required_factors": ["wet soil"]},
            {"id": "b", "pair_id": "PAIR-1", "topic": "test", "scenario_type": "contrastive", "expected_label": "LOW_RISK", "required_factors": ["firm soil"]},
        ]
        predictions = [
            {"id": "a", "response": RESPONSE},
            {"id": "b", "response": RESPONSE.replace("HIGH_RISK", "LOW_RISK")},
        ]
        annotations = [
            {"id": "a", "review_status": "reviewed", "required_factors_found": ["wet soil"], "unsupported_claims": [], "clarity_rating": 5},
            {"id": "b", "review_status": "reviewed", "required_factors_found": ["firm soil"], "unsupported_claims": [], "clarity_rating": 4},
        ]
        metrics, _ = score(benchmark, predictions, annotations)
        self.assertEqual(metrics["automatic_metrics"]["accuracy"], 1.0)
        self.assertEqual(metrics["automatic_metrics"]["contrastive_pair_accuracy"], 1.0)
        self.assertEqual(metrics["human_review_metrics"]["required_factor_coverage"], 1.0)
        self.assertEqual(metrics["human_review_metrics"]["mean_clarity_rating"], 4.5)

    def test_rejects_missing_prediction(self) -> None:
        benchmark = [{"id": "a", "expected_label": "HIGH_RISK", "required_factors": []}]
        with self.assertRaises(EvaluationError):
            score(benchmark, [])


if __name__ == "__main__":
    unittest.main()
