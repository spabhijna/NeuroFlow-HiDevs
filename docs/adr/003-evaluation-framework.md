## Context
Manual evaluation is slow and expensive.

## Decision
Use LLM-as-judge with periodic human validation.

## Consequences
Pros:
- Scalable evaluation
- Continuous feedback loop

Cons:
- Bias and hallucination in evaluation

Mitigation:
- Random human audits
- Drift detection