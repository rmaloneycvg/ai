-- RAG Triple-Vector Store Schema
-- Vectors: folder_embedding (domain), hierarchy_embedding (heading tree), content_embedding (section text)
-- Model: bge-m3 via Ollama (1024 dimensions)

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id                  SERIAL PRIMARY KEY,
    source_file         TEXT NOT NULL,          -- relative path: "csharp/efcore-query-patterns.md"
    folder_path         TEXT NOT NULL,          -- domain folder: "csharp", "mssql", "nextjs"
    chunk_index         INTEGER NOT NULL,       -- sequential per source_file (0-based)
    hierarchy_path      TEXT NOT NULL,          -- heading tree: "EF Core > Patterns > Projection"
    heading             TEXT NOT NULL,          -- this chunk's heading text
    content             TEXT NOT NULL,          -- markdown content under this heading
    depth               INTEGER NOT NULL,       -- heading level (0=root, 1=#, 2=##, 3=###, 4=####)
    token_count         INTEGER NOT NULL,       -- approximate token count (chars/4)
    folder_embedding    vector(1024) NOT NULL,  -- embeds: "{folder} {filename_stem}"
    hierarchy_embedding vector(1024) NOT NULL,  -- embeds: full hierarchy_path
    content_embedding   vector(1024) NOT NULL,  -- embeds: "{heading}\n\n{content[:800]}"
    file_modified_at    TIMESTAMPTZ NOT NULL,   -- source file mtime at ingest
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_file, chunk_index)
);

-- HNSW indexes for fast approximate nearest neighbor on each vector
CREATE INDEX IF NOT EXISTS ix_chunks_folder_emb
    ON chunks USING hnsw (folder_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS ix_chunks_hierarchy_emb
    ON chunks USING hnsw (hierarchy_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS ix_chunks_content_emb
    ON chunks USING hnsw (content_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Lookup indexes
CREATE INDEX IF NOT EXISTS ix_chunks_source_file ON chunks (source_file);
CREATE INDEX IF NOT EXISTS ix_chunks_folder_path ON chunks (folder_path);
CREATE INDEX IF NOT EXISTS ix_chunks_depth ON chunks (depth);

-- Ingestion state: tracks file timestamps for change detection
CREATE TABLE IF NOT EXISTS ingest_state (
    source_file      TEXT PRIMARY KEY,
    file_modified_at TIMESTAMPTZ NOT NULL,
    chunk_count      INTEGER NOT NULL,
    ingested_at      TIMESTAMPTZ DEFAULT NOW()
);
