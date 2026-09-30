CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_uuid TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    mime_type TEXT,
    size_bytes INTEGER NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    minio_bucket TEXT NOT NULL,
    minio_key TEXT NOT NULL UNIQUE,
    document_type TEXT,
    title TEXT,
    extracted_text TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    ai_model TEXT,
    ai_confidence REAL,
    duplicate_of INTEGER REFERENCES documents(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (duplicate_of) REFERENCES documents(id)
);

CREATE INDEX IF NOT EXISTS idx_documents_type
    ON documents(document_type);

CREATE INDEX IF NOT EXISTS idx_documents_filename
    ON documents(filename);

CREATE INDEX IF NOT EXISTS idx_documents_duplicate
    ON documents(duplicate_of);
