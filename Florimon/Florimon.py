import email
from email import policy
import io
import re
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
import zlib
from pathlib import Path

# ---------- Pad-definities ----------
ZIP_PATH = Path.home() / "Downloads" / "test_emails.zip"
EXTRACT_DIR = Path.home() / "Downloads" / "test_emails"
IMPORTANT_DIR = Path.home() / "Downloads" / "important_documents"
MAYBE_IMPORTANT_DIR = Path.home() / "Downloads" / "maybe_important_documents"
DB_PATH = Path.home() / "Downloads" / "documents.db"


# ---------- Tekstextractie uit Bytes ----------
def read_txt_bytes(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")


def read_docx_bytes(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if "word/document.xml" not in z.namelist():
                return ""
            xml_data = z.read("word/document.xml")
        root = ET.fromstring(xml_data)
        return " ".join(el.text for el in root.iter() if el.tag.endswith("}t") and el.text)
    except Exception:
        return data.decode("utf-8", errors="ignore")


def read_xlsx_bytes(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if "xl/sharedStrings.xml" not in z.namelist():
                return ""
            xml_data = z.read("xl/sharedStrings.xml")
        root = ET.fromstring(xml_data)
        return " ".join(el.text for el in root.iter() if el.tag.endswith("}t") and el.text)
    except Exception:
        return data.decode("utf-8", errors="ignore")


def read_pdf_bytes(data: bytes) -> str:
    text = []
    for stream in re.findall(rb"stream\r?\n(.*?)\r?\nendstream", data, re.DOTALL):
        try:
            stream = zlib.decompress(stream)
        except zlib.error:
            pass
        for part in re.findall(rb"\((.*?)(?<!\\)\)", stream):
            text.append(part.decode("latin-1", errors="ignore"))
    return " ".join(text)


def extract_text_from_attachment(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".txt":
        return read_txt_bytes(data)
    if suffix == ".docx":
        return read_docx_bytes(data)
    if suffix == ".xlsx":
        return read_xlsx_bytes(data)
    if suffix == ".pdf":
        return read_pdf_bytes(data)
    return ""


# ---------- Score en Sleutelwoorden ----------
HIGH_THRESHOLD = 5
LOW_THRESHOLD = 3

SD_WORX_KEYWORDS = {
    # Direct Payroll & Salary (+5 / +6)
    "sd worx": 6, "payroll": 5, "payslip": 5, "loonstrook": 5, "salarisstrook": 5,
    "salary": 5, "salaris": 5, "wedde": 5, "loon": 5, "jaaropgave": 5, "fiche 281": 5,
    "13e maand": 5, "thirteenth month": 5, "holiday allowance": 4, "vakantiegeld": 4,
    "bonus": 4, "commission": 4, "provisie": 4,

    # Legal & Employment Contracts (+5)
    "contract": 5, "arbeidsovereenkomst": 5, "employment agreement": 5, "addendum": 4,
    "termination": 5, "ontslag": 5, "resignation": 4, "opzegging": 4, "severance": 5,
    "transitievergoeding": 5,

    # Invoicing & Expenses (+4)
    "invoice": 4, "factuur": 4, "expense report": 4, "onkostennota": 4,
    "declaration": 3, "declaratie": 3, "reimbursement": 3, "vergoeding": 3,

    # Tax, Pension & Social Security (+3 / +4)
    "tax": 3, "belasting": 3, "bedrijfsvoorheffing": 4, "withholding tax": 4,
    "pension": 4, "pensioen": 4, "groepsverzekering": 4, "social security": 4,
    "rsz": 5, "nssow": 4,

    # Absence, Leave & Health (+3 / +4)
    "sick leave": 4, "ziektemelding": 4, "maternity leave": 4, "bevallingsverlof": 4,
    "parental leave": 4, "ouderschapsverlof": 4, "absence": 3, "verzuim": 3,
    "medical certificate": 4, "doktersattest": 4,

    # General HR & Administration (+2 / +3)
    "hr": 3, "human resources": 3, "personnel": 2, "personeel": 2, "employee": 2,
    "werknemer": 2, "employer": 2, "werkgever": 2, "onboarding": 3, "offboarding": 3,
    "timesheet": 3, "urenkaart": 3, "appraisal": 3, "evaluatie": 3,
}


def calculate_score(filename: str, file_data: bytes, subject: str = "", email_body: str = ""):
    score = 0
    reasons = []
    subject = subject.lower()
    email_body = email_body.lower()
    content = extract_text_from_attachment(filename, file_data).lower()
    suffix = Path(filename).suffix.lower()

    if suffix in [".pdf", ".docx", ".xlsx"]:
        score += 1
        reasons.append("file type +1")

    matched_keywords = set()
    for keyword, weight in SD_WORX_KEYWORDS.items():
        if keyword in subject or keyword in content or keyword in email_body:
            if keyword not in matched_keywords:
                matched_keywords.add(keyword)
                score += weight
                reasons.append(f"'{keyword}' +{weight}")

    if "attached" in email_body or "in bijlage" in email_body or "bijgevoegd" in email_body:
        score += 2
        reasons.append("'attachment indicator' +2")

    return score, reasons


def classify_attachment(filename: str, file_data: bytes, subject: str = "", email_body: str = ""):
    score, reasons = calculate_score(filename, file_data, subject, email_body)

    if score >= HIGH_THRESHOLD:
        status = "IMPORTANT"
    elif score >= LOW_THRESHOLD:
        status = "MAYBE IMPORTANT"
    else:
        status = "NOT IMPORTANT"

    return status, score, reasons


# ---------- Database Beheer ----------
def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS important_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            email_subject TEXT,
            score INTEGER NOT NULL,
            reasons TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maybe_important_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            email_subject TEXT,
            score INTEGER NOT NULL,
            reasons TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_to_subset(filename: str, email_subject: str, status: str, score: int, reasons: list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    reasons_str = ", ".join(reasons) if reasons else "no matches"

    if status == "IMPORTANT":
        table_name = "important_documents"
    elif status == "MAYBE IMPORTANT":
        table_name = "maybe_important_documents"
    else:
        conn.close()
        return

    cursor.execute(f"""
        INSERT INTO {table_name} (filename, email_subject, score, reasons)
        VALUES (?, ?, ?, ?)
    """, (filename, email_subject, score, reasons_str))

    conn.commit()
    conn.close()


def print_database_summary():
    """Telt het aantal rijen per tabel in de database en print een overzicht."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM important_documents")
    important_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM maybe_important_documents")
    maybe_count = cursor.fetchone()[0]

    conn.close()

    print("\n" + "=" * 45)
    print("        OVERZICHT DATABASE INHOUD")
    print("=" * 45)
    print(f"Tabel 'important_documents'       : {important_count} document(en)")
    print(f"Tabel 'maybe_important_documents' : {maybe_count} document(en)")
    print(f"Totaal in database               : {important_count + maybe_count} document(en)")
    print("=" * 45)


# ---------- Bestanden Opslaan ----------
def save_attachment_to_folder(filename: str, file_data: bytes, destination_folder: Path):
    destination_folder.mkdir(parents=True, exist_ok=True)
    destination_path = destination_folder / filename
    destination_path.write_bytes(file_data)


# ---------- EML Bestanden Verwerken ----------
def process_eml_file(eml_path: Path):
    with open(eml_path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    subject = msg.get("subject", "") or ""

    body_parts = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body_parts.append(part.get_content())
    else:
        if msg.get_content_type() == "text/plain":
            body_parts.append(msg.get_content())

    email_body = "\n".join(body_parts)

    for part in msg.walk():
        filename = part.get_filename()
        if not filename:
            continue

        suffix = Path(filename).suffix.lower()
        if suffix not in [".pdf", ".txt", ".docx", ".xlsx"]:
            continue

        file_data = part.get_payload(decode=True)
        if not file_data:
            continue

        status, score, reasons = classify_attachment(filename, file_data, subject, email_body)

        if status == "IMPORTANT":
            save_attachment_to_folder(filename, file_data, IMPORTANT_DIR)
            save_to_subset(filename, subject, status, score, reasons)
        elif status == "MAYBE IMPORTANT":
            save_attachment_to_folder(filename, file_data, MAYBE_IMPORTANT_DIR)
            save_to_subset(filename, subject, status, score, reasons)

        print(f"File: {filename:<30} Score: {score:<3} Status: {status:<18} Subject: {subject}")


# ---------- Hoofdprogramma ----------
if __name__ == "__main__":
    init_database()

    if not ZIP_PATH.exists():
        print(f"Fout: Bestand '{ZIP_PATH}' is niet gevonden.")
    else:
        print(f"Zipbestand uitpakken: {ZIP_PATH}")
        with zipfile.ZipFile(ZIP_PATH, "r") as z:
            z.extractall(EXTRACT_DIR)

        eml_files = list(EXTRACT_DIR.rglob("*.eml"))
        print(f"Gevonden .eml-bestanden: {len(eml_files)}\n")

        for eml_file in eml_files:
            process_eml_file(eml_file)

        # Print het overzicht van de aantallen op het einde
        print_database_summary()