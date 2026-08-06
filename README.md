# AgriContext-IE

**An Ireland-focused agricultural language model for decisions that depend on
local field conditions.**

AgriContext-IE is being built for the Agriculture category of the Adaption Labs
AutoScientist Hackathon. The project aims to improve how a language model
reasons about field trafficability, soil damage, grazing, and poaching risk
when the correct answer depends on weather, drainage, field observations, and
the proposed machinery or livestock load.

Agricultural advice should not become confident
just because a prompt mentions a county, rainfall total, or nearby field. When
essential field specific evidence is missing, the model should say so and request
the information needed for a defensible assessment.

> **Project status:** active development. The repository currently contains 40
> draft seed-training examples and 20 draft evaluation cases. The adapted model,
> comparative results, and demo are not yet released.

## Why I chose this project?

I have found that generic agricultural models can often overlook distinctions that matter in practice:

- The same rainfall can affect well-drained and poorly drained fields
  differently.
- A dry-looking surface can conceal wet soil lower in the profile.
- A light single pass and a heavily loaded tractor create different risks.
- Short, controlled grazing can differ from unrestricted access through one
  gateway.
- Conditions at a weather station or neighbouring farm do not establish the
  condition of an individual paddock.

I designed AgriContext-IE to recognise those contrasts, explain which factors
changed its assessment, and avoid filling gaps with invented local details.

## Initial scope

Benchmark v0 covers three related task families:

1. Machinery access and soil structural damage risk
2. Livestock grazing and poaching risk
3. Weather-sensitive field-operation timing

English is the initial language. A bounded, human-reviewed Irish/Gaeilge
capability is planned only after the English data and evaluation pipeline are
established.

## Response contract

The model selects exactly one risk label:

- `LOW_RISK`
- `MODERATE_RISK`
- `HIGH_RISK`
- `INSUFFICIENT_CONTEXT`

It then responds in a consistent, auditable format:

```text
RISK: LOW_RISK | MODERATE_RISK | HIGH_RISK | INSUFFICIENT_CONTEXT

ASSESSMENT:
A concise explanation of the assessment.

RELEVANT FACTORS:
- Factors that increased or reduced the risk

MISSING INFORMATION:
- Important missing information, or "None essential"

NEXT STEP:
A cautious and practical next step.

CONFIDENCE:
LOW | MEDIUM | HIGH
```

The model must not invent weather readings, field observations, soil types,
regulations, products, or dosages. Its output is decision support—not proof of
regulatory compliance or a substitute for field inspection or qualified
professional advice.

## Evaluation approach

The base and adapted models will be tested under the same prompt and decoding
conditions on a held-out, human-reviewed benchmark. Planned metrics include:

- Risk-label accuracy
- Contrastive-pair accuracy
- Missing-context detection
- Required-factor coverage
- Unsupported-claim rate
- Response-format compliance
- Clarity and practical usefulness

Contrastive pairs are an important part of the benchmark. Each pair holds most
of a scenario constant while changing a decision-relevant fact, such as field
firmness, machinery load, grazing duration, or subsurface moisture. A capable
model should change its assessment for the right reason.

The current evaluation set contains 20 English cases:

| Label | Cases |
| --- | ---: |
| `HIGH_RISK` | 7 |
| `INSUFFICIENT_CONTEXT` | 5 |
| `LOW_RISK` | 4 |
| `MODERATE_RISK` | 4 |

All current cases are drafts until subject-matter review is complete. Evaluation
prompts and reference answers must not be reused or closely paraphrased in the
training dataset.

The seed-training split currently contains 40 draft examples, balanced evenly
across the four risk labels. These examples also require review before they are
used for a release training run.

## Evidence and traceability

