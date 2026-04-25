## Context
Different queries require different model capabilities.

## Decision
Route models based on cost, latency, and complexity.

## Routing Matrix

| Query Type        | Model Tier        |
|------------------|------------------|
| Simple factual   | Small model      |
| RAG QA           | Mid-tier model   |
| Reasoning heavy  | Large model      |
| Domain-specific  | Fine-tuned model |

## Consequences
Pros:
- Cost optimization
- Better performance

Cons:
- Routing complexity
- Requires monitoring