"""Builds data/data.db with synthetic tables and the document set. Deterministic."""
from __future__ import annotations

import sqlite3
from pathlib import Path

EMPLOYEES = [
    (1, "Asha Rao", "Engineering", "Staff Engineer", 182000, "asha.rao@example.com", "APAC"),
    (2, "Liam Walsh", "Engineering", "Engineer", 126000, "liam.walsh@example.com", "EMEA"),
    (3, "Maria Chen", "Sales", "Account Executive", 118000, "maria.chen@example.com", "AMER"),
    (4, "Omar Haddad", "Sales", "Sales Director", 205000, "omar.haddad@example.com", "EMEA"),
    (5, "Priya Nair", "Support", "Support Lead", 98000, "priya.nair@example.com", "APAC"),
    (6, "Jonas Berg", "Support", "Support Agent", 71000, "jonas.berg@example.com", "EMEA"),
    (7, "Sofia Rossi", "HR", "HR Manager", 112000, "sofia.rossi@example.com", "EMEA"),
    (8, "Kenji Sato", "Engineering", "Engineering Manager", 195000, "kenji.sato@example.com", "APAC"),
    (9, "Dana Lee", "Finance", "Controller", 140000, "dana.lee@example.com", "AMER"),
    (10, "Tariq Aziz", "Sales", "Account Executive", 121000, "tariq.aziz@example.com", "APAC"),
]

DEALS = [
    (1, "Northwind", "EMEA", 120000, "Won", "Omar Haddad"),
    (2, "Contoso", "AMER", 450000, "Negotiation", "Maria Chen"),
    (3, "Fabrikam", "APAC", 80000, "Won", "Tariq Aziz"),
    (4, "Globex", "EMEA", 230000, "Proposal", "Omar Haddad"),
    (5, "Initech", "AMER", 60000, "Lost", "Maria Chen"),
    (6, "Umbrella", "APAC", 310000, "Negotiation", "Tariq Aziz"),
    (7, "Hooli", "AMER", 520000, "Won", "Maria Chen"),
    (8, "Stark Ltd", "EMEA", 95000, "Proposal", "Omar Haddad"),
    (9, "Wayne Corp", "APAC", 140000, "Won", "Tariq Aziz"),
    (10, "Acme", "EMEA", 70000, "Lost", "Omar Haddad"),
]

TICKETS = [
    (101, "ana.kovacs@clientmail.com", "Cannot export report to CSV", "open", "high", "Priya Nair", "Export button spins forever on reports over 10k rows."),
    (102, "brian.ortiz@clientmail.com", "Invoice shows wrong VAT", "open", "medium", "Jonas Berg", "VAT 21 percent applied to a zero-rated account."),
    (103, "chloe.martin@clientmail.com", "SSO login loop", "closed", "high", "Priya Nair", "Fixed by clearing stale SAML session; root cause was clock skew."),
    (104, "dmitri.ivanov@clientmail.com", "Need API rate limit increase", "open", "low", "Jonas Berg", "Requesting 5x quota for the nightly sync job."),
    (105, "elena.garcia@clientmail.com", "Dashboard tiles blank", "pending", "medium", "Priya Nair", "Browser extension blocked the chart script."),
]

# (doc_id, title, allowed_roles, text)
DOCS = [
    ("kb-sso", "SSO troubleshooting", ["analyst", "support", "hr_admin"],
     "If users loop on the SSO login page, check clock skew between the identity provider and the service. "
     "Clear stale SAML sessions and confirm the assertion consumer URL matches the configured value."),
    ("kb-export", "Large report exports", ["analyst", "support"],
     "CSV exports above ten thousand rows run as background jobs. The download link is emailed. "
     "If the export spinner never ends, ask the user to retry with a narrower date range."),
    ("kb-rate", "API rate limits", ["analyst", "support"],
     "Default API quota is 100 requests per minute per key. Increases need a business justification and "
     "are approved by the support lead. Nightly sync jobs should use the bulk endpoint instead."),
    ("hr-comp", "Compensation bands", ["hr_admin"],
     "Engineering bands: Engineer 110k to 140k, Staff 160k to 200k. Sales bands include a variable component. "
     "Band exceptions need approval from the HR manager and finance."),
    ("hr-leave", "Leave policy", ["hr_admin", "support", "analyst"],
     "Employees receive 25 days of paid leave per year. Unused days carry over up to five days. "
     "Parental leave is 16 weeks fully paid."),
    ("sales-playbook", "Enterprise sales playbook", ["analyst"],
     "Deals above 250k need a legal review before the proposal stage. Discounts above 15 percent need "
     "director approval. Track every negotiation in the pipeline tool."),
    ("sec-incident", "Security incident process", ["analyst", "support", "hr_admin"],
     "Report suspected incidents to the security channel within one hour. Do not forward customer data by "
     "email. The on-call engineer opens an incident record and assigns a commander."),
    ("fin-close", "Month-end close", ["analyst"],
     "Revenue is recognised when a deal reaches the Won stage and the contract is countersigned. "
     "Month-end close completes on the third business day."),
]


def build_data_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT, title TEXT,
                                salary INTEGER, email TEXT, region TEXT);
        CREATE TABLE deals (id INTEGER PRIMARY KEY, account TEXT, region TEXT, amount INTEGER,
                            stage TEXT, owner TEXT);
        CREATE TABLE tickets (id INTEGER PRIMARY KEY, customer TEXT, subject TEXT, status TEXT,
                              priority TEXT, assignee TEXT, body TEXT);
        """
    )
    con.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?,?)", EMPLOYEES)
    con.executemany("INSERT INTO deals VALUES (?,?,?,?,?,?)", DEALS)
    con.executemany("INSERT INTO tickets VALUES (?,?,?,?,?,?,?)", TICKETS)
    con.commit()
    con.close()
