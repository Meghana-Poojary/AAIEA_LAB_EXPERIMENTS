"""Evaluation of a deterministic recommendation against synthetic demonstration labels."""
import json
import pandas as pd
from screening import DATA_DIR, load_candidates, score_candidate

def main():
    df = load_candidates()
    labels_path = DATA_DIR / "evaluation_labels.csv"
    labels = pd.read_csv(labels_path)
    merged = df.merge(labels, on="application_id", suffixes=("", "_label"), validate="one_to_one")
    rows = []
    for _, row in merged.iterrows():
        result = score_candidate(row.to_dict())
        rows.append({"application_id": row["application_id"], "score": result["score"],
                     "recommended_stage": result["recommended_stage"],
                     "predicted_positive": int(result["recommended_stage"] == "SHORTLIST_RECOMMENDED"),
                     "label": int(row["label_for_demo_evaluation"])})
    out = pd.DataFrame(rows)
    valid = out["score"].notna()
    y_true = out.loc[valid, "label"].astype(int)
    y_pred = out.loc[valid, "predicted_positive"].astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    metrics = {
        "warning": "Synthetic labels and synthetic candidates only; not a validation of real hiring quality or fairness.",
        "applications": int(len(out)), "valid_scored": int(valid.sum()),
        "accuracy": round((tp + tn) / max(tp + tn + fp + fn, 1), 3),
        "precision": round(tp / max(tp + fp, 1), 3),
        "recall": round(tp / max(tp + fn, 1), 3),
        "confusion_matrix": {"true_positive": tp, "true_negative": tn, "false_positive": fp, "false_negative": fn},
        "recommendation_counts": out["recommended_stage"].value_counts().to_dict()
    }
    print(json.dumps(metrics, indent=2))
    out.to_csv(DATA_DIR / "evaluation_results.csv", index=False)
    print(f"Detailed results written to {DATA_DIR / 'evaluation_results.csv'}")

if __name__ == "__main__":
    main()
