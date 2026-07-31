# AgriContext-IE Project Specification

## Category

Agriculture

## Project objective

Build an Ireland-first agricultural language model that gives better
answers when agricultural decisions depend on country, local weather,
soil drainage, season, field conditions, and production system.

The model should recognise when insufficient local context has been
provided instead of returning generic one-size-fits-all advice.

## Primary language

English

## Secondary language

Irish/Gaeilge as a bounded secondary capability.

Irish examples will be added only after the English dataset structure
and evaluation process are working correctly.

## Initial MVP use cases

1. Field trafficability and soil-damage risk after rainfall
2. Weather-sensitive agricultural decisions
3. Missing-context detection
4. Country-specific versus generic agricultural guidance

## Intended behaviour

For each question, the model should:

1. Give a recommendation or risk assessment
2. Explain which local factors affected the answer
3. Identify important missing information
4. Give safe and practical next steps
5. State its level of confidence
6. Avoid inventing regulations, weather readings, products, or dosages

## Initial evaluation goals

Compare the base and adapted models on:

- Broad agriculture accuracy
- Irish-context accuracy
- Context-sensitive reasoning
- Contrastive scenario accuracy
- Missing-context detection
- Unsupported recommendation rate
- English-Irish consistency