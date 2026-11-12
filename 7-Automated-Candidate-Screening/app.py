import json
import pandas as pd
import streamlit as st
from screening import (DATA_DIR, load_candidates, load_jobs, score_candidate,
                       validate_candidate, draft_notification, append_audit, review_decision)

st.set_page_config(page_title="ACSRS | Candidate Review", page_icon="🧭", layout="wide")
st.title("🧭 ACSRS")
st.caption("Automated Candidate Screening and Review System · transparent recommendations with human approval")
st.warning("Demo only. Scores are decision-support signals, not hiring decisions. Every outcome requires human review; notification drafts are never sent automatically.")

with st.sidebar:
    st.header("Data source")
    upload = st.file_uploader("Upload candidate CSV", type=["csv"])
    st.caption("Expected columns are documented in README.md.")
    reviewer = st.text_input("Reviewer name / ID", value="")
    st.caption("Use a consistent reviewer identifier for the audit trail.")

try:
    df = pd.read_csv(upload).fillna("") if upload else load_candidates()
    jobs = load_jobs()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

st.subheader("Dataset overview")
c1, c2, c3 = st.columns(3)
c1.metric("Applications", len(df))
c2.metric("Roles", df["job_id"].nunique() if "job_id" in df else 0)
c3.metric("Policy version", json.load(open(DATA_DIR / "rules.json", encoding="utf-8"))["policy_version"])

if "application_id" in df:
    dupes = df[df["application_id"].duplicated(keep=False)]["application_id"].astype(str).unique().tolist()
    if dupes:
        st.error(f"Duplicate application IDs found: {', '.join(dupes)}. These require correction before reliable review.")
    else:
        st.success("No duplicate application IDs detected.")

st.subheader("Screen and validate")
if st.button("Run rule-based screening", type="primary"):
    results = []
    for _, r in df.iterrows():
        row = r.to_dict()
        errors = validate_candidate(row, jobs)
        result = score_candidate(row, jobs)
        result["validation_summary"] = "VALID" if not errors else "INVALID"
        result["validation_errors"] = errors
        result["notification_draft"] = draft_notification(result, row)
        results.append(result)
        append_audit("SCREENING_RUN", result.get("application_id", ""), "system",
                     {"recommended_stage": result["recommended_stage"], "score": result["score"],
                      "validation_summary": result["validation_summary"]})
    st.session_state["results"] = results
    st.session_state["source_df"] = df.to_dict(orient="records")

results = st.session_state.get("results", [])
if results:
    result_df = pd.DataFrame([{
        "application_id": r["application_id"], "candidate_name": r["candidate_name"],
        "job_id": r["job_id"], "score": r["score"], "validation": r.get("validation_summary", ""),
        "recommended_stage": r["recommended_stage"], "human_status": r["decision_status"]
    } for r in results])
    st.dataframe(result_df, use_container_width=True, hide_index=True)
    st.download_button("Download screening results CSV", result_df.to_csv(index=False), "acsrs_screening_results.csv", "text/csv")

    st.subheader("Human review queue")
    ids = [r["application_id"] for r in results]
    selected_id = st.selectbox("Select application", ids)
    result = next(r for r in results if r["application_id"] == selected_id)
    source_row = next((r for r in st.session_state["source_df"] if str(r.get("application_id", "")) == str(selected_id)), {})
    st.markdown(f"### {result['candidate_name']} · {result.get('job_title', result['job_id'])}")
    left, right = st.columns([1, 1])
    with left:
        st.metric("Rule-based score", "Needs review" if result["score"] is None else f"{result['score']}/100")
        st.write("**Recommendation:**", result["recommended_stage"])
        st.write("**Validation:**", result.get("validation_summary", ""))
        for line in result["explanation"]:
            st.write("•", line)
        if result.get("validation_errors"):
            st.error("Validation issues")
            for err in result["validation_errors"]:
                st.write("•", err)
    with right:
        st.markdown("**Notification draft — not sent**")
        st.write("Subject:", result["notification_draft"]["subject"])
        st.text_area("Draft body", result["notification_draft"]["body"], height=210, key=f"draft_{selected_id}")
        st.caption("Copy or edit the draft after human review. This app does not send email.")

    st.markdown("**Record human decision**")
    decision = st.selectbox("Decision", ["HOLD", "APPROVE_SHORTLIST", "APPROVE_REJECTION", "REQUEST_MORE_INFO"], key=f"decision_{selected_id}")
    notes = st.text_area("Review notes (avoid sensitive personal details)", key=f"notes_{selected_id}")
    if st.button("Save human decision", key=f"save_{selected_id}"):
        if not reviewer.strip():
            st.error("Enter a reviewer name / ID in the sidebar first.")
        else:
            review_decision(selected_id, decision, reviewer, notes)
            st.success("Human decision recorded in audit log.")
    st.subheader("Audit log")
    audit_path = DATA_DIR / "audit_log.jsonl"
    if audit_path.exists():
        records = []
        for line in audit_path.read_text(encoding="utf-8").splitlines()[-200:]:
            try: records.append(json.loads(line))
            except json.JSONDecodeError: pass
        if records:
            st.dataframe(pd.DataFrame(records).sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)
            st.download_button("Download audit log", audit_path.read_text(encoding="utf-8"), "acsrs_audit_log.jsonl")
    else:
        st.info("No audit events recorded yet.")
else:
    st.info("Click **Run rule-based screening** to validate applications and produce explainable recommendations.")

with st.expander("Scoring policy"):
    rules = json.loads((DATA_DIR / "rules.json").read_text(encoding="utf-8"))
    st.json(rules)
with st.expander("Available job requirements"):
    st.dataframe(pd.read_csv(DATA_DIR / "job_requirements.csv"), use_container_width=True, hide_index=True)

st.subheader("Evaluation")
st.write("Run `python evaluate.py` in the project terminal to compare recommendations with fictional demo labels. These labels are for software testing only and do not represent ground truth about candidate quality.")
