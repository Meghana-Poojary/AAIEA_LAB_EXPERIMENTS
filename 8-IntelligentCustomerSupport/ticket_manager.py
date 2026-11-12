"""SQLite-backed ticket creation, retrieval and lifecycle updates."""
import sqlite3, json
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from pathlib import Path

DB_PATH = "tickets.db"
ALLOWED_STATUSES = {
    "OPEN", "PENDING_APPROVAL", "APPROVED_FOR_RESPONSE", "IN_REVIEW",
    "ON_HOLD", "AWAITING_CUSTOMER", "ESCALATED", "RESOLVED", "CLOSED"
}

def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DB_PATH):
    with connect(db_path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY, query_id TEXT UNIQUE, customer_id TEXT,
            intent TEXT, complexity TEXT, priority TEXT, status TEXT,
            assigned_team TEXT, created_at TEXT, updated_at TEXT,
            first_response_due TEXT, resolution_due TEXT, resolution_summary TEXT,
            classification_json TEXT, match_score REAL, route TEXT
        )""")

def create_ticket(query, classification, config, match_score=0, route="", db_path=DB_PATH):
    now = datetime.now(timezone.utc)
    priority = classification["priority"]
    minutes = int(config.get("sla_minutes", {}).get(priority, 240))
    ticket = {
        "ticket_id": "TKT-" + uuid4().hex[:8].upper(),
        "query_id": query["query_id"], "customer_id": query["customer_id"],
        "intent": classification["intent"], "complexity": classification["complexity"],
        "priority": priority, "status": "OPEN", "assigned_team": None,
        "created_at": now.isoformat(), "updated_at": now.isoformat(),
        "first_response_due": (now + timedelta(minutes=minutes)).isoformat(),
        "resolution_due": (now + timedelta(minutes=minutes)).isoformat(),
        "resolution_summary": None, "classification_json": json.dumps(classification),
        "match_score": float(match_score), "route": route
    }
    init_db(db_path)
    with connect(db_path) as conn:
        conn.execute("""INSERT INTO tickets VALUES
        (:ticket_id,:query_id,:customer_id,:intent,:complexity,:priority,:status,
         :assigned_team,:created_at,:updated_at,:first_response_due,:resolution_due,
         :resolution_summary,:classification_json,:match_score,:route)""", ticket)
    return ticket

def update_ticket(ticket_id, status=None, assigned_team=None, resolution_summary=None, db_path=DB_PATH):
    if status and status not in ALLOWED_STATUSES:
        raise ValueError("Invalid ticket status")
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM tickets WHERE ticket_id=?", (ticket_id,)).fetchone()
        if not row:
            raise ValueError("Ticket not found")
        new_status = status or row["status"]
        conn.execute("""UPDATE tickets SET status=?, assigned_team=COALESCE(?,assigned_team),
            resolution_summary=COALESCE(?,resolution_summary), updated_at=? WHERE ticket_id=?""",
            (new_status, assigned_team, resolution_summary, datetime.now(timezone.utc).isoformat(), ticket_id))
    return get_ticket(ticket_id, db_path)

def get_ticket(ticket_id, db_path=DB_PATH):
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM tickets WHERE ticket_id=?", (ticket_id,)).fetchone()
        return dict(row) if row else None

def list_tickets(db_path=DB_PATH):
    init_db(db_path)
    with connect(db_path) as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM tickets ORDER BY created_at DESC")]
