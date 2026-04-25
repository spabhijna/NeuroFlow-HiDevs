## Context
Need scalable, low-latency vector search integrated with structured data.

## Decision
Use pgvector over Pinecone, Weaviate, Qdrant.

## Consequences
Pros:
- Unified storage (vectors + metadata)
- No vendor lock-in
- Easier joins and filtering

Cons:
- Slightly less optimized than specialized vector DBs
- Requires tuning for scale