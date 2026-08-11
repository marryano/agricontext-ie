# AgriContext-IE Evaluation Plan

## Purpose

This plan defines a reproducible comparison between an unadapted base model and
the model produced by AutoScientist. Both models must receive the same prompts,
blueprint, and decoding settings. The evaluation set must never be uploaded as
training or augmentation data.

## Frozen benchmark

- Version: `benchmark-v0.1.1`
- File: `data/evaluation/eval_v0.jsonl`
- Cases: 20
- SHA-256: `ae752617ea5e77421f2aedfbe86c8f0fe1c090b8d7dfe8efe822cb96026a49f9`
- Language: English
- Review status: all cases reviewed
- Labels: 7 high risk, 5 insufficient context, 4 low risk, 4 moderate risk
- Contrastive groups: 4 pairs / 8 cases

If the benchmark changes, create and document a new version. Do not silently
replace this checksum.

## Comparison controls

Lock the following for the baseline and adapted runs:

- Exact base model ID and revision
- Blueprint file and checksum
- Evaluation file and checksum
- Prompt construction
- Temperature, top-p, output-token limit, and random seed
- Number of samples per case
- Scoring code version

The default pipeline settings are temperature `0`, top-p `1`, maximum 600
output tokens, seed `42`, and one response per case. If a backend cannot honor a
setting, record that fact in the run manifest rather than implying it did.

## Run artifacts

`scripts/prepare_evaluation.py` creates an immutable run directory containing:

- `manifest.json`: model, benchmark, blueprint, checksums, and decoding settings
- `prompts.jsonl`: answer-free system and user prompts
- `predictions_template.jsonl`: required output schema
- `annotations_template.jsonl`: optional human-review schema

Copy the predictions template to `predictions.jsonl` and replace each empty
response with the model's raw response. Do not repair formatting, labels, or
wording after generation.

Example:

```bash
python3 scripts/prepare_evaluation.py \
  --run-id baseline-001 \
  --run-type baseline \
  --model exact/model-id \
  --model-revision exact-revision
```

The inference backend is intentionally separate from scoring. This allows the
same benchmark to evaluate a hosted base model, a local checkpoint, or an
AutoScientist adapter without changing metric definitions.

## Automatic metrics

Run:

```bash
python3 scripts/score_evaluation.py \
  --run-id baseline-001 \
  --predictions results/runs/baseline-001/predictions.jsonl
```

The scorer produces `metrics.json`, `case_results.csv`, and `report.md`.

### Risk-label accuracy

The proportion of cases whose parsed `RISK:` label exactly matches
`expected_label`. This is the primary metric.

### Macro F1

The unweighted mean F1 across all four risk labels. This prevents the largest
label group from dominating the result.

### Contrastive-pair accuracy

A pair passes only when every case in that pair receives its expected label.
This tests whether the model changes its conclusion when a controlled,
decision-relevant condition changes.

### Missing-context precision and recall

Recall measures how many expected `INSUFFICIENT_CONTEXT` cases were detected.
Precision measures how often that prediction was appropriate. Recall is the
headline missing-context metric, but both values must be reported.

### Format compliance

A response passes only when it contains exactly one of each required heading in
the required order, a valid risk label, and a `LOW`, `MEDIUM`, or `HIGH`
confidence value.

## Human-review metrics

The following cannot be scored reliably through string matching and must not be
silently replaced with model-as-judge estimates:

- Required-factor coverage
- Unsupported agricultural claims
- Practical clarity

To score them, copy `annotations_template.jsonl` to `annotations.jsonl`. For
each case:

1. Change `review_status` from `pending` to `reviewed`.
2. Copy each supported item from the benchmark's `required_factors` into
   `required_factors_found` when the response meaningfully covers it.
3. Record each unsupported or invented claim as a string in
   `unsupported_claims`.
4. Assign `clarity_rating` from 1 (unusable) to 5 (clear and practical).
5. Use `reviewer_notes` for adjudication context.

Factor strings must exactly match the benchmark so annotations remain
auditable. Score a reviewed annotation file with:

```bash
python3 scripts/score_evaluation.py \
  --run-id baseline-001 \
  --predictions results/runs/baseline-001/predictions.jsonl \
  --annotations results/runs/baseline-001/annotations.jsonl
```

Human reviewers should be blinded to whether outputs came from the baseline or
adapted model. Randomize presentation order outside this pipeline and preserve
the mapping used for adjudication.

## Comparing models

After scoring both runs:

```bash
python3 scripts/compare_evaluations.py \
  --baseline results/runs/baseline-001/metrics.json \
  --adapted results/runs/adapted-001/metrics.json \
  --output results/baseline-vs-adapted.md
```

For higher-is-better metrics:

```text
relative improvement = (adapted - baseline) / baseline
```

For unsupported-claim rate, lower is better, so the numerator is reversed.
Always report baseline score, adapted score, absolute change, and relative
improvement. Relative improvement is undefined when the baseline equals zero.

## Acceptance criteria

The adapted model should:

- Improve primary risk-label accuracy
- Avoid regression in missing-context recall
- Avoid regression in format compliance
- Improve or preserve contrastive-pair accuracy
- Not increase the human-reviewed unsupported-claim rate

Because v0 contains only 20 cases, every result must include the raw count and
case-level report. Small percentage changes should not be presented as broad
state-of-the-art evidence without a larger independent test set.

## Leakage controls

- Never upload `data/evaluation/` to Adaptive Data or AutoScientist.
- Never copy evaluation prompts, reference answers, or close paraphrases into
  training data.
- Keep scenarios derived from the same template or source event in one split.
- Run `python3 scripts/validate_data.py` before every training or evaluation run.
- Preserve raw responses and manifests; never overwrite a completed run ID.