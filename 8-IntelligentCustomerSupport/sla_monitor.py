"""SLA deadline evaluation."""
from datetime import datetime, timezone, timedelta

def check_sla(ticket, at_risk_minutes=10, now=None):
    now = now or datetime.now(timezone.utc)
    due = datetime.fromisoformat(ticket["first_response_due"])
    if due.tzinfo is None: due = due.replace(tzinfo=timezone.utc)
    if now > due:
        return "BREACHED"
    if due - now <= timedelta(minutes=at_risk_minutes):
        return "AT_RISK"
    return "WITHIN_SLA"

def monitor_tickets(tickets, at_risk_minutes=10):
    return [{"ticket_id":t["ticket_id"], "priority":t["priority"],
             "sla_status":check_sla(t, at_risk_minutes), "due":t["first_response_due"]}
            for t in tickets if t["status"] not in ("RESOLVED","CLOSED")]
