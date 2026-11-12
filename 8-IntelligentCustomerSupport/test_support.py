"""Automated tests for the core support workflow. Run: python -m unittest -v"""
import unittest, tempfile, os
from classifier import classify_query
from resolver import retrieve_article
from workflow_router import route_query
from ingestion import ingest_queries
from notifications import generate_notification, send_with_retry
from sla_monitor import check_sla
from datetime import datetime, timezone, timedelta

KB=[{"article_id":"KB1","keywords":["login","password"],"approved":True,"response":"Reset password."}]

class SupportTests(unittest.TestCase):
    def test_login_classification(self):
        self.assertEqual(classify_query("I cannot log in")["intent"],"Login / Access")
    def test_outage_is_p1(self):
        self.assertEqual(classify_query("application is down for all users")["priority"],"P1")
    def test_billing_classification(self):
        self.assertEqual(classify_query("where is my invoice")["intent"],"Billing")
    def test_feature_request(self):
        self.assertEqual(classify_query("please add dark mode")["priority"],"P4")
    def test_approved_kb_retrieval(self):
        article,score=retrieve_article("login problem",KB)
        self.assertEqual(article["article_id"],"KB1"); self.assertGreater(score,0)
    def test_unapproved_kb_ignored(self):
        article,score=retrieve_article("login problem",[dict(KB[0],approved=False)])
        self.assertIsNone(article); self.assertEqual(score,0)
    def test_p1_escalation_precedence(self):
        self.assertEqual(route_query({"priority":"P1","complexity":"Low"},100,True),"URGENT_HUMAN_ESCALATION")
    def test_empty_query_rejected(self):
        import csv
        with tempfile.NamedTemporaryFile("w",suffix=".csv",delete=False,newline="") as f:
            w=csv.DictWriter(f,fieldnames=["query_id","customer_id","query_text","created_at"]); w.writeheader()
            w.writerow({"query_id":"1","customer_id":"C1","query_text":"","created_at":"now"})
            name=f.name
        try:
            valid,rejected=ingest_queries(name); self.assertEqual(len(valid),0); self.assertTrue(rejected)
        finally: os.unlink(name)
    def test_notification_retry(self):
        n=generate_notification({"ticket_id":"TKT-TEST"},"CREATED")
        result=send_with_retry(n,fail_first=2,max_attempts=3)
        self.assertEqual(result["status"],"SENT"); self.assertEqual(result["attempts"],3)
    def test_sla_breach(self):
        due=(datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat()
        self.assertEqual(check_sla({"first_response_due":due}),"BREACHED")

if __name__=="__main__": unittest.main()
