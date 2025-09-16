-- Canonical schema (Postgres syntax, P1 implemented via SQLite shim)

CREATE TABLE IF NOT EXISTS platforms (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    api_version TEXT,
    export_format_version TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS import_runs (
    id UUID PRIMARY KEY,
    platform_id UUID NOT NULL REFERENCES platforms(id),
    source_file TEXT NOT NULL,
    checksum TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE,
    error TEXT
);

CREATE TABLE IF NOT EXISTS threads (
    id UUID PRIMARY KEY,
    platform_id UUID NOT NULL REFERENCES platforms(id),
    import_run_id UUID REFERENCES import_runs(id),
    external_id TEXT,
    title TEXT,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    quality_score REAL,
    UNIQUE(platform_id, external_id)
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY,
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    content_type TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE,
    sequence_number INTEGER NOT NULL,
    token_count INTEGER,
    has_attachments BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_messages_thread_seq ON messages(thread_id, sequence_number);
CREATE INDEX IF NOT EXISTS idx_messages_content_fts ON messages USING GIN (to_tsvector('english', content));

CREATE TABLE IF NOT EXISTS attachments (
    id UUID PRIMARY KEY,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    filename TEXT,
    mime_type TEXT,
    file_size INTEGER,
    content_hash TEXT,
    storage_path TEXT,
    extracted_text TEXT,
    metadata JSONB DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type TEXT,
    aliases TEXT[],
    description TEXT,
    confidence REAL,
    first_mentioned TIMESTAMP WITH TIME ZONE,
    mention_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS entity_mentions (
    id UUID PRIMARY KEY,
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    start_char INTEGER,
    end_char INTEGER,
    confidence REAL
);

CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    keywords TEXT[],
    parent_topic_id UUID REFERENCES topics(id),
    confidence REAL,
    thread_count INTEGER DEFAULT 0,
    auto_generated BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS thread_topics (
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    score REAL,
    PRIMARY KEY (thread_id, topic_id)
);

CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color TEXT,
    description TEXT,
    auto_generated BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS thread_tags (
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (thread_id, tag_id)
);

CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY,
    content_id UUID NOT NULL,
    content_type TEXT NOT NULL,
    model_name TEXT NOT NULL,
    vector VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_content ON embeddings(content_id, content_type);

CREATE TABLE IF NOT EXISTS link_edges (
    id UUID PRIMARY KEY,
    source_thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    target_thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    link_type TEXT NOT NULL,
    score REAL,
    evidence_bits INTEGER,
    policy_version TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validated_by_human BOOLEAN DEFAULT FALSE,
    human_override BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS audits (
    id UUID PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id UUID NOT NULL,
    action TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    actor TEXT
);

-- Auxiliary indexes for search
CREATE INDEX IF NOT EXISTS idx_threads_title ON threads USING GIN (to_tsvector('english', coalesce(title, '')));
CREATE INDEX IF NOT EXISTS idx_threads_updated_at ON threads(updated_at DESC);
