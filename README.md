# AgriContext-IE

AgriContext-IE is an Ireland-first agricultural language model built for the
Adaption Labs AutoScientist Hackathon. It helps assess field trafficability,
soil damage, grazing, and poaching risk using the conditions that actually
matter: drainage, recent weather, field observations, and machinery or
livestock pressure.

The project is designed to avoid confident, generic advice. If the prompt does
not contain enough field-level information, the model returns
`INSUFFICIENT_CONTEXT` and explains what is missing.

## Current state

- 40 reviewed training examples, balanced across four risk labels
- 20 reviewed evaluation cases, including four contrastive pairs
- A LoRA adapter trained by AutoScientist on Llama 3.3 70B Instruct
- Reproducible scripts for baseline and adapted-model evaluation
- Claims traced to official Met Éireann and Teagasc sources

The model has not yet been scored on the frozen benchmark, so no performance
improvement is claimed here.

## Output format

Every response uses one of these labels:

```text
LOW_RISK | MODERATE_RISK | HIGH_RISK | INSUFFICIENT_CONTEXT
```

and follows this structure:

```text
RISK:
ASSESSMENT:
RELEVANT FACTORS:
MISSING INFORMATION:
NEXT STEP:
CONFIDENCE:
```

The model must not invent weather, soil conditions, regulations, products, or
dosages. It supports decisions; it does not replace field inspection or advice
from a qualified professional.

## Repository

```text
data/seed/          Reviewed training examples
data/evaluation/    Frozen held-out benchmark
docs/               Task definition, evidence, and evaluation plan
release/model/      AutoScientist LoRA adapter and configuration
scripts/            Validation and evaluation tools
tests/              Evaluation-pipeline tests
```

The main project contracts are in
[`docs/task-definition.md`](docs/task-definition.md) and
[`docs/blueprint.md`](docs/blueprint.md). Source and claim provenance live in
[`docs/source-register.csv`](docs/source-register.csv) and
[`docs/claim-register.csv`](docs/claim-register.csv).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Add your Adaption API key to `.env` and keep that file private:

```dotenv
ADAPTION_API_KEY=replace_with_your_adaption_api_key
```

Check the dataset and API connection:

```bash
python3 scripts/validate_data.py
python3 scripts/check_adaption_connection.py
```

## Evaluation

Prepare an answer-free run after choosing the exact base model:

```bash
python3 scripts/prepare_evaluation.py \
  --run-id baseline-001 \
  --run-type baseline \
  --model togethercomputer/Meta-Llama-3.3-70B-Instruct-Reference \
  --model-revision exact-revision
```

Add raw model responses to `results/runs/baseline-001/predictions.jsonl`, then
score them:

```bash
python3 scripts/score_evaluation.py \
  --run-id baseline-001 \
  --predictions results/runs/baseline-001/predictions.jsonl
```

Repeat for the adapter and compare the two `metrics.json` files with
`scripts/compare_evaluations.py`. Full metric definitions and reviewer guidance
are in [`docs/evaluation-plan.md`](docs/evaluation-plan.md).

## Model release

The files in `release/model/` are a PEFT/LoRA adapter, not standalone model
weights. Use them with the compatible Llama 3.3 70B Instruct base model and
follow the base model's licence and access requirements. See the
[`model card`](release/model/README.md) for training details and limitations.

Built with [Adaption AutoScientist](https://docs.adaptionlabs.ai/guides/autoscientist).
