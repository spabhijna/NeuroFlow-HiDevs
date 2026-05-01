-- =====================================================
-- Enable Row Level Security
-- =====================================================
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_pairs ENABLE ROW LEVEL SECURITY;
ALTER TABLE finetune_jobs ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- Helper: safer current_setting (avoids crash if not set)
-- Returns NULL (not error) when session var is missing
-- =====================================================
CREATE OR REPLACE FUNCTION current_pipeline()
RETURNS uuid AS $$
DECLARE
  raw TEXT;
BEGIN
  raw := current_setting('app.current_pipeline_id', true);
  IF raw IS NULL OR raw = '' THEN
    RETURN NULL;
  END IF;
  RETURN raw::uuid;
EXCEPTION WHEN invalid_text_representation THEN
  RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- =====================================================
-- Documents
-- =====================================================
CREATE POLICY documents_policy
ON documents
FOR ALL
USING (pipeline_id = current_pipeline());

-- =====================================================
-- Chunks
-- =====================================================
CREATE POLICY chunks_policy
ON chunks
FOR ALL
USING (
  document_id IN (
    SELECT id FROM documents
    WHERE pipeline_id = current_pipeline()
  )
);

-- =====================================================
-- Pipeline Runs
-- =====================================================
CREATE POLICY pipeline_runs_policy
ON pipeline_runs
FOR ALL
USING (pipeline_id = current_pipeline());

-- =====================================================
-- Evaluations (linked via run_id)
-- =====================================================
CREATE POLICY evaluations_policy
ON evaluations
FOR ALL
USING (
  run_id IN (
    SELECT id FROM pipeline_runs
    WHERE pipeline_id = current_pipeline()
  )
);

-- =====================================================
-- Training Pairs (linked via run_id)
-- =====================================================
CREATE POLICY training_pairs_policy
ON training_pairs
FOR ALL
USING (
  run_id IN (
    SELECT id FROM pipeline_runs
    WHERE pipeline_id = current_pipeline()
  )
);

-- =====================================================
-- Finetune Jobs
-- (No pipeline_id yet → allow all for now)
-- =====================================================
CREATE POLICY finetune_jobs_policy
ON finetune_jobs
FOR ALL
USING (true);

-- =====================================================
-- FORCE RLS (even for table owners)
-- =====================================================
ALTER TABLE documents FORCE ROW LEVEL SECURITY;
ALTER TABLE chunks FORCE ROW LEVEL SECURITY;
ALTER TABLE pipeline_runs FORCE ROW LEVEL SECURITY;
ALTER TABLE evaluations FORCE ROW LEVEL SECURITY;
ALTER TABLE training_pairs FORCE ROW LEVEL SECURITY;
-- finetune_jobs intentionally not forced (no isolation yet)