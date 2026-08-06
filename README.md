# AgriContext-IE

**An Ireland-based agricultural language model for decisions that depend on
local field conditions.**

AgriContext-IE is being built for the Agriculture category of the Adaption Labs
AutoScientist Hackathon. It focuses on field trafficability, soil damage,
grazing, and poaching risk—areas where useful advice depends on local weather,
drainage, field observations, and machinery or livestock pressure.

Instead of returning generic advice when those details are absent, the model is
designed to identify the missing information and let the user know there is insufficient context to provide a solid response.

## What the model tests

- Machinery access and soil structural damage risk
- Livestock grazing and poaching risk
- Weather-sensitive field-operation timing
- Field-level versus regional or neighbouring conditions
- Missing-context detection
- Contrastive reasoning, such as light versus heavy loads or firm surfaces
  versus wet subsurface soil

English is the initial language. A bounded, human-reviewed Irish/Gaeilge subset
is planned after the English pipeline is established.

## Response contract

The model selects one of:

```text
LOW_RISK | MODERATE_RISK | HIGH_RISK | INSUFFICIENT_CONTEXT
```

Each answer follows this structure:

```text
RISK:
ASSESSMENT:
RELEVANT FACTORS:
MISSING INFORMATION:
NEXT STEP:
CONFIDENCE:
```

The model must not invent weather readings, field conditions, regulations,
products, or dosages. Its output is decision support—not proof of compliance or
a replacement for field inspection or qualified professional advice.

## Evaluation

Base and adapted models will be evaluated under identical conditions on a
held-out, human-reviewed benchmark using:

- Risk-label and contrastive-pair accuracy
- Missing-context detection
- Required-factor coverage
- Unsupported-claim rate
- Format compliance and practical clarity

Current evaluation distribution:

| Label | Cases |
| --- | ---: |
| `HIGH_RISK` | 7 |
| `INSUFFICIENT_CONTEXT` | 5 |
| `LOW_RISK` | 4 |
| `MODERATE_RISK` | 4 |

All current data is marked `draft`. Evaluation prompts and close paraphrases
must remain out of training data.

Agricultural claims are traced to official Met Éireann and Teagasc material in
[`docs/source-register.csv`](docs/source-register.csv) and
[`docs/claim-register.csv`](docs/claim-register.csv). Source reuse rights must
be confirmed before dataset publication.

## Quick start

Python 3.10 or newer is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Add your Adaption API key to `.env`:

```dotenv
ADAPTION_API_KEY=replace_with_your_adaption_api_key
```

Check authentication without starting a paid adaptation run:

```bash
python3 scripts/check_adaption_connection.py
```

Validate the training and evaluation JSONL files:

```bash
python3 scripts/validate_data.py
```

## Repository layout

```text
data/seed/         Draft seed-training data
data/evaluation/   Held-out benchmark cases
data/adapted/      Adaptation outputs
data/release/      Publication-ready artifacts
docs/              Task, rubric, evidence, and evaluation plans
scripts/           Data validation and Adaption connection checks
results/           Baseline and adapted-model results
demo/              Future interactive demo
```

The main specifications are
[`docs/task-definition.md`](docs/task-definition.md) and
[`docs/blueprint.md`](docs/blueprint.md).

## Roadmap

- [x] Define the task, labels, and response contract
- [x] Create initial training and contrastive evaluation data
- [x] Add source traceability and JSONL validation
- [ ] Complete agricultural review and freeze the hidden benchmark
- [ ] Implement reproducible baseline scoring
- [ ] Run data adaptation and AutoScientist training
- [ ] Compare the base and adapted models
- [ ] Publish the dataset and weights to Hugging Face and Kaggle
- [ ] Release a demo and model/dataset cards

## Acknowledgements

Built for the [Adaption Labs](https://adaptionlabs.ai/) AutoScientist Hackathon
using the [Adaption API and Python SDK](https://docs.adaptionlabs.ai/), with
agricultural evidence from Met Éireann and Teagasc sources recorded in this
repository.