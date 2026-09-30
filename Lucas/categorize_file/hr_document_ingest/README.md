# HR document ingestion: SQLite + MinIO + local AI

Architecture:

    input file
       |
       v
    Python ingest.py
       |
       +--> SHA-256 exact duplicate check
       |
       +--> text extraction
       |
       +--> Ollama AI
       |      |
       |      +--> document_type
       |      +--> title
       |      +--> confidence
       |      +--> metadata defined by contents.yaml
       |
       +--> fuzzy duplicate check
       |
       +--> MinIO object storage
       |
       +--> SQLite metadata/catalogue

## 1. Start MinIO

    docker compose up -d

MinIO console:

    http://localhost:9001

Credentials in the included development compose file:

    minioadmin / minioadmin

Do not use these credentials in production.

## 2. Install Python dependencies

    python -m venv .venv

Linux/macOS:

    source .venv/bin/activate

Windows PowerShell:

    .venv\Scripts\Activate.ps1

Then:

    pip install -r requirements.txt

## 3. Start Ollama

Install Ollama separately and pull a model, for example:

    ollama pull llama3.2:3b

Then make sure Ollama is running on:

    http://localhost:11434

You can use another model:

    OLLAMA_MODEL=qwen2.5:7b python ingest.py ./contract.pdf

## 4. Ingest a file

    python ingest.py ./documents/contract.pdf

The program:

1. calculates SHA-256
2. rejects an exact duplicate
3. extracts text from PDF/DOCX/text files
4. gives the text + contents.yaml contract to the AI
5. gets structured JSON metadata
6. checks for a near-duplicate
7. uploads the original file to MinIO
8. stores the metadata and MinIO pointer in SQLite

## 5. View the catalogue

Open `hr_catalog.sqlite` in Beekeeper Studio.

The important table is:

    documents

The actual file is NOT stored in SQLite.

Example row:

    document_type = employment_contract
    minio_bucket = hr-documents
    minio_key = employment_contract/<uuid>/contract.pdf
    metadata_json = {"annual_salary": 72000, ...}

## contents.yaml

`contents.yaml` is the contract between the database and the AI.

To add a new document type, add it there:

    document_types:
      travel_policy:
        description: "Company travel policy"
        labels:
          - policy_version
          - effective_from
          - country

No Python code change is required.

## Duplicate detection

Exact duplicates use SHA-256.

Near duplicates currently use text similarity with SequenceMatcher. This is
fine for a test/local catalogue. For thousands or millions of documents,
replace this with embeddings + a vector index.

## Scanned PDFs / images

The included extractor handles text-based PDFs and DOCX. Scanned PDFs and
images require OCR. A production version should add Tesseract, OCRmyPDF,
or a vision-capable local model.

## Security

HR documents can contain highly sensitive personal data. For local testing,
MinIO and Ollama keep processing local. In production, add encryption,
authentication, access controls, backups, audit logging, retention rules,
and proper secrets management.
