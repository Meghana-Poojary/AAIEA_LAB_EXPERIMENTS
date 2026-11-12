"""Notification drafts, simulated delivery, retry handling and logging."""
import csv, time
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

LOG_PATH = Path("notification_log.csv")
FIELDS = ["notification_id","ticket_id","event","message","status","attempts","timestamp","error"]

def _log(row):
    exists = LOG_PATH.exists()
    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not exists: writer.writeheader()
        writer.writerow(row)

def generate_notification(ticket, event):
    tid = ticket["ticket_id"]
    templates = {
        "CREATED": f"Support ticket {tid} has been created.",
        "ESCALATED": f"Ticket {tid} requires specialist review.",
        "RESOLVED": f"Ticket {tid} has been marked as resolved.",
        "SLA_BREACH": f"Ticket {tid} has exceeded its SLA target.",
        "ASSIGNED": f"Ticket {tid} has been assigned to the support team."
    }
    return {"notification_id":"NTF-"+uuid4().hex[:8].upper(),
            "ticket_id":tid,"event":event,
            "message":templates.get(event, f"Ticket {tid} has been updated."),
            "status":"DRAFT","attempts":0}

def send_with_retry(notification, fail_first=0, max_attempts=3):
    """Simulates delivery. fail_first is useful for testing retry behaviour."""
    error = ""
    for attempt in range(1, max_attempts + 1):
        try:
            if attempt <= fail_first:
                raise RuntimeError("Simulated temporary delivery failure")
            result = {**notification, "status":"SENT", "attempts":attempt, "error":""}
            _log({**result, "timestamp":datetime.now(timezone.utc).isoformat()})
            return result
        except Exception as exc:
            error = str(exc)
            if attempt == max_attempts:
                result = {**notification, "status":"FAILED", "attempts":attempt, "error":error}
                _log({**result, "timestamp":datetime.now(timezone.utc).isoformat()})
                return result
            time.sleep(0.1 * (2 ** (attempt - 1)))
    return {**notification, "status":"FAILED", "attempts":max_attempts, "error":error}
