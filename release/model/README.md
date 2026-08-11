---
base_model: togethercomputer/Meta-Llama-3.3-70B-Instruct-Reference
library_name: peft
pipeline_tag: text-generation
language:
  - en
tags:
  - agriculture
  - ireland
  - llama
  - lora
  - peft
  - adaption-autoscientist
---

# AgriContext-IE

AgriContext-IE is an Ireland-first agricultural decision-support adapter for
field trafficability, soil damage, grazing, and poaching-risk questions. It was
trained with Adaption AutoScientist for the Agriculture category of the
AutoScientist Challenge.

The model is designed to use the local conditions supplied in a prompt—such as
drainage, recent weather, current field observations, and machinery or
livestock pressure. When essential information is absent, it should return
`INSUFFICIENT_CONTEXT` instead of guessing.

This release contains a LoRA adapter, tokenizer files, chat template, and
training metadata. It does not contain the full 70B base-model weights.

## Performance

Adaption AutoScientist completed three research iterations and reported a
**66.19% best head-to-head win rate** for the adapted model against the original
base model.

| Measure | Result |
| --- | ---: |
| AutoScientist status | Succeeded |
| Best adapted-vs-base win rate | 66.19% |
| Completed AutoScientist iterations | 3 / 3 |
| Final recorded evaluation loss | 1.168 |

The win rate means the adapted model was preferred in approximately two-thirds
of AutoScientist's pairwise comparisons. It is not a claim of 66.19% absolute
accuracy or 66.19% relative improvement. The project's separate 20-case
benchmark has not yet been scored, so no independent benchmark result is
claimed here.

## Intended behaviour

The model returns one of four labels:

```text
LOW_RISK | MODERATE_RISK | HIGH_RISK | INSUFFICIENT_CONTEXT
```

Responses follow this structure:

```text
RISK:
ASSESSMENT:
RELEVANT FACTORS:
MISSING INFORMATION:
NEXT STEP:
CONFIDENCE:
```

Primary use cases are:

- Machinery access and soil structural-damage risk
- Livestock grazing and poaching risk
- Weather-sensitive field-operation timing
- Detecting missing or overly broad agricultural context

## Loading the adapter

The base model is large and may require gated access and substantial accelerator
memory. Follow the base model's licence and access requirements.

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_model_id = "togethercomputer/Meta-Llama-3.3-70B-Instruct-Reference"
adapter_id = "agricontext-ie"

tokenizer = AutoTokenizer.from_pretrained(adapter_id)
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    torch_dtype="auto",
    device_map="auto",
)
model = PeftModel.from_pretrained(base_model, adapter_id)

messages = [
    {
        "role": "system",
        "content": (
            "You are AgriContext-IE, a context-aware agricultural "
            "decision-support assistant for Irish farming conditions. "
            "Use only the conditions supplied. If essential information "
            "is missing, return INSUFFICIENT_CONTEXT."
        ),
    },
    {
        "role": "user",
        "content": (
            "Can I take a loaded tractor and trailer onto my grass field "
            "today? The nearest rain gauge recorded 18 mm over 48 hours."
        ),
    },
]

inputs = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,
    return_tensors="pt",
).to(model.device)

outputs = model.generate(inputs, max_new_tokens=500, do_sample=False)
print(tokenizer.decode(outputs[0][inputs.shape[-1]:], skip_special_tokens=True))
```

Set `adapter_id` to the local adapter directory or its published Hugging Face
repository ID.

For consistent results, use the full system blueprint distributed with the
project rather than the shortened example above.

## Training details

| Setting | Value |
| --- | --- |
| Base model recorded by AutoScientist | `meta-llama/Llama-3.3-70B-Instruct-Reference` |
| Compatible base path in adapter config | `togethercomputer/Meta-Llama-3.3-70B-Instruct-Reference` |
| Method | Supervised fine-tuning |
| Adapter | LoRA / PEFT |
| Rank / alpha | 8 / 8 |
| Target modules | `q_proj`, `v_proj` |
| Epochs | 1 |
| Optimizer schedule | Cosine |
| Learning rate | `1e-4` |
| Warmup ratio | 0.1 |
| Maximum gradient norm | 2 |
| Precision recorded in config | bfloat16 |
| Trainer steps | 102 |
| Evaluation events | 5 |

The training set contains 40 reviewed English examples, evenly balanced across
the four risk labels. It is deliberately narrow and focuses on Irish dairy and
grassland field conditions. Agricultural claims were traced to official Met
Éireann and Teagasc material during dataset construction.

AutoScientist run metadata:

- Training experiment: `963e2d81-7268-45e4-b019-85b8a2abf57a`
- Fine-tuning job: `4080ab61-6ecd-4539-84ed-e328eebd62cf`
- Training type: LoRA
- Training method: SFT

## Limitations and safety

- The training set is small and the domain is intentionally narrow.
- The initial release is English-only and Ireland-first.
- Conditions can vary between nearby fields; regional data is not proof of a
  particular field's condition.
- `LOW_RISK` does not mean zero risk or guarantee suitability.
- The model must not invent weather readings, soil conditions, regulations,
  products, or dosages.
- Pesticide, veterinary medicine, and chemical-dosage instructions are outside
  scope.
- Output is not proof of regulatory compliance and does not replace direct
  inspection or advice from a farmer, agricultural adviser, agronomist, or
  another qualified professional.

## Release contents

- `adapter_model.safetensors` — LoRA adapter weights
- `adapter_config.json` — PEFT adapter configuration
- `config.json` — base architecture configuration
- `tokenizer.json` and tokenizer metadata
- `chat_template.jinja` — Llama chat template
- `trainer_state.json` — trainer logs and evaluation losses
- `autoscientist_config.json` — AutoScientist run and recipe metadata

## Framework versions

The exported checkpoint records PEFT 0.15.1 and Transformers 5.13.0. Newer
compatible releases may also work, but were not validated as part of this
release.
