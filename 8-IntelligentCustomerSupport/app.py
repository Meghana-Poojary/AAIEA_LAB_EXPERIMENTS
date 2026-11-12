"""Command-line entry point for Intelligent Customer Support System."""
import json, argparse, csv
from pathlib import Path
from ingestion import ingest_queries, save_rejections
from classifier import classify_query
from resolver import load_knowledge_base, retrieve_article
from workflow_router import route_query
from ticket_manager import create_ticket, update_ticket, list_tickets, init_db
from notifications import generate_notification, send_with_retry
from audit_logger import log_event

def load_config(path="config.json"):
    with open(path, encoding="utf-8") as f: return json.load(f)

def process_query(query, knowledge_base, config):
    classification = classify_query(query["query_text"])
    article, score = retrieve_article(query["query_text"], knowledge_base)
    route = route_query(classification, score, article is not None)
    ticket = create_ticket(query, classification, config, score, route)

    if route == "PROPOSE_AUTO_RESOLUTION":
        ticket = update_ticket(ticket["ticket_id"], "PENDING_APPROVAL",
                               resolution_summary=article["response"])
        event = "CREATED"
    else:
        team = "Incident Response" if classification["priority"] == "P1" else (
            "Technical Support" if classification["intent"] in ("Technical Error","Unresolved Issue")
            else "Billing Support" if classification["intent"] == "Billing"
            else "Customer Support")
        ticket = update_ticket(ticket["ticket_id"], "ESCALATED", assigned_team=team,
                               resolution_summary=article["response"] if article else "No approved knowledge-base article found.")
        event = "ESCALATED"

    notification = generate_notification(ticket, event)
    delivery = send_with_retry(notification, max_attempts=int(config.get("retry_attempts",3)))
    log_event(query["query_id"], ticket["ticket_id"], "QUERY_PROCESSED",
              classification, article["article_id"] if article else "",
              score, route, ticket_status=ticket["status"],
              notification_status=delivery["status"])
    return {"query_id":query["query_id"],"classification":classification,
            "article_id":article["article_id"] if article else None,
            "match_score":score,"route":route,"ticket":ticket,
            "notification":delivery}

def run(input_path="customer_queries.csv"):
    config = load_config()
    kb = load_knowledge_base()
    valid, rejected = ingest_queries(input_path)
    save_rejections(rejected)
    init_db()
    results = []
    for query in valid:
        try: results.append(process_query(query,kb,config))
        except Exception as exc:
            log_event(query_id=query.get("query_id",""),event_type="PROCESSING_ERROR",error_details=exc)
    Path("output").mkdir(exist_ok=True)
    with open("output/processing_results.json","w",encoding="utf-8") as f:
        json.dump(results,f,indent=2)
    print(f"Processed: {len(results)} | Rejected: {len(rejected)}")
    print(f"Tickets stored in tickets.db; results: output/processing_results.json")
    for item in results:
        c=item["classification"]
        print(f'{item["query_id"]}: {c["intent"]} / {c["priority"]} -> {item["route"]} [{item["ticket"]["ticket_id"]}]')
    return results

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Intelligent Customer Support System")
    parser.add_argument("--input",default="customer_queries.csv",help="CSV or JSON query file")
    args=parser.parse_args()
    run(args.input)
