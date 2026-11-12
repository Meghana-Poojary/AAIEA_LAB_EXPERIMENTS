"""Append-only CSV audit logger."""
import csv
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

FIELDS = ["event_id","timestamp","query_id","ticket_id","event_type",
          "intent","complexity","priority","knowledge_article_id",
          "match_score","route","reviewer_action","ticket_status",
          "notification_status","error_details"]

def log_event(query_id="", ticket_id="", event_type="", classification=None,
              article_id="", match_score="", route="", reviewer_action="",
              ticket_status="", notification_status="", error_details=""):
    path = Path("audit_log.csv")
    exists = path.exists()
    c = classification or {}
    row = {"event_id":"AUD-"+uuid4().hex[:10].upper(),
           "timestamp":datetime.now(timezone.utc).isoformat(),
           "query_id":query_id,"ticket_id":ticket_id,"event_type":event_type,
           "intent":c.get("intent",""),"complexity":c.get("complexity",""),
           "priority":c.get("priority",""),"knowledge_article_id":article_id,
           "match_score":match_score,"route":route,"reviewer_action":reviewer_action,
           "ticket_status":ticket_status,"notification_status":notification_status,
           "error_details":str(error_details)}
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not exists: writer.writeheader()
        writer.writerow(row)
    return row
