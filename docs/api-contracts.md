
## 1. Ingestion API

### `POST /ingest`
Initiates the ingestion process for a new document or data source.

* **Auth:** Required
* **Rate Limit:** 10 requests / minute

**Request:**
```json
{
  "source_type": "pdf | docx | image | csv | url",
  "content": "file_url_or_base64",
  "metadata": {}
}
```

**Response:**
```json
{
  "ingest_id": "uuid",
  "status": "processing"
}
```

**Errors:**
* `400 Bad Request` → Invalid input
* `500 Internal Server Error` → Processing failure

---

## 2. Query & Streaming API

### `POST /query`
Submits a query to the retrieval and generation pipeline.

**Request:**
```json
{
  "query": "string",
  "filters": {},
  "pipeline_id": "optional"
}
```

**Response:**
```json
{
  "query_id": "uuid",
  "status": "processing"
}
```

### `GET /query/{query_id}/stream`
Streams the generated response back to the client using Server-Sent Events (SSE).

**Response (SSE):**
```text
event: token
data: partial_text
```

---

## 3. Evaluation API

### `GET /evaluations`
Retrieves a paginated list of evaluation metrics for past queries.

**Response:**
```json
{
  "results": [
    {
      "query_id": "uuid",
      "faithfulness": 0.9,
      "relevance": 0.85
    }
  ],
  "page": 1
}
```

### `GET /evaluations/aggregate`
Retrieves rolling aggregate metrics across all evaluated queries.

**Response:**
```json
{
  "avg_faithfulness": 0.82,
  "avg_relevance": 0.79
}
```

---

## 4. Pipeline Management API

### `POST /pipelines`
Creates or configures a new processing pipeline.

**Request:**
```json
{
  "name": "default",
  "config": {}
}
```

### `GET /pipelines/{id}/runs`
Retrieves the execution history and logs for a specific pipeline.

**Response:**
```json
{
  "runs": []
}
```

---

## 5. Fine-Tuning API

### `POST /finetune/jobs`
Initiates a new model fine-tuning job using a prepared dataset.

**Request:**
```json
{
  "dataset_id": "uuid",
  "model": "base-model"
}
```

### `GET /finetune/jobs/{id}`
Checks the status and metrics of a running fine-tuning job.

**Response:**
```json
{
  "status": "running",
  "metrics": {}
}
```

---

## 6. System & Diagnostics

### `GET /health`
Checks the operational status of the API.

**Response:**
```json
{
  "status": "ok"
}
```

### `GET /metrics`
Exposes system and application metrics.

**Response:**
* Returns **Prometheus-compatible** plaintext metrics.