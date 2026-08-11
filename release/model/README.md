---
base_model: togethercomputer/Meta-Llama-3.3-70B-Instruct-Reference
library_name: peft
tags:
  - agriculture
  - ireland
  - lora
  - adaption-autoscientist
---

# AgriContext-IE LoRA Adapter

AgriContext-IE is an Ireland-first agricultural decision-support model for
field trafficability, soil-damage, grazing, and poaching-risk questions. It is
trained to use the local conditions supplied in the prompt and to return
`INSUFFICIENT_CONTEXT` when essential field information is missing.

## Model details

- Base model: `togethercomputer/Meta-Llama-3.3-70B-Instruct-Reference`
- Training method: supervised fine-tuning
- Adapter type: LoRA/PEFT
- LoRA rank and alpha: 8
- Target modules: `q_proj`, `v_proj`
- Epochs: 1
- Learning rate: `1e-4`
- Training system: Adaption AutoScientist
- Primary language: English
- Domain: Irish dairy and grassland field conditions

The release contains adapter weights and configuration only. Access to
compatible base-model weights is required for inference.

## Intended use

The adapter is intended for concise, structured assessments of:

- Machinery trafficability and soil structural damage risk
- Grazing and poaching risk
- Weather-sensitive field operations
- Missing or overly broad agricultural context

Expected responses contain a risk label, assessment, relevant factors, missing
information, a practical next step, and confidence level.

## Limitations and safety

- The current scope is narrow and Ireland-first.
- The model must not invent weather readings, soil conditions, regulations,
  products, or dosages.
- `LOW_RISK` does not mean no risk or guarantee that a field is suitable.
- Output is not proof of regulatory compliance and does not replace direct
  inspection or advice from a farmer, adviser, agronomist, or other qualified
  professional.
- Pesticide, veterinary medicine, and chemical-dosage instructions are outside
  the intended scope.

The adapter has not yet been scored on the project's frozen held-out benchmark.
No improvement over the base model is claimed until those results are published.

## Training and evaluation data

The repository contains 40 reviewed seed examples and a separate 20-case frozen
benchmark. Evaluation prompts and close paraphrases are excluded from training.
Agricultural claims are linked to official Met Éireann and Teagasc sources in
the project claim and source registers.

See the project repository for the task definition, blueprint, dataset,
evaluation plan, and reproducibility scripts.
