"""Optional Streamlit dashboard: streamlit run streamlit_app.py"""
import streamlit as st
import pandas as pd
from app import run, load_config, process_query
from ingestion import ingest_queries
from resolver import load_knowledge_base
from ticket_manager import list_tickets, update_ticket
from sla_monitor import monitor_tickets

st.set_page_config(page_title="Intelligent Customer Support", page_icon="🎫", layout="wide")
st.title("🎫 Intelligent Customer Support System")
st.caption("SaaS query classification • approved knowledge retrieval • ticket escalation • SLA monitoring")

tab1, tab2, tab3, tab4 = st.tabs(["Process Queries","Ticket Dashboard","Human Review","SLA Monitor"])

with tab1:
    st.subheader("Ingest customer queries")
    uploaded = st.file_uploader("Upload CSV or JSON", type=["csv","json"])
    if st.button("Process sample dataset"):
        with st.spinner("Processing queries..."):
            results=run("customer_queries.csv")
        st.success(f"Processed {len(results)} valid queries. See the Ticket Dashboard.")
    if uploaded:
        temp_path="uploaded_queries."+uploaded.name.split(".")[-1]
        with open(temp_path,"wb") as f: f.write(uploaded.getbuffer())
        try:
            valid,rejected=ingest_queries(temp_path)
            st.write(f"Valid records: {len(valid)} | Rejected records: {len(rejected)}")
            st.dataframe(pd.DataFrame(valid), use_container_width=True)
            if rejected: st.warning("Some records were rejected."); st.json(rejected)
            if st.button("Run uploaded queries"):
                kb=load_knowledge_base(); cfg=load_config()
                results=[process_query(q,kb,cfg) for q in valid]
                st.success(f"Created {len(results)} ticket workflows.")
                st.dataframe(pd.DataFrame([{"query_id":r["query_id"],"intent":r["classification"]["intent"],
                    "priority":r["classification"]["priority"],"route":r["route"],
                    "ticket_id":r["ticket"]["ticket_id"]} for r in results]),use_container_width=True)
        except Exception as e: st.error(str(e))

with tab2:
    st.subheader("Ticket overview")
    tickets=list_tickets()
    if tickets:
        df=pd.DataFrame(tickets)
        c1,c2,c3=st.columns(3)
        c1.metric("Total tickets",len(df))
        c2.metric("Escalated",int((df.status=="ESCALATED").sum()))
        c3.metric("Pending approval",int((df.status=="PENDING_APPROVAL").sum()))
        st.dataframe(df[["ticket_id","query_id","intent","priority","status","assigned_team","created_at"]],use_container_width=True)
    else: st.info("No tickets yet. Process the sample dataset first.")

with tab3:
    st.subheader("Human agent review")
    tickets=list_tickets()
    pending=[t for t in tickets if t["status"] in ("PENDING_APPROVAL","ESCALATED","IN_REVIEW","ON_HOLD")]
    if pending:
        selected=st.selectbox("Select ticket",pending,format_func=lambda x:f'{x["ticket_id"]} | {x["priority"]} | {x["status"]}')
        st.json({k:selected[k] for k in ("ticket_id","query_id","intent","priority","status","resolution_summary","route")})
        action=st.selectbox("Review action",["APPROVE","EDIT","HOLD","REQUEST_INFORMATION","ESCALATE","RESOLVE"])
        edited=st.text_area("Response / resolution text",value=selected.get("resolution_summary") or "")
        reviewer=st.text_input("Reviewer ID",value="AGENT001")
        if st.button("Apply review action"):
            new_status={"APPROVE":"APPROVED_FOR_RESPONSE","EDIT":"IN_REVIEW","HOLD":"ON_HOLD",
                        "REQUEST_INFORMATION":"AWAITING_CUSTOMER","ESCALATE":"ESCALATED","RESOLVE":"RESOLVED"}[action]
            update_ticket(selected["ticket_id"],new_status,resolution_summary=edited)
            st.success(f"Ticket updated: {new_status}")
            st.rerun()
    else: st.info("No tickets currently awaiting review.")

with tab4:
    st.subheader("SLA monitoring")
    tickets=list_tickets()
    if tickets:
        sla=monitor_tickets(tickets,load_config().get("sla_at_risk_minutes",10))
        st.dataframe(pd.DataFrame(sla),use_container_width=True)
        if sla:
            breached=sum(x["sla_status"]=="BREACHED" for x in sla)
            at_risk=sum(x["sla_status"]=="AT_RISK" for x in sla)
            a,b=st.columns(2); a.metric("Breached",breached); b.metric("At risk",at_risk)
    else: st.info("No tickets available for SLA monitoring.")
