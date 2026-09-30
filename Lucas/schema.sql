-- Meridian HR Collective — local document catalog (no blobs).
PRAGMA foreign_keys = ON;

CREATE TABLE legal_entities (
  id            INTEGER PRIMARY KEY,
  code          TEXT NOT NULL UNIQUE,
  name          TEXT NOT NULL,
  country_code  TEXT NOT NULL,
  vat_number    TEXT,
  chamber_id    TEXT,
  timezone      TEXT NOT NULL
);

CREATE TABLE clients (
  id                 INTEGER PRIMARY KEY,
  slug               TEXT NOT NULL UNIQUE,
  legal_name         TEXT NOT NULL,
  trading_name       TEXT NOT NULL,
  country_code       TEXT NOT NULL,
  industry           TEXT NOT NULL,
  billing_currency   TEXT NOT NULL,
  account_manager    TEXT NOT NULL,
  msa_signed_on      TEXT NOT NULL,
  risk_tier          TEXT NOT NULL CHECK (risk_tier IN ('low','medium','high')),
  employee_headcount INTEGER NOT NULL
);

CREATE TABLE people (
  id                 INTEGER PRIMARY KEY,
  employee_number    TEXT NOT NULL UNIQUE,
  preferred_name     TEXT NOT NULL,
  legal_name         TEXT NOT NULL,
  role_kind          TEXT NOT NULL CHECK (role_kind IN ('employee','contractor','candidate','alumni')),
  home_country       TEXT NOT NULL,
  work_country       TEXT NOT NULL,
  email              TEXT NOT NULL,
  cost_center        TEXT NOT NULL,
  department         TEXT NOT NULL,
  job_title          TEXT NOT NULL,
  client_id          INTEGER REFERENCES clients(id),
  legal_entity_id    INTEGER NOT NULL REFERENCES legal_entities(id),
  hire_date          TEXT,
  termination_date   TEXT,
  fte                REAL,
  manager_employee_number TEXT
);

CREATE TABLE document_types (
  code               TEXT PRIMARY KEY,
  display_name       TEXT NOT NULL,
  family             TEXT NOT NULL,
  default_retention  TEXT NOT NULL,
  default_classification TEXT NOT NULL,
  pii_class          TEXT NOT NULL,
  label_schema_json  TEXT NOT NULL,
  extraction_notes   TEXT NOT NULL
);

CREATE TABLE documents (
  id                    TEXT PRIMARY KEY,
  document_type         TEXT NOT NULL REFERENCES document_types(code),
  title                 TEXT NOT NULL,
  original_filename     TEXT NOT NULL,
  mime_type             TEXT NOT NULL,
  byte_size             INTEGER NOT NULL,
  page_count            INTEGER,
  language_code         TEXT NOT NULL,
  country_code          TEXT NOT NULL,
  client_id             INTEGER REFERENCES clients(id),
  person_id             INTEGER REFERENCES people(id),
  legal_entity_id       INTEGER NOT NULL REFERENCES legal_entities(id),
  classification        TEXT NOT NULL,
  pii_level             TEXT NOT NULL,
  retention_class       TEXT NOT NULL,
  retain_until          TEXT,
  status                TEXT NOT NULL,
  issued_on             TEXT,
  effective_from        TEXT,
  effective_to          TEXT,
  received_on           TEXT NOT NULL,
  indexed_on            TEXT NOT NULL,
  ocr_confidence        REAL,
  source_system         TEXT NOT NULL,
  workflow_state        TEXT NOT NULL,
  revision              INTEGER NOT NULL DEFAULT 1,
  deep_link             TEXT NOT NULL UNIQUE,
  viewer_link           TEXT NOT NULL,
  sharepoint_link       TEXT,
  content_sha256        TEXT NOT NULL,
  extracted_text        TEXT NOT NULL,
  extracted_json        TEXT NOT NULL
);

CREATE TABLE document_tags (
  id            INTEGER PRIMARY KEY,
  document_id   TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  namespace     TEXT NOT NULL,
  key           TEXT NOT NULL,
  value         TEXT NOT NULL,
  UNIQUE (document_id, namespace, key, value)
);

CREATE TABLE sorting_labels (
  id            INTEGER PRIMARY KEY,
  document_id   TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  label_key     TEXT NOT NULL,
  value_type    TEXT NOT NULL CHECK (value_type IN (
                  'money','date','integer','float','enum','boolean','duration_days')),
  value_numeric REAL,
  value_text    TEXT,
  value_date    TEXT,
  currency      TEXT,
  unit          TEXT,
  UNIQUE (document_id, label_key)
);

CREATE TABLE extracted_entities (
  id                INTEGER PRIMARY KEY,
  document_id       TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  entity_type       TEXT NOT NULL,
  raw_value         TEXT NOT NULL,
  normalized_value  TEXT,
  confidence        REAL NOT NULL,
  page              INTEGER,
  role_in_document  TEXT
);

CREATE TABLE document_relations (
  from_document_id  TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  to_document_id    TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  relation_type     TEXT NOT NULL,
  note              TEXT,
  PRIMARY KEY (from_document_id, to_document_id, relation_type)
);

CREATE TABLE ingestion_events (
  id            INTEGER PRIMARY KEY,
  document_id   TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  occurred_on   TEXT NOT NULL,
  actor         TEXT NOT NULL,
  channel       TEXT NOT NULL,
  detail        TEXT NOT NULL
);

CREATE VIEW v_documents AS
SELECT
  d.id,
  d.title,
  d.document_type,
  dt.family AS document_family,
  d.status,
  d.workflow_state,
  d.classification,
  d.country_code,
  d.language_code,
  d.deep_link,
  c.slug AS client_slug,
  c.legal_name AS client_name,
  p.employee_number,
  p.preferred_name AS person_name,
  d.issued_on,
  d.byte_size,
  d.ocr_confidence
FROM documents d
JOIN document_types dt ON dt.code = d.document_type
LEFT JOIN clients c ON c.id = d.client_id
LEFT JOIN people p ON p.id = d.person_id;

CREATE VIEW v_money_labels AS
SELECT
  d.id AS document_id,
  d.document_type,
  sl.label_key,
  sl.value_numeric AS amount,
  sl.currency,
  c.slug AS client_slug
FROM sorting_labels sl
JOIN documents d ON d.id = sl.document_id
LEFT JOIN clients c ON c.id = d.client_id
WHERE sl.value_type = 'money';

CREATE INDEX idx_docs_type ON documents(document_type);
CREATE INDEX idx_docs_client ON documents(client_id);
CREATE INDEX idx_docs_person ON documents(person_id);
CREATE INDEX idx_docs_country ON documents(country_code);
CREATE INDEX idx_docs_status ON documents(status);
CREATE INDEX idx_tags_key_value ON document_tags(key, value);
CREATE INDEX idx_labels_key ON sorting_labels(label_key, value_numeric);
CREATE INDEX idx_entities_type ON extracted_entities(entity_type, normalized_value);
