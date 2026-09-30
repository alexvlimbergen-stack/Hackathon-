#!/usr/bin/env python3
"""Build data/hr_catalog.sqlite from schema.sql (deterministic synthetic HR files)."""

from __future__ import annotations

import hashlib
import json
import random
import sqlite3
import uuid
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "hr_catalog.sqlite"
SCHEMA_PATH = ROOT / "schema.sql"
RNG = random.Random(20230930)

ISO = date.fromisoformat


def uid() -> str:
    return str(uuid.UUID(bytes=bytes(RNG.getrandbits(8) for _ in range(16)), version=4))


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def daterange(start: date, end: date) -> date:
    span = (end - start).days
    return start + timedelta(days=RNG.randint(0, max(span, 0)))


def money(lo: float, hi: float, step: float = 10.0) -> float:
    n = int((hi - lo) / step)
    return round(lo + RNG.randint(0, max(n, 0)) * step, 2)


def load_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


LABEL_SCHEMAS = {
    "candidate_cv": ["years_experience", "salary_expectation", "notice_period_days"],
    "interview_notes": ["recommendation_score", "interview_date"],
    "offer_letter": ["offered_annual_salary", "proposed_start_date", "bonus_target_pct"],
    "background_check": ["completed_on", "result"],
    "employment_contract": [
        "annual_salary",
        "hourly_rate",
        "fte",
        "probation_end",
        "notice_period_days",
    ],
    "nda": ["term_years", "effective_from"],
    "policy_acknowledgement": ["acknowledged_on", "policy_version"],
    "payslip": ["gross_pay", "net_pay", "tax_withheld", "hours_worked", "period_end"],
    "loan_document": [
        "principal_amount",
        "outstanding_balance",
        "interest_rate_pct",
        "term_months",
        "first_due_date",
    ],
    "benefits_enrollment": [
        "employer_monthly_contribution",
        "employee_monthly_contribution",
        "coverage_start",
    ],
    "tax_form": ["tax_year", "taxable_wage"],
    "timesheet": ["hours_regular", "hours_overtime", "billable_amount", "period_end"],
    "expense_report": ["claimed_amount", "approved_amount", "trip_start"],
    "client_invoice": [
        "amount_excl_vat",
        "vat_amount",
        "amount_incl_vat",
        "due_date",
        "paid_on",
    ],
    "id_document": ["expiry_date"],
    "work_permit": ["valid_from", "expiry_date"],
    "performance_review": ["overall_score", "cycle_year"],
    "training_certificate": ["credits", "valid_until", "completed_on"],
    "termination_letter": ["last_working_day", "severance_amount", "garden_leave_days"],
    "medical_leave": ["leave_start", "expected_return", "occupational_pct"],
}

TYPE_META = {
    "candidate_cv": ("Candidate CV", "pre_hire", "ephemeral_2y", "confidential", "standard"),
    "interview_notes": ("Interview notes", "pre_hire", "ephemeral_2y", "confidential", "standard"),
    "offer_letter": ("Offer letter", "pre_hire", "personnel_7y", "confidential", "standard"),
    "background_check": ("Background check", "pre_hire", "personnel_7y", "restricted", "high"),
    "employment_contract": ("Employment contract", "employment_core", "contract_10y", "confidential", "standard"),
    "nda": ("Non-disclosure agreement", "employment_core", "contract_10y", "confidential", "low"),
    "policy_acknowledgement": ("Policy acknowledgement", "employment_core", "personnel_7y", "internal", "low"),
    "payslip": ("Payslip", "compensation", "payroll_10y", "restricted", "high"),
    "loan_document": ("Employee loan agreement", "compensation", "financial_10y", "restricted", "high"),
    "benefits_enrollment": ("Benefits enrollment", "compensation", "personnel_7y", "confidential", "standard"),
    "tax_form": ("Tax form", "compensation", "payroll_10y", "restricted", "high"),
    "timesheet": ("Timesheet", "time_and_billing", "financial_10y", "internal", "low"),
    "expense_report": ("Expense report", "time_and_billing", "financial_10y", "confidential", "standard"),
    "client_invoice": ("Client invoice", "time_and_billing", "financial_10y", "confidential", "low"),
    "id_document": ("Identity document copy", "mobility", "immigration_10y", "restricted", "high"),
    "work_permit": ("Work permit / residence", "mobility", "immigration_10y", "restricted", "high"),
    "performance_review": ("Performance review", "talent_cycle", "personnel_7y", "confidential", "standard"),
    "training_certificate": ("Training certificate", "talent_cycle", "personnel_7y", "internal", "none"),
    "termination_letter": ("Termination letter", "offboarding", "personnel_7y", "confidential", "standard"),
    "medical_leave": ("Medical leave file", "offboarding", "medical_30y", "restricted", "high"),
}

