# ACSRS — Automated Candidate Screening and Review System

A local educational demo for **transparent, rule-based recruitment workflow support**. It validates structured application data, calculates explainable scores against job-specific criteria, recommends a workflow stage, drafts candidate messages, records an audit trail, supports human approval, and evaluates screening performance against a synthetic labelled dataset.

## Important design boundary
ACSRS is a decision-support prototype, not an autonomous hiring system. Scores and stages are recommendations only. A human reviewer must approve shortlist/rejection decisions. Do not use protected or sensitive attributes (age, sex, race, religion, disability, caste, marital status, photo, etc.) as screening features. The bundled data is fictional and should not be used to make real employment decisions. Before real deployment, obtain legal/privacy review, validate job-relatedness, conduct bias and accessibility audits, and give candidates an appropriate review/appeal path.

## Features
- CSV upload or bundled synthetic candidate dataset
- Data validation (required fields, numeric ranges, known job IDs, duplicate application IDs)
- Explainable rule-based scoring (required skills, experience, education, certifications)
- Workflow routing: `NEEDS_REVIEW`, `SHORTLIST_RECOMMENDED`, `NOT_QUALIFIED_RECOMMENDED`
- Draft-only shortlist / rejection notifications (never sent automatically)
- Human approval/rejection controls
- JSON Lines audit log with timestamps and action records
- Evaluation metrics against synthetic `label_for_demo_evaluation` labels
- MCP server exposing tools to validate data, screen a candidate, list jobs, and read audit summary

## Quick start (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```
Open the local URL shown by Streamlit.

## Run the MCP server
In a second terminal, activate the same virtual environment and run:
```powershell
python mcp_server.py
```
The server uses MCP stdio transport. Connect it to an MCP-compatible client using the command `python` and the absolute path to `mcp_server.py` (with the project virtual environment's Python executable). For example, configure the client with a command and args appropriate to your client:
```json
{
  "mcpServers": {
    "acsrs": {
      "command": "C:/path/to/acsrs_project/.venv/Scripts/python.exe",
      "args": ["C:/path/to/acsrs_project/mcp_server.py"]
    }
  }
}
```
Use forward slashes in JSON paths. Exact configuration depends on your MCP client.

## Files
- `app.py` — Streamlit dashboard and human review interface
- `screening.py` — validation, scoring, routing, message drafts, audit helpers
- `mcp_server.py` — MCP tools/resources
- `evaluate.py` — evaluation report
- `data/candidate_applications.csv` — fictional structured applications
- `data/job_requirements.csv` — job-specific criteria in JSON columns
- `data/evaluation_labels.csv` — fictional labels for demonstration only
- `data/rules.json` — scoring policy and thresholds
- `tests/test_screening.py` — unit tests

## Scoring policy
Weights are configurable in `data/rules.json`. The default score is a weighted sum:
- Required skills match: 40 points
- Experience: 25 points
- Education: 20 points
- Certifications: 15 points

Required skills score is the percentage of required skills present multiplied by 40. Experience score scales to the job's target years and caps at 25. Education uses the minimum required level. Certifications score is the fraction of listed preferred certifications matched, scaled to 15; if no preferred certifications exist, full points are awarded. Missing or invalid data routes to `NEEDS_REVIEW`, not automatic rejection. A valid score at or above the shortlist threshold becomes `SHORTLIST_RECOMMENDED`; below the review threshold becomes `NOT_QUALIFIED_RECOMMENDED`; all other scores become `NEEDS_REVIEW`. All are recommendations requiring a human decision.

## Data schema
Candidate CSV columns:
`application_id,candidate_name,email,job_id,skills,years_experience,education_level,certifications,work_authorization,application_complete,label_for_demo_evaluation`

`skills` and `certifications` are semicolon-separated strings. `label_for_demo_evaluation` is a synthetic binary label (`1` = demo-positive, `0` = demo-negative) used only by evaluation, not scoring.

Job CSV columns:
`job_id,job_title,min_years_experience,min_education_level,required_skills,preferred_certifications`
Skill and certification columns contain JSON arrays.

## Audit trail
Actions append to `data/audit_log.jsonl` (created on first action). Treat audit logs as sensitive operational records; don't put unnecessary candidate details in logs, and apply retention/access policies in real deployments.
