# Intelligent Customer Support System with Escalation

A modular Python implementation of the supplied SaaS customer-support case study.

## Features
- CSV/JSON query ingestion and validation
- Rule-based intent, complexity and priority classification
- Retrieval from approved JSON knowledge-base articles
- Heuristic knowledge match score (not a calibrated probability)
- Rule-based routing to proposed automation, review or escalation
- SQLite ticket persistence and lifecycle updates
- Human review actions
- Simulated notifications with retry handling
- SLA deadline monitoring
- CSV audit and notification logs
- Automated unit tests
- Optional Streamlit dashboard

## Requirements
- Python 3.10+
- Core implementation uses only the Python standard library.
- Dashboard: `pip install -r requirements.txt`

## Run from this folder
```bash
python app.py
```
Use a different CSV or JSON input:
```bash
python app.py --input customer_queries.csv
```
Run tests:
```bash
python -m unittest -v
```
Launch dashboard:
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Generated files
- `tickets.db`: SQLite ticket database
- `audit_log.csv`: workflow audit events
- `notification_log.csv`: simulated delivery attempts
- `rejected_queries.json`: rejected input records and reasons
- `output/processing_results.json`: per-query processing summary

## Important implementation notes
- The notification service simulates delivery; it does not send real email or SMS.
- The match score is a keyword overlap heuristic, not a probability of correctness.
- Human approval is represented in ticket state and dashboard actions. Production deployment
  requires authenticated agents, role-based authorization and approval enforcement before
  dispatching customer-facing messages.
- SLA values in `config.json` are sample laboratory targets, not contractual recommendations.
- Do not use real customer personal data in the sample files.

## Suggested screenshots for the lab report
1. Project folder structure in VS Code.
2. Terminal showing `python app.py` and processed/rejected counts.
3. Terminal showing `python -m unittest -v` test results.
4. Streamlit Process Queries tab with valid/rejected input counts.
5. Ticket Dashboard showing ticket IDs, intent, priority and status.
6. Human Review tab showing a selected ticket and review action.
7. SLA Monitor showing WITHIN_SLA / AT_RISK / BREACHED states.
8. `tickets.db` opened in a SQLite viewer showing stored tickets.
9. `audit_log.csv` showing classification/routing events.
10. `notification_log.csv` showing SENT/FAILED status and retry attempts.
