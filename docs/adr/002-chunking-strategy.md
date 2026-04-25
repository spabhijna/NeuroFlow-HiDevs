## Context
Chunking affects retrieval accuracy significantly.

## Decision
Use semantic chunking by default.

Fallback:
- Fixed-size for structured data
- Sentence-boundary for low-resource cases

## Consequences
Pros:
- Better semantic coherence
- Improved retrieval quality

Cons:
- Higher preprocessing cost