Benchmark claims are mapped to source IDs so that agricultural reasoning can be
reviewed independently of model performance. The current source register uses
official material from [Met Éireann](https://www.met.ie/) and
[Teagasc](https://www.teagasc.ie/).

- [`docs/source-register.csv`](docs/source-register.csv) records each source and
  its intended scope.
- [`docs/claim-register.csv`](docs/claim-register.csv) maps bounded claims to
  sources and evaluation uses.
- [`docs/eval-case-plan.csv`](docs/eval-case-plan.csv) links cases to the claims
  they test.

Source reuse and licensing must be confirmed before publishing an adapted
dataset. The registers document evidence provenance; they do not by themselves
grant reuse rights.

## Repository structure

```text
agricontext-ie/
├── data/
│   ├── seed/             # Seed training data
│   ├── adapted/          # AutoScientist/Adaptive Data outputs
│   ├── evaluation/       # Held-out evaluation cases
│   └── release/          # Publication-ready dataset artifacts
├── demo/                 # Future interactive demonstration
├── docs/                 # Specification, rubric, sources, claims, and plans
├── results/              # Baseline and adapted-model evaluation results
├── scripts/
│   ├── check_adaption_connection.py
│   └── validate_data.py
├── src/                  # Future application and evaluation code
├── .env.example
└── requirements.txt
```

## Getting started

### 1. Create a Python environment

Python 3.10 or newer is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Configure Adaption access

Create a local `.env` from the example and insert your own API key:

```bash
cp .env.example .env
```

```dotenv
ADAPTION_API_KEY=replace_with_your_adaption_api_key
```

`.env` is ignored by Git. Never commit or share a real API key. See the
[Adaption developer documentation](https://docs.adaptionlabs.ai/) for current
SDK and API guidance.

### 3. Check authentication

```bash
python3 scripts/check_adaption_connection.py
```

This performs a read-only dataset listing request. It does not upload data or
start a credit-consuming adaptation run.

### 4. Validate the datasets

```bash
python3 scripts/validate_data.py
```

The validator checks required fields, unique IDs, supported labels, review
status, JSONL structure, and exact normalized prompt overlap between the
training and evaluation splits.

## Dataset formats

Each JSONL line is one JSON object.

Training rows require:

```text
id, language, topic, scenario_type, instruction, response,
expected_label, source_ids, review_status
```

Evaluation rows require:

```text
id, language, topic, scenario_type, instruction, expected_label,
required_factors, reference_response, source_ids, review_status
```

Evaluation rows currently also include `pair_id`, which is `null` for standalone
cases and shared by related contrastive cases.

See [`docs/task-definition.md`](docs/task-definition.md) for the complete task
contract and risk-label rubric.

## Project roadmap

- [x] Define the task and structured response contract
- [x] Create benchmark v0 and contrastive test cases
- [x] Establish source and claim registers
- [x] Add JSONL validation and an Adaption authentication check
- [ ] Complete independent agricultural review of benchmark v0
- [ ] Freeze a hidden benchmark version
- [x] Build the initial 40-example seed training dataset
- [ ] Complete subject-matter review of the seed training dataset
- [ ] Add reproducible baseline inference and scoring
- [ ] Run data adaptation and AutoScientist training
- [ ] Compare the base and adapted models
- [ ] Publish the adapted dataset and model weights to Hugging Face and Kaggle
- [ ] Release an interactive demo and model/dataset cards

## Key project documents

- [`docs/project-spec.md`](docs/project-spec.md) — overall objective and MVP
- [`docs/task-definition.md`](docs/task-definition.md) — benchmark contract and
  label rubric
- [`docs/blueprint.md`](docs/blueprint.md) — intended model behavior and output
  structure
- [`docs/evaluation-plan.md`](docs/evaluation-plan.md) — evaluation methodology
  (in development)
- [`data/evaluation/eval_v0.jsonl`](data/evaluation/eval_v0.jsonl) — current
  draft benchmark

## Contributing

Useful contributions include agricultural subject-matter review, adversarial or
contrastive case design, evaluation tooling, Irish-language review, and demo
development. Keep evaluation material isolated from training data and attach
source IDs to factual agricultural examples.

Before submitting changes to dataset files, run:

```bash
python3 scripts/validate_data.py
```

## Acknowledgements

This project is being developed for the
[Adaption Labs](https://adaptionlabs.ai/) AutoScientist Hackathon using the
[Adaption API and Python SDK](https://docs.adaptionlabs.ai/). Agricultural
evidence is currently drawn from official Met Éireann and Teagasc resources,
with individual sources recorded in the repository.