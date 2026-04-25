## 1. Ingestion Subsystem

### Flow
`User Upload` → `File Parser` → `Content Extraction` → `Chunking` → `Embedding` → `Vector Store (pgvector)`

### Steps
* **Accept input:** PDF, DOCX, Image, CSV, URL
* **Route to parser:**
    * **PDF** → PyMuPDF
    * **DOCX** → `python-docx`
    * **Image** → OCR
    * **URL** → HTML scraper
* **Normalize text**
* **Chunk:** Default: semantic chunking
* **Generate embeddings**
* **Store:**
    * Embedding vector
    * Chunk text
    * Metadata (source, timestamp, type)

---

## 2. Retrieval Subsystem

### Pipeline
```text
User Query
   ↓
Query Embedding
   ↓
[Parallel]
   ├─ Vector Search
   ├─ BM25 Keyword Search
   └─ Metadata Filter
   ↓
Reciprocal Rank Fusion (RRF)
   ↓
Cross-Encoder Reranker
   ↓
Top-K Context Window
```

### Notes
* **RRF** improves robustness across retrieval methods.
* **Cross-encoder** ensures semantic relevance.

---

## 3. Generation Subsystem

### Flow
`Context + Query` → `Prompt Builder` → `Model Router` → `LLM` → `Streaming Output` → `Logging`

### Features
* **Dynamic model routing:** Optimizes cost vs. capability.
* **Token streaming:** Server-Sent Events (SSE).
* **Full trace logging:** Captures:
    * Query
    * Retrieved chunks
    * Prompt
    * Response

---

## 4. Evaluation Subsystem

### Async Pipeline
```text
Completed Response
   ↓
Evaluation Queue
   ↓
LLM-as-Judge Scoring
   ↓
Metrics Storage (Postgres)
```

### Metrics
* Faithfulness
* Answer Relevance
* Context Precision
* Context Recall

### Storage
* Row per query
* Rolling aggregates

---

## 5. Fine-Tuning Subsystem

### Pipeline
```text
Evaluation Logs
   ↓
Filter (faithfulness > 0.8 AND rating ≥ 4)
   ↓
Dataset Builder (JSONL)
   ↓
Fine-tuning Job
   ↓
MLflow Tracking
   ↓
Model Registry
   ↓
Router Update
```