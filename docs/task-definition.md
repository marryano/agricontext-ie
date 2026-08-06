# AgriContext-IE — Benchmark v0

## Project objective

AgriContext-IE is an Ireland-first agricultural language model designed
to give better answers when an agricultural decision depends on local
weather, soil drainage, field condition, season, geography, and the
planned farm operation.

The model should recognise when essential local information is missing,
rather than producing confident one-size-fits-all advice.

## Benchmark v0 scope

The first benchmark covers three related task families:

1. Machinery access and soil structural damage risk
2. Livestock grazing and poaching risk
3. Weather-sensitive field-operation timing

This benchmark is the first measurable capability of the project. It
does not define the full eventual scope of the model.

## Expected input

Each prompt may contain some or all of the following:

- Country
- County or region
- Season
- Recent weather
- Forecast weather
- Soil drainage class
- Soil or field surface condition
- Slope or exposure
- Planned operation
- Machinery and approximate load
- Livestock type and stocking context
- Existing signs of rutting, poaching, compaction, or waterlogging

Not every prompt will contain enough information to reach a conclusion.

## Risk labels

The model must choose exactly one of:

- LOW_RISK
- MODERATE_RISK
- HIGH_RISK
- INSUFFICIENT_CONTEXT

## Required response format

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

## Required behaviour

The model should:

- Base its assessment on the context supplied in the prompt
- Recognise that nearby fields may respond differently to the same weather
- Distinguish well-drained and poorly drained soils
- Consider observed field condition as well as weather measurements
- Consider the planned machinery or livestock load
- State when insufficient context has been provided
- Explain which factors affected its assessment
- Use Irish agricultural context only when Ireland is specified
- Clearly state uncertainty

## Prohibited behaviour

The model must not:

- Invent rainfall, weather, soil, or field-condition data
- Invent the soil type or drainage class
- Assume that county-level weather perfectly represents a field
- Apply one rainfall threshold universally
- Claim that a risk assessment proves regulatory compliance
- Give pesticide, veterinary medicine, or chemical dosage instructions
- Invent legal rules or current product authorisations
- Recommend proceeding when essential context is absent
- Present general educational guidance as a guaranteed farm-specific result

## Language scope

Benchmark v0 is English-only.

A bounded, human-reviewed Irish-language subset may be introduced after
the English dataset and evaluation pipeline are working correctly.

## Success criteria

The adapted model should outperform its base model on:

- Risk-label accuracy
- Contrastive-pair accuracy
- Missing-context detection
- Identification of relevant factors
- Unsupported-claim rate
- Response-format compliance
- Clarity and practical usefulness

## Risk-label rubric

### LOW_RISK

The supplied evidence indicates that the field is currently firm and
trafficable, with no strong signs of waterlogging, poaching or structural
weakness. The planned livestock or machinery pressure is limited and no
major contradictory risk factor has been supplied.

LOW_RISK does not mean zero risk or guaranteed suitability.

### MODERATE_RISK

One or more meaningful risk factors are present, but limited access may
be possible with precautions such as shorter grazing periods, back
fencing, multiple access points, lighter loads or close monitoring.

The answer must explain the precautions and remaining uncertainty.

### HIGH_RISK

The supplied evidence strongly indicates a substantial risk of rutting,
poaching, compaction or sward damage. Examples include visible softness,
standing water, active poaching, wet soil combined with a heavy load, or
repeated livestock traffic under poor conditions.

The normal next step should be to delay, stop access, move livestock or
choose a more suitable paddock.

### INSUFFICIENT_CONTEXT

Essential information needed for a defensible assessment has not been
provided. Relevant missing information may include current field
condition, soil drainage, recent weather, forecast weather, planned load,
access pattern or the proposed operation.

The model must identify the missing information instead of guessing.