MIME = {
    "candidate_cv": ("application/pdf", "pdf"),
    "interview_notes": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"),
    "offer_letter": ("application/pdf", "pdf"),
    "background_check": ("application/pdf", "pdf"),
    "employment_contract": ("application/pdf", "pdf"),
    "nda": ("application/pdf", "pdf"),
    "policy_acknowledgement": ("application/pdf", "pdf"),
    "payslip": ("application/pdf", "pdf"),
    "loan_document": ("application/pdf", "pdf"),
    "benefits_enrollment": ("application/pdf", "pdf"),
    "tax_form": ("application/pdf", "pdf"),
    "timesheet": ("text/csv", "csv"),
    "expense_report": ("application/pdf", "pdf"),
    "client_invoice": ("application/pdf", "pdf"),
    "id_document": ("image/jpeg", "jpg"),
    "work_permit": ("application/pdf", "pdf"),
    "performance_review": ("application/pdf", "pdf"),
    "training_certificate": ("application/pdf", "pdf"),
    "termination_letter": ("application/pdf", "pdf"),
    "medical_leave": ("application/pdf", "pdf"),
}


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    load_schema(conn)

    entities = [
        ("MER-NL", "Meridian HR Collective B.V.", "NL", "NL822199441B01", "24183421", "Europe/Amsterdam"),
        ("MER-BE", "Meridian HR Collective NV", "BE", "BE0777123456", "0777.123.456", "Europe/Brussels"),
        ("MER-DE", "Meridian HR Collective GmbH", "DE", "DE813456789", "HRB 118822", "Europe/Berlin"),
        ("MER-GB", "Meridian HR Collective Ltd", "GB", "GB884422110", "OC991122", "Europe/London"),
    ]
    conn.executemany(
        """INSERT INTO legal_entities(code,name,country_code,vat_number,chamber_id,timezone)
           VALUES (?,?,?,?,?,?)""",
        entities,
    )
    entity_ids = {row[0]: i + 1 for i, row in enumerate(entities)}

    clients = [
        ("helix-logistics", "Helix Logistics B.V.", "Helix", "NL", "transport", "EUR", "Sofie Vermeer", "2021-03-12", "medium", 420),
        ("nordlicht-energy", "Nordlicht Energy GmbH", "Nordlicht", "DE", "energy", "EUR", "Jonas Weber", "2019-11-02", "high", 1100),
        ("orbita-health", "Orbita Health NV", "Orbita", "BE", "healthcare", "EUR", "Amira Benali", "2022-06-18", "medium", 260),
        ("quartz-retail", "Quartz Retail Ltd", "Quartz", "GB", "retail", "GBP", "Priya Shah", "2020-01-09", "low", 780),
        ("lumen-fintech", "Lumen Fintech B.V.", "Lumen", "NL", "finance", "EUR", "Sofie Vermeer", "2023-09-01", "high", 95),
        ("atlas-foods", "Atlas Foods SAS", "Atlas", "FR", "food", "EUR", "Amira Benali", "2018-04-22", "low", 640),
        ("cipher-labs", "Cipher Labs Inc.", "Cipher", "US", "software", "USD", "Jonas Weber", "2024-02-14", "medium", 180),
        ("meridian-internal", "Meridian HR Collective (internal)", "Meridian", "NL", "professional_services", "EUR", "Board", "2015-01-01", "low", 85),
    ]
    conn.executemany(
        """INSERT INTO clients(slug,legal_name,trading_name,country_code,industry,billing_currency,
           account_manager,msa_signed_on,risk_tier,employee_headcount) VALUES (?,?,?,?,?,?,?,?,?,?)""",
        clients,
    )
    client_ids = {row[0]: i + 1 for i, row in enumerate(clients)}
    client_by_id = {i + 1: row for i, row in enumerate(clients)}

    first_names = [
        "Eva", "Tomasz", "Amira", "Lars", "Noor", "Jules", "Mila", "Farid", "Hanne", "Owen",
        "Sanne", "Diego", "Leila", "Koen", "Yara", "Niels", "Ines", "Bram", "Sofia", "Mateo",
        "Anouk", "Piotr", "Chloe", "Daan", "Amina", "Ruben", "Elise", "Viktor", "Lotte", "Samir",
    ]
    last_names = [
        "Bakker", "Kowalski", "Haddad", "Jansen", "Peeters", "Dubois", "Nguyen", "Iqbal", "De Vries",
        "Moreau", "Schmidt", "Costa", "Willems", "Berg", "Kaya", "Van Dam", "Leroy", "Silva",
    ]
    titles = [
        "Warehouse coordinator", "Payroll specialist", "Site nurse", "Java engineer", "Store lead",
        "Control-room operator", "Recruiter", "Finance analyst", "HSE advisor", "Data engineer",
        "Picker", "Legal counsel", "Lab technician", "Account executive", "Forklift driver",
    ]
    depts = ["operations", "payroll", "clinical", "engineering", "retail", "energy", "talent", "finance"]
    people_rows = []
    for i in range(32):
        fn, ln = first_names[i % len(first_names)], last_names[(i * 3) % len(last_names)]
        name = f"{fn} {ln}"
        role = ["employee", "employee", "employee", "contractor", "candidate", "alumni"][i % 6]
        home = ["NL", "BE", "DE", "GB", "FR", "US", "PL"][i % 7]
        work = ["NL", "BE", "DE", "GB", "NL", "BE", "DE"][i % 7]
        client_slug = list(client_ids.keys())[i % 7] if role != "candidate" else None
        if role == "alumni":
            client_slug = list(client_ids.keys())[(i + 2) % 7]
        legal = ["MER-NL", "MER-BE", "MER-DE", "MER-GB"][{"NL": 0, "BE": 1, "DE": 2, "GB": 3, "FR": 1, "US": 0, "PL": 0}[work]]
        hire = daterange(ISO("2018-01-01"), ISO("2025-06-01")) if role != "candidate" else None
        term = None
        if role == "alumni":
            term = daterange(hire, ISO("2026-03-01"))
        fte = 1.0 if role == "employee" else (0.8 if role == "contractor" else None)
        if i % 9 == 0 and role == "employee":
            fte = 0.6
        people_rows.append(
            (
                f"E{24000 + i}",
                fn,
                name,
                role,
                home,
                work,
                f"{fn.lower()}.{ln.lower().replace(' ', '')}@people.meridian-hr.test",
                f"CC-{100 + (i % 12)}",
                depts[i % len(depts)],
                titles[i % len(titles)],
                client_ids[client_slug] if client_slug else None,
                entity_ids[legal],
                hire.isoformat() if hire else None,
                term.isoformat() if term else None,
                fte,
                f"E{24000 + (i % 7)}" if i > 6 else None,
            )
        )
    conn.executemany(
        """INSERT INTO people(employee_number,preferred_name,legal_name,role_kind,home_country,work_country,
           email,cost_center,department,job_title,client_id,legal_entity_id,hire_date,termination_date,fte,manager_employee_number)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        people_rows,
    )
    people = conn.execute(
        "SELECT id, employee_number, preferred_name, legal_name, role_kind, home_country, work_country, email, "
        "cost_center, department, job_title, client_id, legal_entity_id, hire_date, termination_date, fte FROM people"
    ).fetchall()

    type_notes = {
        k: f"Extract {', '.join(v)}; keep nested facts in extracted_json."
        for k, v in LABEL_SCHEMAS.items()
    }
    for code, labels in LABEL_SCHEMAS.items():
        display, family, ret, clas, pii = TYPE_META[code]
        schema = {lab: "typed sorting_label" for lab in labels}
        conn.execute(
            """INSERT INTO document_types(code,display_name,family,default_retention,default_classification,pii_class,label_schema_json,extraction_notes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (code, display, family, ret, clas, pii, json.dumps(schema), type_notes[code]),
        )

    inserted: list[str] = []
    by_person_type: dict[tuple[int, str], list[str]] = {}

    def add_tags(doc_id: str, tags: list[tuple[str, str, str]]) -> None:
        conn.executemany(
            "INSERT INTO document_tags(document_id,namespace,key,value) VALUES (?,?,?,?)",
            [(doc_id, ns, k, v) for ns, k, v in tags],
        )

    def add_labels(doc_id: str, labels: list[dict]) -> None:
        for lab in labels:
            conn.execute(
                """INSERT INTO sorting_labels(document_id,label_key,value_type,value_numeric,value_text,value_date,currency,unit)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    doc_id,
                    lab["key"],
                    lab["type"],
                    lab.get("numeric"),
                    lab.get("text"),
                    lab.get("date"),
                    lab.get("currency"),
                    lab.get("unit"),
                ),
            )

    def add_entities(doc_id: str, ents: list[tuple]) -> None:
        conn.executemany(
            """INSERT INTO extracted_entities(document_id,entity_type,raw_value,normalized_value,confidence,page,role_in_document)
               VALUES (?,?,?,?,?,?,?)""",
            [(doc_id, *e) for e in ents],
        )

    def insert_doc(
        *,
        dtype: str,
        title: str,
        person,
        client_id: int | None,
        country: str,
        lang: str,
        issued: date,
        received: date,
        effective_from: date | None,
        effective_to: date | None,
        status: str,
        workflow: str,
        source: str,
        pages: int | None,
        text: str,
        payload: dict,
        labels: list[dict],
        extra_tags: list[tuple[str, str, str]],
        classification: str | None = None,
        pii: str | None = None,
        retain_until: str | None = None,
        revision: int = 1,
    ) -> str:
        doc_id = uid()
        mime, ext = MIME[dtype]
        meta = TYPE_META[dtype]
        _, family, ret, clas, pii_def = meta
        clas = classification or clas
        pii = pii or pii_def
        le_id = person[12] if person else 1
        empno = person[1] if person else "none"
        filename = f"{dtype}_{empno}_{issued.isoformat()}.{ext}"
        viewer = f"https://dms.meridian-hr.local/open?id={doc_id}&rev={revision}"
        deep = f"meridian-dms://v1/doc/{doc_id}?rev={revision}"
        sp = f"https://meridianhr.sharepoint.local/sites/people-ops/doc.aspx?unique={doc_id}"
        size = RNG.randint(48_000, 2_400_000) if ext != "csv" else RNG.randint(2_000, 40_000)
        ocr = round(RNG.uniform(0.86, 0.99), 3) if ext in {"pdf", "jpg"} else 1.0
        conn.execute(
            """INSERT INTO documents(
                id,document_type,title,original_filename,mime_type,byte_size,page_count,language_code,country_code,
                client_id,person_id,legal_entity_id,classification,pii_level,retention_class,retain_until,status,
                issued_on,effective_from,effective_to,received_on,indexed_on,ocr_confidence,source_system,workflow_state,
                revision,deep_link,viewer_link,sharepoint_link,content_sha256,extracted_text,extracted_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                doc_id,
                dtype,
                title,
                filename,
                mime,
                size,
                pages,
                lang,
                country,
                client_id,
                person[0] if person else None,
                le_id,
                clas,
                pii,
                ret,
                retain_until,
                status,
                issued.isoformat(),
                effective_from.isoformat() if effective_from else None,
                effective_to.isoformat() if effective_to else None,
                received.isoformat(),
                (received + timedelta(days=1)).isoformat(),
                ocr,
                source,
                workflow,
                revision,
                deep,
                viewer,
                sp,
                sha(deep + text[:200]),
                text,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        client_slug = client_by_id[client_id][0] if client_id else "unassigned"
        le_code = conn.execute("SELECT code FROM legal_entities WHERE id=?", (le_id,)).fetchone()[0]
        year = str(issued.year)
        q = f"Q{(issued.month - 1) // 3 + 1}"
        role_kind = person[4] if person else "candidate"
        emp_status = "active"
        if person:
            if person[4] == "alumni":
                emp_status = "terminated"
            elif person[4] == "candidate":
                emp_status = "not_hired" if RNG.random() < 0.3 else "never_started"
        dept_tag = person[9] if person else "talent"
        tags = [
            ("geo", "country", country),
            ("party", "client_slug", client_slug),
            ("party", "legal_entity_code", le_code),
            ("classification", "sensitivity", clas),
            ("classification", "pii_level", pii),
            ("classification", "retention_class", ret),
            ("classification", "legal_hold", "active" if RNG.random() < 0.04 else "none"),
            ("content", "file_type", dtype),
            ("content", "document_family", family),
            ("content", "language", lang),
            ("ops", "source_system", source),
            ("ops", "workflow_state", workflow),
            ("ops", "department", {
                "candidate_cv": "talent",
                "interview_notes": "talent",
                "offer_letter": "talent",
                "background_check": "talent",
                "employment_contract": "legal",
                "nda": "legal",
                "policy_acknowledgement": "people_ops",
                "payslip": "payroll",
                "loan_document": "payroll",
                "benefits_enrollment": "people_ops",
                "tax_form": "payroll",
                "timesheet": "finance",
                "expense_report": "finance",
                "client_invoice": "finance",
                "id_document": "immigration",
                "work_permit": "immigration",
                "performance_review": "people_ops",
                "training_certificate": "learning",
                "termination_letter": "legal",
                "medical_leave": "people_ops",
            }[dtype]),
            ("ops", "document_year", year),
            ("ops", "quarter", q),
            ("employment", "role_kind", role_kind),
            ("employment", "employment_status", emp_status),
        ]
        if person:
            tags.append(("party", "employee_number", person[1]))
            tags.append(("ops", "cost_center", person[8]))
        tags.extend(extra_tags)
        add_tags(doc_id, tags)
        add_labels(doc_id, labels)
        inserted.append(doc_id)
        if person:
            by_person_type.setdefault((person[0], dtype), []).append(doc_id)
        conn.execute(
            "INSERT INTO ingestion_events(document_id,occurred_on,actor,channel,detail) VALUES (?,?,?,?,?)",
            (
                doc_id,
                received.isoformat(),
                source,
                source,
                f"Indexed {dtype} title={title}",
            ),
        )
        return doc_id

    currencies = {"NL": "EUR", "BE": "EUR", "DE": "EUR", "FR": "EUR", "GB": "GBP", "US": "USD", "PL": "EUR"}
    cities = {"NL": "Rotterdam", "BE": "Antwerp", "DE": "Hamburg", "GB": "Manchester", "FR": "Lille", "US": "Austin", "PL": "Warsaw"}

    workforce = [p for p in people if p[4] in {"employee", "contractor", "alumni"}]
    candidates = [p for p in people if p[4] == "candidate"]
    active = [p for p in workforce if p[4] != "alumni"]

    # CVs + interviews + some offers + background
    for p in candidates + workforce[:8]:
        country = p[6]
        lang = {"NL": "nl", "BE": "nl", "DE": "de", "GB": "en", "FR": "fr", "US": "en", "PL": "en"}[country]
        issued = daterange(ISO("2023-01-01"), ISO("2026-08-01"))
        years = RNG.randint(1, 18)
        ask = money(32000, 92000, 500)
        text = (
            f"CURRICULUM VITAE\nName: {p[3]}\nHeadline: {p[10]}\nYears experience: {years}\n"
            f"Skills: SAP, Excel, stakeholder mgmt\nLast employer: Contoso Industries\n"
            f"Languages: {lang}, en\nEmail: {p[7]}\nSalary expectation: {ask} {currencies[country]}"
        )
        cv_id = insert_doc(
            dtype="candidate_cv",
            title=f"CV — {p[3]}",
            person=p,
            client_id=p[11],
            country=country,
            lang=lang,
            issued=issued,
            received=issued + timedelta(days=1),
            effective_from=None,
            effective_to=None,
            status="active",
            workflow="archived" if p[4] != "candidate" else "pending_approval",
            source="recruiter_ats",
            pages=RNG.randint(1, 3),
            text=text,
            payload={
                "headline": p[10],
                "skills": RNG.sample(
                    ["python", "sap", "excel", "forklift", "gdpr", "java", "salesforce", "first_aid"], 4
                ),
                "last_employer": "Contoso Industries",
                "education_highest": RNG.choice(["MBO-4", "HBO", "WO", "A-levels", "BTS"]),
                "languages": {lang: "native", "en": "b2"},
                "willing_to_relocate": RNG.choice([True, False]),
            },
            labels=[
                {"key": "years_experience", "type": "integer", "numeric": years},
                {"key": "salary_expectation", "type": "money", "numeric": ask, "currency": currencies[country]},
                {"key": "notice_period_days", "type": "integer", "numeric": RNG.choice([14, 28, 30, 60])},
            ],
            extra_tags=[("geo", "work_location_city", cities[country]), ("content", "template_code", "cv-europass-v3")],
        )
        if p[4] == "candidate" or RNG.random() < 0.5:
            idate = issued + timedelta(days=RNG.randint(5, 20))
            score = RNG.randint(1, 5)
            rec = ["reject", "hold", "progress", "offer"][min(score, 4) - 1] if score else "hold"
            notes = insert_doc(
                dtype="interview_notes",
                title=f"Interview round {RNG.randint(1,3)} — {p[2]}",
                person=p,
                client_id=p[11],
                country=country,
                lang=lang,
                issued=idate,
                received=idate,
                effective_from=idate,
                effective_to=None,
                status="active",
                workflow="approved",
                source="recruiter_ats",
                pages=2,
                text=f"Interview with {p[3]}. Score {score}/5. Recommendation: {rec}. Strengths: communication. Risks: notice period.",
                payload={
                    "round": RNG.randint(1, 3),
                    "interviewers": ["Sofie Vermeer", "Lars Jansen"],
                    "strengths": ["communication", "domain knowledge"],
                    "risks": ["notice period"],
                    "recommendation": rec,
                },
                labels=[
                    {"key": "recommendation_score", "type": "integer", "numeric": score},
                    {"key": "interview_date", "type": "date", "date": idate.isoformat()},
                ],
                extra_tags=[("content", "template_code", "int-notes-v2")],
            )
            conn.execute(
                "INSERT INTO document_relations VALUES (?,?,?,?)",
                (notes, cv_id, "annex_of", "interview notes attached to CV packet"),
            )

    for p in active:
        country = p[6]
        lang = {"NL": "nl", "BE": "nl", "DE": "de", "GB": "en", "FR": "fr", "US": "en"}.get(country, "en")
        cur = currencies.get(country, "EUR")
        hire = ISO(p[13]) if p[13] else ISO("2022-01-01")
        salary = money(28000, 88000, 500)
        fte = p[15] or 1.0
        hourly = round(salary / (1872 * fte), 2) if fte else None
        probation = hire + timedelta(days=60)
        notice = 30 if p[4] == "employee" else 14
        payload = {
            "contract_form": "definite" if p[4] == "contractor" else "indefinite",
            "scale_step": f"schaal-{RNG.randint(6, 12)}",
            "holiday_hours": int(200 * fte),
            "non_compete_months": 6 if RNG.random() < 0.4 else 0,
            "governing_law": country,
            "signatories": [p[3], "Meridian HR Collective"],
        }
        text = (
            f"EMPLOYMENT AGREEMENT\nParty A: Meridian\nParty B: {p[3]}\nStart: {hire.isoformat()}\n"
            f"FTE: {fte}\nAnnual salary: {salary} {cur}\nHourly: {hourly}\nProbation until {probation}\n"
            f"Notice: {notice} days\nJob: {p[10]}\nIBAN beneficiary payroll: NL{RNG.randint(10,99)}MERID{RNG.randint(1000000,9999999)}"
        )
        cid = insert_doc(
            dtype="employment_contract",
            title=f"Contract — {p[3]}",
            person=p,
            client_id=p[11],
            country=country,
            lang=lang,
            issued=hire - timedelta(days=10),
            received=hire - timedelta(days=8),
            effective_from=hire,
            effective_to=None,
            status="active",
            workflow="executed",
            source="legal_esign",
            pages=RNG.randint(8, 22),
            text=text,
            payload=payload,
            labels=[
                {"key": "annual_salary", "type": "money", "numeric": salary, "currency": cur},
                {"key": "hourly_rate", "type": "money", "numeric": hourly, "currency": cur},
                {"key": "fte", "type": "float", "numeric": fte},
                {"key": "probation_end", "type": "date", "date": probation.isoformat()},
                {"key": "notice_period_days", "type": "integer", "numeric": notice},
            ],
            extra_tags=[
                ("geo", "work_location_city", cities.get(country, "Rotterdam")),
                ("content", "signature_status", "fully_executed"),
                ("content", "template_code", "emp-nl-v5" if country == "NL" else "emp-intl-v3"),
            ],
            retain_until=(hire.replace(year=hire.year + 10)).isoformat(),
        )
        nda_from = hire - timedelta(days=10)
        insert_doc(
            dtype="nda",
            title=f"NDA — {p[3]}",
            person=p,
            client_id=p[11],
            country=country,
            lang="en" if RNG.random() < 0.5 else lang,
            issued=nda_from,
            received=nda_from,
            effective_from=nda_from,
            effective_to=nda_from.replace(year=nda_from.year + 5),
            status="active",
            workflow="executed",
            source="legal_esign",
            pages=6,
            text=f"MUTUAL NDA between Meridian and {p[3]}. Term 5 years. Governing law {country}.",
            payload={"mutual": True, "carveouts": ["public_domain", "prior_knowledge"], "governing_law": country},
            labels=[
                {"key": "term_years", "type": "integer", "numeric": 5},
                {"key": "effective_from", "type": "date", "date": nda_from.isoformat()},
            ],
            extra_tags=[("content", "signature_status", "fully_executed")],
        )
        ack = hire + timedelta(days=1)
        insert_doc(
            dtype="policy_acknowledgement",
            title=f"Code of conduct ack — {p[2]}",
            person=p,
            client_id=p[11],
            country=country,
            lang=lang,
            issued=ack,
            received=ack,
            effective_from=ack,
            effective_to=None,
            status="active",
            workflow="executed",
            source="employee_portal",
            pages=1,
            text=f"{p[3]} acknowledged POL-COC-2024 via employee portal on {ack.isoformat()}.",
            payload={"policy_code": "POL-COC-2024", "policy_title": "Code of conduct", "channel": "employee_portal"},
            labels=[
                {"key": "acknowledged_on", "type": "date", "date": ack.isoformat()},
                {"key": "policy_version", "type": "enum", "text": "2024.3"},
            ],
            extra_tags=[("content", "template_code", "pol-ack-v1")],
        )
        offer_day = hire - timedelta(days=21)
        offered = salary
        oid = insert_doc(
            dtype="offer_letter",
            title=f"Offer — {p[3]}",
            person=p,
            client_id=p[11],
            country=country,
            lang=lang,
            issued=offer_day,
            received=offer_day,
            effective_from=hire,
            effective_to=offer_day + timedelta(days=14),
            status="superseded",
            workflow="executed",
            source="recruiter_ats",
            pages=3,
            text=f"Offer of employment to {p[3]} at {offered} {cur} starting {hire.isoformat()}. Bonus target 8%. Expires in 14 days.",
            payload={"offer_expiry": (offer_day + timedelta(days=14)).isoformat(), "equity_note": None, "probation_months": 2, "work_pattern": f"{fte} FTE"},
            labels=[
                {"key": "offered_annual_salary", "type": "money", "numeric": offered, "currency": cur},
                {"key": "proposed_start_date", "type": "date", "date": hire.isoformat()},
                {"key": "bonus_target_pct", "type": "float", "numeric": 8.0, "unit": "percent"},
            ],
            extra_tags=[("content", "signature_status", "fully_executed")],
        )
        conn.execute(
            "INSERT INTO document_relations VALUES (?,?,?,?)",
            (cid, oid, "supersedes", "signed contract supersedes offer"),
        )
        bg = offer_day + timedelta(days=3)
        result = RNG.choice(["clear", "clear", "clear", "consider"])
        insert_doc(
            dtype="background_check",
            title=f"Background check — {p[3]}",
            person=p,
            client_id=p[11],
            country=country,
            lang="en",
            issued=bg,
            received=bg,
            effective_from=bg,
            effective_to=None,
            status="active",
            workflow="approved",
            source="email_ingest",
            pages=4,
            text=f"Vendor Certn-Test. Identity + education + criminal (local). Result: {result}. Adverse findings: 0.",
            payload={"vendor": "Certn-Test", "checks_run": ["identity", "education", "criminal_local"], "adverse_findings_count": 0 if result == "clear" else 1},
            labels=[
                {"key": "completed_on", "type": "date", "date": bg.isoformat()},
                {"key": "result", "type": "enum", "text": result},
            ],
            extra_tags=[("content", "template_code", "bgc-eu-v2")],
        )

        # ID + maybe permit
        exp = daterange(ISO("2026-01-01"), ISO("2034-12-01"))
        last4 = f"{RNG.randint(0, 9999):04d}"
        insert_doc(
            dtype="id_document",
            title=f"Passport/ID copy — {p[2]}",
            person=p,
            client_id=p[11],
            country=p[5],
            lang=lang,
            issued=hire - timedelta(days=5),
            received=hire - timedelta(days=5),
            effective_from=None,
            effective_to=exp,
            status="active",
            workflow="archived",
            source="scanner_mailroom",
            pages=2,
            text=f"Scan of {RNG.choice(['passport', 'national_id'])} {p[5]} last4 {last4} expiring {exp.isoformat()}. Name {p[3]}.",
            payload={
                "doc_kind": RNG.choice(["passport", "national_id"]),
                "issuing_country": p[5],
                "last4": last4,
                "nationality": p[5],
            },
            labels=[{"key": "expiry_date", "type": "date", "date": exp.isoformat()}],
            extra_tags=[("geo", "region", "schengen" if p[5] in {"NL", "BE", "DE", "FR", "PL"} else "other")],
        )
        if p[5] != p[6] or p[5] in {"US", "PL"}:
            vf = hire
            pe = daterange(ISO("2026-06-01"), ISO("2028-12-01"))
            pid = insert_doc(
                dtype="work_permit",
                title=f"Work permit — {p[3]}",
                person=p,
                client_id=p[11],
                country=p[6],
                lang="en",
                issued=vf - timedelta(days=20),
                received=vf - timedelta(days=15),
                effective_from=vf,
                effective_to=pe,
                status="active",
                workflow="executed",
                source="email_ingest",
                pages=5,
                text=f"Permit class ICT/GVVA for {p[3]} sponsored by Meridian. Valid {vf}–{pe}. Hours cap 40.",
                payload={"permit_class": RNG.choice(["GVVA", "ICT", "skilled_worker", "blue_card"]), "sponsor_legal_entity": "MER-NL", "hours_cap": 40, "remarks": None},
                labels=[
                    {"key": "valid_from", "type": "date", "date": vf.isoformat()},
                    {"key": "expiry_date", "type": "date", "date": pe.isoformat()},
                ],
                extra_tags=[("content", "template_code", "permit-eu-v1")],
            )
            conn.execute(
                "INSERT INTO document_relations VALUES (?,?,?,?)",
                (pid, cid, "permit_supports_contract", None),
            )

        # payslips last 4 months
        contract_id = cid
        for m in range(4):
            period_end = date(2026, 9, 30) - timedelta(days=30 * m)
            period_start = period_end.replace(day=1)
            gross = round(salary / 12, 2)
            tax = round(gross * 0.32, 2)
            net = round(gross - tax - 40, 2)
            hours = round(160 * fte, 1)
            iban = f"NL{RNG.randint(10,99):02d}INGB{RNG.randint(10**8, 10**9-1)}"
            ps = insert_doc(
                dtype="payslip",
                title=f"Payslip {period_start.strftime('%Y-%m')} — {p[2]}",
                person=p,
                client_id=p[11],
                country=country,
                lang=lang,
                issued=period_end + timedelta(days=2),
                received=period_end + timedelta(days=2),
                effective_from=period_start,
                effective_to=period_end,
                status="active",
                workflow="paid",
                source="payroll_engine",
                pages=2,
                text=(
                    f"PAYSLIP {period_start}–{period_end}\nEmployee {p[3]} ({p[1]})\n"
                    f"Gross {gross} {cur}\nTax {tax}\nNet {net}\nHours {hours}\nCredit {iban}\nYTD gross {round(gross*(12-m),2)}"
                ),
                payload={
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    "earnings_lines": [{"code": "BASE", "amount": gross}],
                    "deduction_lines": [{"code": "WAGE_TAX", "amount": tax}, {"code": "PENSION", "amount": 40}],
                    "ytd_gross": round(gross * (9 - m), 2),
                    "employer_cost": round(gross * 1.28, 2),
                },
                labels=[
                    {"key": "gross_pay", "type": "money", "numeric": gross, "currency": cur},
                    {"key": "net_pay", "type": "money", "numeric": net, "currency": cur},
                    {"key": "tax_withheld", "type": "money", "numeric": tax, "currency": cur},
                    {"key": "hours_worked", "type": "float", "numeric": hours, "unit": "hour"},
                    {"key": "period_end", "type": "date", "date": period_end.isoformat()},
                ],
                extra_tags=[("content", "template_code", "payslip-2026")],
            )
            conn.execute(
                "INSERT INTO document_relations VALUES (?,?,?,?)",
                (ps, contract_id, "payslip_for_contract", None),
            )
            add_entities = True
            conn.executemany(
                """INSERT INTO extracted_entities(document_id,entity_type,raw_value,normalized_value,confidence,page,role_in_document)
                   VALUES (?,?,?,?,?,?,?)""",
                [
                    (ps, "person", p[3], p[1], 0.99, 1, "employee"),
                    (ps, "amount", f"{net} {cur}", str(net), 0.97, 1, "net_pay"),
                    (ps, "iban", iban, iban, 0.95, 1, "salary_account"),
                ],
            )

        # timesheets + maybe invoice
        for m in range(2):
            period_end = date(2026, 9, 30) - timedelta(days=30 * m)
            hr = round(152 * fte, 1)
            ho = float(RNG.choice([0, 0, 4, 8]))
            bill = round((hr + ho) * (hourly or 35) * 1.15, 2)
            ts = insert_doc(
                dtype="timesheet",
                title=f"Timesheet {period_end.isoformat()} — {p[2]}",
                person=p,
                client_id=p[11],
                country=country,
                lang="en",
                issued=period_end + timedelta(days=1),
                received=period_end + timedelta(days=1),
                effective_from=period_end.replace(day=1),
                effective_to=period_end,
                status="active",
                workflow="approved",
                source="employee_portal",
                pages=None,
                text=f"Timesheet {p[3]} regular {hr}h overtime {ho}h billable {bill} {cur} project {client_by_id[p[11]][0] if p[11] else 'internal'}",
                payload={
                    "project_codes": [f"PRJ-{RNG.randint(1000,1999)}"],
                    "approver": p[15] and "line-manager" or "system",
                    "onsite_days": RNG.randint(8, 20),
                },
                labels=[
                    {"key": "hours_regular", "type": "float", "numeric": hr, "unit": "hour"},
                    {"key": "hours_overtime", "type": "float", "numeric": ho, "unit": "hour"},
                    {"key": "billable_amount", "type": "money", "numeric": bill, "currency": cur},
                    {"key": "period_end", "type": "date", "date": period_end.isoformat()},
                ],
                extra_tags=[],
            )
            if p[11] and p[11] != client_ids["meridian-internal"] and m == 0:
                excl = bill
                vat_rate = 0.21 if country != "GB" else 0.20
                vat = round(excl * vat_rate, 2)
                incl = round(excl + vat, 2)
                due = period_end + timedelta(days=30)
                paid = due - timedelta(days=RNG.randint(0, 10)) if RNG.random() < 0.7 else None
                inv_no = f"INV-2026-{p[1][-4:]}-{period_end.month:02d}"
                inv = insert_doc(
                    dtype="client_invoice",
                    title=f"Invoice {inv_no}",
                    person=p,
                    client_id=p[11],
                    country=country,
                    lang="en",
                    issued=period_end + timedelta(days=5),
                    received=period_end + timedelta(days=5),
                    effective_from=None,
                    effective_to=None,
                    status="active",
                    workflow="paid" if paid else "pending_approval",
                    source="finance_erp",
                    pages=2,
                    text=f"INVOICE {inv_no} to {client_by_id[p[11]][1]} excl {excl} VAT {vat} incl {incl} due {due} IBAN NL91ABNA0417164300",
                    payload={
                        "invoice_number": inv_no,
                        "po_number": f"PO-{RNG.randint(80000, 90000)}",
                        "vat_rate": vat_rate,
                        "line_items": [{"desc": f"Staffing {p[10]}", "amount": excl}],
                        "iban_beneficiary": "NL91ABNA0417164300",
                    },
                    labels=(
                        [
                            {"key": "amount_excl_vat", "type": "money", "numeric": excl, "currency": cur},
                            {"key": "vat_amount", "type": "money", "numeric": vat, "currency": cur},
                            {"key": "amount_incl_vat", "type": "money", "numeric": incl, "currency": cur},
                            {"key": "due_date", "type": "date", "date": due.isoformat()},
                        ]
                        + (
                            [{"key": "paid_on", "type": "date", "date": paid.isoformat()}]
                            if paid
                            else []
                        )
                    ),
                    extra_tags=[("party", "account_manager", client_by_id[p[11]][6])],
                )
                conn.execute(
                    "INSERT INTO document_relations VALUES (?,?,?,?)",
                    (inv, ts, "invoice_for_timesheet", None),
                )
                conn.executemany(
                    """INSERT INTO extracted_entities(document_id,entity_type,raw_value,normalized_value,confidence,page,role_in_document)
                       VALUES (?,?,?,?,?,?,?)""",
                    [
                        (inv, "org", client_by_id[p[11]][1], client_by_id[p[11]][0], 0.99, 1, "bill_to"),
                        (inv, "vat", str(vat_rate), str(vat_rate), 0.9, 1, "vat_rate"),
                        (inv, "iban", "NL91ABNA0417164300", "NL91ABNA0417164300", 0.99, 1, "beneficiary"),
                    ],
                )

        if RNG.random() < 0.45:
            claimed = money(40, 680, 5)
            approved = claimed if RNG.random() < 0.85 else round(claimed * 0.8, 2)
            trip_s = daterange(ISO("2026-03-01"), ISO("2026-09-01"))
            insert_doc(
                dtype="expense_report",
                title=f"Expenses — {p[2]} {trip_s.isoformat()}",
                person=p,
                client_id=p[11],
                country=country,
                lang=lang,
                issued=trip_s + timedelta(days=7),
                received=trip_s + timedelta(days=8),
                effective_from=trip_s,
                effective_to=trip_s + timedelta(days=3),
                status="active",
                workflow="approved" if approved == claimed else "disputed",
                source="employee_portal",
                pages=3,
                text=f"Expense report {p[3]} travel {claimed} {cur} approved {approved}. Mileage {RNG.randint(20,400)} km. Receipt EXP-{RNG.randint(10000,99999)}",
                payload={
                    "lines": [
                        {"category": "rail", "amount": round(claimed * 0.6, 2), "receipt_ref": f"RCT-{RNG.randint(1000,9999)}"},
                        {"category": "meals", "amount": round(claimed * 0.4, 2), "receipt_ref": f"RCT-{RNG.randint(1000,9999)}"},
                    ],
                    "mileage_km": RNG.randint(20, 400),
                    "policy_exceptions": [] if approved == claimed else ["alcohol_excluded"],
                },
                labels=[
                    {"key": "claimed_amount", "type": "money", "numeric": claimed, "currency": cur},
                    {"key": "approved_amount", "type": "money", "numeric": approved, "currency": cur},
                    {"key": "trip_start", "type": "date", "date": trip_s.isoformat()},
                ],
                extra_tags=[],
            )

        if RNG.random() < 0.35:
            principal = money(1500, 12000, 100)
            term_m = RNG.choice([12, 24, 36])
            rate = RNG.choice([0.0, 1.5, 3.0, 4.2])
            outstanding = round(principal * RNG.uniform(0.2, 1.0), 2)
            first = hire + timedelta(days=90)
            loan_id = insert_doc(
                dtype="loan_document",
                title=f"Staff loan — {p[3]}",
                person=p,
                client_id=p[11],
                country=country,
                lang=lang,
                issued=first - timedelta(days=7),
                received=first - timedelta(days=6),
                effective_from=first,
                effective_to=first + timedelta(days=30 * term_m),
                status="active",
                workflow="executed",
                source="legal_esign",
                pages=7,
                text=(
                    f"EMPLOYEE LOAN {p[3]}\nPurpose: {RNG.choice(['bike_plan', 'relocation', 'education', 'hardship'])}\n"
                    f"Principal {principal} {cur}\nOutstanding {outstanding}\nRate {rate}% term {term_m}m\n"
                    f"Payroll deduction weekly. First due {first.isoformat()}."
                ),
                payload={
                    "loan_purpose": RNG.choice(["bike_plan", "relocation", "education", "hardship"]),
                    "amortization": "linear",
                    "security_interest": None,
                    "early_repay_fee_pct": 0.0,
                    "payroll_deduction": True,
                },
                labels=[
                    {"key": "principal_amount", "type": "money", "numeric": principal, "currency": cur},
                    {"key": "outstanding_balance", "type": "money", "numeric": outstanding, "currency": cur},
                    {"key": "interest_rate_pct", "type": "float", "numeric": rate, "unit": "percent"},
                    {"key": "term_months", "type": "integer", "numeric": term_m},
                    {"key": "first_due_date", "type": "date", "date": first.isoformat()},
                ],
                extra_tags=[("content", "template_code", "loan-staff-v4")],
            )
            # link a payslip if exists
            pays = by_person_type.get((p[0], "payslip"), [])
            if pays:
                conn.execute(
                    "INSERT OR IGNORE INTO document_relations VALUES (?,?,?,?)",
                    (pays[0], loan_id, "loan_referenced_on_payslip", "deduction line"),
                )

        insert_doc(
            dtype="benefits_enrollment",
            title=f"Pension/health enrollment — {p[2]}",
            person=p,
            client_id=p[11],
            country=country,
            lang=lang,
            issued=hire + timedelta(days=14),
            received=hire + timedelta(days=14),
            effective_from=hire,
            effective_to=None,
            status="active",
            workflow="executed",
            source="employee_portal",
            pages=2,
            text=f"Plan OmniPension-B. Employer 180 / employee 90 monthly. Tier family={RNG.choice(['employee','employee+partner','family'])}.",
            payload={
                "plan_name": "OmniPension-B",
                "coverage_tier": RNG.choice(["employee", "employee+partner", "family"]),
                "dependents_count": RNG.randint(0, 3),
            },
            labels=[
                {"key": "employer_monthly_contribution", "type": "money", "numeric": 180, "currency": cur},
                {"key": "employee_monthly_contribution", "type": "money", "numeric": 90, "currency": cur},
                {"key": "coverage_start", "type": "date", "date": hire.isoformat()},
            ],
            extra_tags=[],
        )
        ty = 2025
        taxable = round(salary * 0.96, 2)
        insert_doc(
            dtype="tax_form",
            title=f"Annual tax statement {ty} — {p[2]}",
            person=p,
            client_id=p[11],
            country=country,
            lang=lang,
            issued=date(2026, 2, 28),
            received=date(2026, 3, 1),
            effective_from=date(ty, 1, 1),
            effective_to=date(ty, 12, 31),
            status="active",
            workflow="archived",
            source="payroll_engine",
            pages=2,
            text=f"Jaaropgave/P60-equivalent {ty} {p[3]} taxable wage {taxable} {cur} withholding code {RNG.choice(['white','green','1'])}.",
            payload={"form_code": "jaaropgave" if country in {"NL", "BE"} else "p60_equiv", "withholding_code": "1", "filing_status": "standard"},
            labels=[
                {"key": "tax_year", "type": "integer", "numeric": ty},
                {"key": "taxable_wage", "type": "money", "numeric": taxable, "currency": cur},
            ],
            extra_tags=[],
        )
        score = round(RNG.uniform(2.4, 4.9), 1)
        insert_doc(
            dtype="performance_review",
            title=f"Review 2025 — {p[2]}",
            person=p,
            client_id=p[11],
            country=country,
            lang=lang,
            issued=date(2026, 1, 20),
            received=date(2026, 1, 21),
            effective_from=date(2025, 1, 1),
            effective_to=date(2025, 12, 31),
            status="active",
            workflow="approved",
            source="employee_portal",
            pages=5,
            text=f"Performance cycle 2025 {p[3]} overall {score}/5. Goals met {RNG.randint(60,100)}%. Band {RNG.choice(['developing','solid','exceeds'])}.",
            payload={
                "competencies": {"delivery": score, "collaboration": round(score - 0.2, 1)},
                "goals_met_pct": RNG.randint(60, 100),
                "calibration_band": RNG.choice(["developing", "solid", "exceeds"]),
                "next_review_month": "2027-01",
            },
            labels=[
                {"key": "overall_score", "type": "float", "numeric": score},
                {"key": "cycle_year", "type": "integer", "numeric": 2025},
            ],
            extra_tags=[],
        )
        if RNG.random() < 0.55:
            done = daterange(ISO("2024-01-01"), ISO("2026-08-01"))
            credits = RNG.choice([4, 8, 16, 24])
            valid = done.replace(year=done.year + 3)
            insert_doc(
                dtype="training_certificate",
                title=f"Certificate — {p[2]} VCA/GDPR",
                person=p,
                client_id=p[11],
                country=country,
                lang=lang,
                issued=done,
                received=done,
                effective_from=done,
                effective_to=valid,
                status="active",
                workflow="executed",
                source="email_ingest",
                pages=1,
                text=f"Course {RNG.choice(['VCA-VOL','GDPR-essentials','First-aid'])} credits {credits} completed {done} valid until {valid}. Provider LearnCo.",
                payload={
                    "provider": "LearnCo",
                    "course_code": RNG.choice(["VCA-VOL", "GDPR-ESS", "EHBO"]),
                    "delivery": RNG.choice(["classroom", "online"]),
                    "exam_passed": True,
                },
                labels=[
                    {"key": "credits", "type": "integer", "numeric": credits},
                    {"key": "valid_until", "type": "date", "date": valid.isoformat()},
                    {"key": "completed_on", "type": "date", "date": done.isoformat()},
                ],
                extra_tags=[("content", "template_code", "train-cert-v1")],
            )

    for p in [x for x in people if x[4] == "alumni"]:
        country = p[6]
        lang = "nl" if country in {"NL", "BE"} else "en"
        cur = currencies.get(country, "EUR")
        last = ISO(p[14]) if p[14] else ISO("2025-11-01")
        sev = money(0, 18000, 250)
        insert_doc(
            dtype="termination_letter",
            title=f"Termination — {p[3]}",
            person=p,
            client_id=p[11],
            country=country,
            lang=lang,
            issued=last - timedelta(days=30),
            received=last - timedelta(days=29),
            effective_from=last - timedelta(days=30),
            effective_to=last,
            status="archived",
            workflow="executed",
            source="legal_esign",
            pages=4,
            text=f"Notice to {p[3]}. Last working day {last.isoformat()}. Severance {sev} {cur}. Garden leave {RNG.choice([0,14,30])} days. Reason: {RNG.choice(['redundancy','end_of_assignment','resignation'])}.",
            payload={
                "reason_category": RNG.choice(["redundancy", "end_of_assignment", "resignation"]),
                "unused_holiday_payout": money(200, 2400, 50),
                "non_solicit_months": 6,
            },
            labels=[
                {"key": "last_working_day", "type": "date", "date": last.isoformat()},
                {"key": "severance_amount", "type": "money", "numeric": sev, "currency": cur},
                {"key": "garden_leave_days", "type": "duration_days", "numeric": RNG.choice([0, 14, 30]), "unit": "day"},
            ],
            extra_tags=[],
        )

    for p in RNG.sample(active, k=min(6, len(active))):
        country = p[6]
        lang = "nl" if country in {"NL", "BE"} else "en"
        start = daterange(ISO("2026-01-10"), ISO("2026-08-01"))
        ret = start + timedelta(days=RNG.randint(14, 90))
        occ = RNG.choice([0, 50, 100])
        insert_doc(
            dtype="medical_leave",
            title=f"Leave file — {p[2]}",
            person=p,
            client_id=p[11],
            country=country,
            lang=lang,
            issued=start,
            received=start,
            effective_from=start,
            effective_to=ret,
            status="active",
            workflow="pending_approval",
            source="email_ingest",
            pages=3,
            text=f"Medical leave category sick_pay. Start {start} expected return {ret}. Occupational {occ}%. Fit note on file: yes. No diagnosis stored.",
            payload={"leave_category": "sick_pay", "sick_pay_scheme": "statutory+topup", "fit_note_on_file": True},
            labels=[
                {"key": "leave_start", "type": "date", "date": start.isoformat()},
                {"key": "expected_return", "type": "date", "date": ret.isoformat()},
                {"key": "occupational_pct", "type": "integer", "numeric": occ, "unit": "percent"},
            ],
            extra_tags=[],
        )

    # fill remaining entity rows for contracts
    for (pid, dtype), docs in list(by_person_type.items()):
        if dtype != "employment_contract":
            continue
        p = next(x for x in people if x[0] == pid)
        for did in docs:
            conn.executemany(
                """INSERT INTO extracted_entities(document_id,entity_type,raw_value,normalized_value,confidence,page,role_in_document)
                   VALUES (?,?,?,?,?,?,?)""",
                [
                    (did, "person", p[3], p[1], 0.99, 1, "employee"),
                    (did, "org", "Meridian HR Collective", "meridian", 0.99, 1, "employer"),
                    (did, "job_title", p[10], p[10], 0.9, 1, "role"),
                    (did, "date", p[13] or "", p[13] or "", 0.95, 1, "start_date"),
                ],
            )

    conn.commit()
    n_docs = conn.execute("SELECT count(*) FROM documents").fetchone()[0]
    n_tags = conn.execute("SELECT count(*) FROM document_tags").fetchone()[0]
    n_lab = conn.execute("SELECT count(*) FROM sorting_labels").fetchone()[0]
    n_ent = conn.execute("SELECT count(*) FROM extracted_entities").fetchone()[0]
    conn.close()
    print(f"Wrote {DB_PATH}")
    print(f"documents={n_docs} tags={n_tags} sorting_labels={n_lab} entities={n_ent}")


if __name__ == "__main__":
    main()
