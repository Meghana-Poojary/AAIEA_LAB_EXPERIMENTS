from __future__ import annotations
import csv, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RULES_PATH = DATA_DIR / "rules.json"
AUDIT_PATH = DATA_DIR / "audit_log.jsonl"

def load_rules() -> dict:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))

def load_jobs(path: str | Path | None = None) -> dict[str, dict]:
    df = pd.read_csv(path or DATA_DIR / "job_requirements.csv").fillna("")
    jobs = {}
    for _, row in df.iterrows():
        jobs[str(row["job_id"])] = {
            "job_id": str(row["job_id"]),
            "job_title": str(row["job_title"]),
            "min_years_experience": float(row["min_years_experience"]),
            "min_education_level": str(row["min_education_level"]),
            "required_skills": json.loads(row["required_skills"]),
            "preferred_certifications": json.loads(row["preferred_certifications"]),
        }
    return jobs

def split_items(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return sorted({x.strip().casefold() for x in str(value).split(";") if x.strip()})

def validate_candidate(row: dict, jobs: dict[str, dict] | None = None) -> list[str]:
    jobs = jobs or load_jobs()
    rules = load_rules()
    errors = []
    for field in rules["required_fields"]:
        value = row.get(field)
        if value is None or (isinstance(value, str) and not value.strip()) or pd.isna(value):
            errors.append(f"Missing required field: {field}")
    if str(row.get("job_id", "")) not in jobs:
        errors.append(f"Unknown job_id: {row.get('job_id')}")
    try:
        years = float(row.get("years_experience"))
        if years < 0 or years > 60:
            errors.append("years_experience must be between 0 and 60")
    except (TypeError, ValueError):
        errors.append("years_experience must be numeric")
    email = str(row.get("email", "")).strip()
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        errors.append("email format appears invalid")
    if str(row.get("education_level", "")) not in rules["education_order"]:
        errors.append("education_level is not in the supported education scale")
    complete = str(row.get("application_complete", "")).strip().lower()
    if complete not in {"true", "false", "1", "0", "yes", "no"}:
        errors.append("application_complete must be true/false")
    auth = str(row.get("work_authorization", "")).strip().lower()
    if auth not in {"yes", "no", "not_provided"}:
        errors.append("work_authorization must be yes/no/not_provided")
    return errors

def score_candidate(row: dict, jobs: dict[str, dict] | None = None) -> dict:
    jobs = jobs or load_jobs()
    rules = load_rules()
    errors = validate_candidate(row, jobs)
    if errors:
        result = {"application_id": str(row.get("application_id", "")), "candidate_name": str(row.get("candidate_name", "")),
                  "job_id": str(row.get("job_id", "")), "score": None, "component_scores": {},
                  "explanation": errors, "validation_errors": errors, "recommended_stage": "NEEDS_REVIEW",
                  "decision_status": "PENDING_HUMAN_REVIEW"}
        return result
    job = jobs[str(row["job_id"])]
    weights = rules["weights"]
    candidate_skills = set(split_items(row.get("skills", "")))
    required = {s.casefold() for s in job["required_skills"]}
    skill_ratio = (len(required & candidate_skills) / len(required)) if required else 1.0
    skill_points = skill_ratio * weights["skills"]

    years = float(row["years_experience"])
    target = max(float(job["min_years_experience"]), 1.0)
    exp_points = min(years / target, 1.0) * weights["experience"]

    edu_order = rules["education_order"]
    edu_points = weights["education"] if edu_order.index(str(row["education_level"])) >= edu_order.index(job["min_education_level"]) else 0

    preferred = {c.casefold() for c in job["preferred_certifications"]}
    certs = set(split_items(row.get("certifications", "")))
    cert_points = (len(preferred & certs) / len(preferred) * weights["certifications"]) if preferred else weights["certifications"]

    score = round(skill_points + exp_points + edu_points + cert_points, 2)
    complete = str(row.get("application_complete", "")).strip().lower() in {"true", "1", "yes"}
    auth = str(row.get("work_authorization", "")).strip().lower()
    explanations = [
        f"Required skills: {len(required & candidate_skills)}/{len(required)} matched ({skill_points:.1f}/{weights['skills']} points).",
        f"Experience: {years:g} years against target {target:g} ({exp_points:.1f}/{weights['experience']} points).",
        f"Education: {row['education_level']} compared with minimum {job['min_education_level']} ({edu_points}/{weights['education']} points).",
        f"Preferred certifications: {len(preferred & certs)}/{len(preferred)} matched ({cert_points:.1f}/{weights['certifications']} points)." if preferred else "No preferred certifications configured; full certification points awarded.",
    ]
    if not complete:
        stage = "NEEDS_REVIEW"
        explanations.append("Application is marked incomplete; human follow-up is required.")
    elif auth == "not_provided":
        stage = "NEEDS_REVIEW"
        explanations.append("Work authorization was not provided; ask for clarification rather than infer.")
    elif score >= rules["shortlist_threshold"]:
        stage = "SHORTLIST_RECOMMENDED"
    elif score < rules["review_threshold"]:
        stage = "NOT_QUALIFIED_RECOMMENDED"
    else:
        stage = "NEEDS_REVIEW"
    if auth == "no":
        stage = "NEEDS_REVIEW"
        explanations.append("Work authorization response requires human review against the role's lawful requirements.")
    return {
        "application_id": str(row["application_id"]), "candidate_name": str(row["candidate_name"]),
        "job_id": str(row["job_id"]), "job_title": job["job_title"], "score": score,
        "component_scores": {"skills": round(skill_points, 2), "experience": round(exp_points, 2),
                             "education": edu_points, "certifications": round(cert_points, 2)},
        "explanation": explanations, "validation_errors": [], "recommended_stage": stage,
        "decision_status": "PENDING_HUMAN_REVIEW"
    }

def draft_notification(result: dict, row: dict | None = None) -> dict:
    name = str(result.get("candidate_name") or "Candidate")
    stage = result.get("recommended_stage")
    job_title = result.get("job_title", "the role")
    if stage == "SHORTLIST_RECOMMENDED":
        subject = f"Update on your application for {job_title}"
        body = (f"Hello {name},\n\nThank you for applying for {job_title}. We would like to invite you "
                "to the next stage of our recruitment process. A recruiter will share the details after review.\n\n"
                "Regards,\nRecruitment Team")
        kind = "shortlist_draft"
    elif stage == "NOT_QUALIFIED_RECOMMENDED":
        subject = f"Update on your application for {job_title}"
        body = (f"Hello {name},\n\nThank you for your interest in {job_title} and for taking the time to apply. "
                "Following a review of the role-related criteria, we are not recommending progression at this stage. "
                "This draft must be reviewed by the recruitment team before any communication is sent.\n\n"
                "Regards,\nRecruitment Team")
        kind = "rejection_draft"
    else:
        subject = f"Additional review of your application for {job_title}"
        body = (f"Hello {name},\n\nThank you for applying for {job_title}. Our recruitment team is reviewing "
                "your application and may contact you if clarification is needed.\n\nRegards,\nRecruitment Team")
        kind = "review_draft"
    return {"kind": kind, "subject": subject, "body": body, "sent": False}

def append_audit(action: str, application_id: str = "", actor: str = "system", details: dict | None = None) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), "action": action,
              "application_id": str(application_id), "actor": actor, "details": details or {},
              "policy_version": load_rules().get("policy_version", "unknown")}
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def review_decision(application_id: str, decision: str, reviewer: str, notes: str = "") -> None:
    if decision not in {"APPROVE_SHORTLIST", "APPROVE_REJECTION", "REQUEST_MORE_INFO", "HOLD"}:
        raise ValueError("Unsupported review decision")
    if not reviewer.strip():
        raise ValueError("Reviewer identity is required")
    append_audit("HUMAN_REVIEW_DECISION", application_id, reviewer,
                 {"decision": decision, "notes": notes[:1000]})

def load_candidates(path: str | Path | None = None) -> pd.DataFrame:
    return pd.read_csv(path or DATA_DIR / "candidate_applications.csv").fillna("")
