"""CSV/JSON ingestion and validation."""
import csv, json
from pathlib import Path

REQUIRED_FIELDS = {"query_id","customer_id","query_text","created_at"}

def ingest_queries(file_path):
    path = Path(file_path)
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or not REQUIRED_FIELDS.issubset(set(reader.fieldnames)):
                raise ValueError("Missing required CSV columns")
            rows = list(reader)
    elif path.suffix.lower() == ".json":
        with path.open(encoding="utf-8") as f:
            rows = json.load(f)
        if not isinstance(rows, list): raise ValueError("JSON input must contain a list")
    else:
        raise ValueError("Only CSV and JSON files are supported")

    valid, rejected, seen = [], [], set()
    for raw in rows:
        row = {str(k): ("" if v is None else str(v)).strip() for k,v in raw.items()}
        errors = []
        if not all(row.get(field) for field in REQUIRED_FIELDS):
            errors.append("Missing required field")
        if not row.get("query_text","").strip():
            errors.append("Empty query")
        qid = row.get("query_id","")
        if qid in seen: errors.append("Duplicate query ID")
        else: seen.add(qid)
        if errors: rejected.append({"record":row,"errors":errors})
        else: valid.append(row)
    return valid, rejected

def save_rejections(rejected, path="rejected_queries.json"):
    with open(path,"w",encoding="utf-8") as f:
        json.dump(rejected,f,indent=2)
