DROP INDEX IF EXISTS documents_content_hash_key;
DROP INDEX IF EXISTS documents_pipeline_hash_uq;
CREATE UNIQUE INDEX documents_pipeline_hash_uq
  ON documents (pipeline_id, content_hash);
