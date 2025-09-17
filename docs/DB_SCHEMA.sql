-- Personal AI Chat Manager database schema derived from blueprint.md
-- Assumes PostgreSQL 15+ with pgvector extension installed.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- Enumerated types
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
CREATE TYPE message_content_type AS ENUM ('text', 'code', 'image', 'file');
CREATE TYPE embedding_content_type AS ENUM ('message', 'thread_summary', 'attachment');
CREATE TYPE entity_type AS ENUM ('person', 'technology', 'concept', 'project', 'organization', 'artifact', 'other');
CREATE TYPE link_type AS ENUM ('continuation', 'related', 'contradiction', 'solution');
CREATE TYPE audit_action AS ENUM ('insert', 'update', 'delete');

-- Core tables
CREATE TABLE platforms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    api_version TEXT,
    export_format_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_id UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
    external_id TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    message_count INTEGER NOT NULL DEFAULT 0 CHECK (message_count >= 0),
    total_tokens INTEGER NOT NULL DEFAULT 0 CHECK (total_tokens >= 0),
    quality_score NUMERIC(5,2) CHECK (quality_score BETWEEN 0 AND 1)
);

CREATE UNIQUE INDEX threads_platform_external_idx ON threads(platform_id, external_id);
CREATE INDEX threads_created_at_idx ON threads(created_at);
CREATE INDEX threads_updated_at_idx ON threads(updated_at);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    role message_role NOT NULL,
    content TEXT NOT NULL,
    content_type message_content_type NOT NULL DEFAULT 'text',
    timestamp TIMESTAMPTZ NOT NULL,
    sequence_number INTEGER NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0 CHECK (token_count >= 0),
    has_attachments BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE UNIQUE INDEX messages_thread_seq_idx ON messages(thread_id, sequence_number);
CREATE INDEX messages_timestamp_idx ON messages(timestamp);
CREATE INDEX messages_role_idx ON messages(role);
CREATE INDEX messages_thread_ts_idx ON messages(thread_id, timestamp);
CREATE INDEX messages_content_fts_idx ON messages USING GIN (to_tsvector('english', content));

CREATE TABLE attachments (
    content_hash TEXT PRIMARY KEY,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size BIGINT NOT NULL CHECK (file_size >= 0),
    storage_path TEXT NOT NULL,
    extracted_text TEXT,
    metadata JSONB DEFAULT '{}'::JSONB
);
CREATE INDEX attachments_message_idx ON attachments(message_id);
CREATE INDEX attachments_metadata_gin_idx ON attachments USING GIN (metadata);

CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    color TEXT,
    description TEXT,
    auto_generated BOOLEAN NOT NULL DEFAULT FALSE,
    usage_count INTEGER NOT NULL DEFAULT 0 CHECK (usage_count >= 0)
);

CREATE TABLE thread_tags (
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (thread_id, tag_id)
);

CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    type entity_type NOT NULL DEFAULT 'other',
    aliases TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    description TEXT,
    confidence NUMERIC(5,2) CHECK (confidence BETWEEN 0 AND 1),
    first_mentioned TIMESTAMPTZ,
    mention_count INTEGER NOT NULL DEFAULT 0 CHECK (mention_count >= 0)
);

CREATE INDEX entities_type_idx ON entities(type);
CREATE INDEX entities_confidence_idx ON entities(confidence);

CREATE TABLE message_entities (
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    confidence NUMERIC(5,2) CHECK (confidence BETWEEN 0 AND 1),
    PRIMARY KEY (message_id, entity_id)
);

CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    keywords TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    parent_topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    confidence NUMERIC(5,2) CHECK (confidence BETWEEN 0 AND 1),
    thread_count INTEGER NOT NULL DEFAULT 0 CHECK (thread_count >= 0),
    auto_generated BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX topics_parent_idx ON topics(parent_topic_id);

CREATE TABLE thread_topics (
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    confidence NUMERIC(5,2) CHECK (confidence BETWEEN 0 AND 1),
    PRIMARY KEY (thread_id, topic_id)
);

CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type embedding_content_type NOT NULL,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
    attachment_id TEXT REFERENCES attachments(content_hash) ON DELETE CASCADE,
    vector vector(1024) NOT NULL,
    model_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (
        (content_type = 'message' AND message_id IS NOT NULL AND thread_id IS NULL AND attachment_id IS NULL) OR
        (content_type = 'thread_summary' AND thread_id IS NOT NULL AND message_id IS NULL AND attachment_id IS NULL) OR
        (content_type = 'attachment' AND attachment_id IS NOT NULL AND message_id IS NULL AND thread_id IS NULL)
    )
);

CREATE INDEX embeddings_content_type_idx ON embeddings(content_type);
CREATE INDEX embeddings_model_idx ON embeddings(model_name);
CREATE INDEX embeddings_message_idx ON embeddings(message_id);
CREATE INDEX embeddings_thread_idx ON embeddings(thread_id);
CREATE INDEX embeddings_attachment_idx ON embeddings(attachment_id);
CREATE INDEX embeddings_vector_hnsw_idx ON embeddings USING HNSW (vector vector_l2_ops) WITH (m = 16, ef_construction = 200);

CREATE TABLE link_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    target_thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    link_type link_type NOT NULL,
    score NUMERIC(5,2) CHECK (score BETWEEN 0 AND 1),
    evidence_bits INTEGER NOT NULL DEFAULT 0,
    policy_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    validated_by_human BOOLEAN NOT NULL DEFAULT FALSE,
    human_override BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (source_thread_id, target_thread_id, link_type)
);

CREATE INDEX link_edges_score_idx ON link_edges(score);
CREATE INDEX link_edges_type_idx ON link_edges(link_type);

CREATE TABLE audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name TEXT NOT NULL,
    record_id UUID NOT NULL,
    action audit_action NOT NULL,
    old_values JSONB,
    new_values JSONB,
    changed_by TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX audits_table_idx ON audits(table_name);
CREATE INDEX audits_record_idx ON audits(record_id);
CREATE INDEX audits_changed_by_idx ON audits(changed_by);

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    scope JSONB,
    progress_percent NUMERIC(5,2) CHECK (progress_percent BETWEEN 0 AND 100),
    error_messages TEXT[] DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

CREATE INDEX jobs_type_idx ON jobs(job_type);
CREATE INDEX jobs_status_idx ON jobs(status);
CREATE INDEX jobs_updated_idx ON jobs(updated_at);

CREATE TABLE job_artifacts (
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    PRIMARY KEY (job_id, artifact_type)
);

CREATE TABLE imported_files (
    content_hash TEXT PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    source_path TEXT NOT NULL,
    detected_format TEXT NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Maintenance triggers
CREATE OR REPLACE FUNCTION touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER threads_touch_updated
BEFORE UPDATE ON threads
FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

CREATE TRIGGER jobs_touch_updated
BEFORE UPDATE ON jobs
FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- Full text configuration placeholder (extend with domain-specific dictionaries)
-- Example:
-- CREATE TEXT SEARCH CONFIGURATION chatmgr_fts ( COPY = english );
-- ALTER TEXT SEARCH CONFIGURATION chatmgr_fts ADD MAPPING FOR hword, hword_part WITH simple;
-- Adjust messages_content_fts_idx to use chatmgr_fts when configured.

