from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import sqlite3
import uuid
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import boto3
import requests
import yaml
from botocore.client import Config
from docx import Document as DocxDocument
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "hr_catalog.sqlite"
SCHEMA_PATH = ROOT / "schema.sql"
CONTENTS_PATH = ROOT / "contents.yaml"

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "hr-documents")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
x
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if suffix == ".docx":
        doc = DocxDocument(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    if suffix in {".txt", ".md", ".csv", ".json", ".yaml", ".yml"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    # Images/scanned PDFs need OCR. This version deliberately does not
    # silently invent OCR. Install/configure Tesseract if you need it.
    return ""


def load_contents() -> dict[str, Any]:
    return yaml.safe_load(CONTENTS_PATH.read_text(encoding="utf-8"))


def build_ai_prompt(contents: dict[str, Any], filename: str, text: str) -> str:
    contract = json.dumps(contents, indent=2, ensure_ascii=False)
    # Limit the prompt size for very large documents.
    text_for_ai = text[:120_000]

    return f"""
You are the document-ingestion classifier for an HR document catalogue.

The following YAML/JSON is the authoritative catalogue contract. Do not invent
metadata fields. Use only labels defined in it.

CATALOGUE CONTRACT:
{contract}

TASK:
1. Identify the single most likely document_type from document_types.
2. Extract every applicable label for that document type.
3. Also extract applicable global_labels.
4. If a value is not present or cannot be reliably inferred, use null.
5. Preserve numbers as numbers where possible.
6. Dates should be ISO YYYY-MM-DD when unambiguous.
7. Do not guess sensitive facts.
8. Return ONLY valid JSON with exactly these keys:
   document_type, title, confidence, metadata

metadata must be an object whose keys are labels from the contract.

Filename: {filename}

DOCUMENT TEXT:
{text_for_ai}
""".strip()


def ask_ollama(prompt: str) -> dict[str, Any]:
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        },
        timeout=300,
    )
    response.raise_for_status()
    raw = response.json()["response"]
    return json.loads(raw)


def make_s3():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
        config=Config(signature_version="s3v4"),
    )


def ensure_bucket(s3):
    try:
        s3.head_bucket(Bucket=MINIO_BUCKET)
    except Exception:
        s3.create_bucket(Bucket=MINIO_BUCKET)


def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


def exact_duplicate(conn: sqlite3.Connection, content_hash: str):
    return conn.execute(
        "SELECT id, filename, minio_key FROM documents WHERE content_hash = ?",
        (content_hash,),
    ).fetchone()


def fuzzy_duplicate(
    conn: sqlite3.Connection,
    text: str,
    document_type: str | None,
    threshold: float,
):
    if not text:
        return None

    normalized = normalize_text(text)[:30000]

    query = """
        SELECT id, filename, extracted_text
        FROM documents
        WHERE extracted_text IS NOT NULL
    """
    params = []

    if document_type:
        query += " AND document_type = ?"
        params.append(document_type)

    # Compare against a bounded candidate set. For a large catalogue,
    # replace this with embeddings/vector search.
    query += " ORDER BY id DESC LIMIT 500"

    best = None
    best_score = 0.0

    for row in conn.execute(query, params):
        candidate = normalize_text(row[2] or "")[:30000]
        if not candidate:
            continue

        score = SequenceMatcher(None, normalized, candidate).ratio()
        if score > best_score:
            best_score = score
            best = (row[0], row[1], score)

    if best and best[2] >= threshold:
        return best
    return None


def sanitize_key(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name[:180] or "document"


def ingest(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(path)

    contents = load_contents()
    threshold = float(
        contents.get("duplicate_detection", {})
        .get("fuzzy_text_similarity_threshold", 0.94)
    )

    conn = init_db()
    s3 = make_s3()
    ensure_bucket(s3)

    content_hash = sha256_file(path)

    duplicate = exact_duplicate(conn, content_hash)
    if duplicate:
        print(f"EXACT DUPLICATE: document #{duplicate[0]} ({duplicate[1]})")
        print(f"Existing MinIO object: {duplicate[2]}")
        return

    print("Extracting text...")
    text = extract_text(path)

    print(f"Running AI classification with {OLLAMA_MODEL}...")
    analysis = ask_ollama(build_ai_prompt(contents, path.name, text))

    document_type = analysis.get("document_type")
    title = analysis.get("title")
    confidence = analysis.get("confidence")
    metadata = analysis.get("metadata") or {}

    fuzzy = None
    if contents.get("duplicate_detection", {}).get("compare_same_document_type", True):
        fuzzy = fuzzy_duplicate(conn, text, document_type, threshold)

    document_uuid = str(uuid.uuid4())
    key = (
        f"{document_type or 'unknown'}/"
        f"{document_uuid}/"
        f"{sanitize_key(path.name)}"
    )

    print(f"Uploading to MinIO: s3://{MINIO_BUCKET}/{key}")
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

    s3.upload_file(
        str(path),
        MINIO_BUCKET,
        key,
        ExtraArgs={"ContentType": mime_type},
    )

    duplicate_of = fuzzy[0] if fuzzy else None

    conn.execute(
        """
        INSERT INTO documents (
            document_uuid, filename, mime_type, size_bytes, content_hash,
            minio_bucket, minio_key, document_type, title, extracted_text,
            metadata_json, ai_model, ai_confidence, duplicate_of
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            document_uuid,
            path.name,
            mime_type,
            path.stat().st_size,
            content_hash,
            MINIO_BUCKET,
            key,
            document_type,
            title,
            text,
            json.dumps(metadata, ensure_ascii=False),
            OLLAMA_MODEL,
            confidence,
            duplicate_of,
        ),
    )
    conn.commit()

    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    print(f"Inserted document #{row_id}")
    print(f"Type: {document_type}")
    print(f"Title: {title}")
    print(f"Metadata: {json.dumps(metadata, ensure_ascii=False)}")

    if fuzzy:
        print(
            f"ALMOST DUPLICATE: document #{fuzzy[0]} ({fuzzy[1]}), "
            f"similarity={fuzzy[2]:.3f}"
        )
        print("Stored anyway; duplicate_of points to the existing document.")

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="AI-assisted HR document ingestion into SQLite + MinIO."
    )
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    ingest(args.file)


if __name__ == "__main__":
    main()
