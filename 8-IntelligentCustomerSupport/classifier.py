"""Rule-based classification of customer queries."""
def classify_query(query_text: str) -> dict:
    text = (query_text or "").lower()

    # Critical incidents must take precedence over all ordinary categories.
    if any(term in text for term in (
        "security incident", "data breach", "application is down",
        "all users", "service outage", "widespread outage"
    )):
        return {"intent": "Technical Error", "complexity": "High", "priority": "P1"}

    if any(term in text for term in (
        "still unresolved", "did not work", "not working", "keeps showing"
    )):
        return {"intent": "Unresolved Issue", "complexity": "High", "priority": "P2"}

    if any(term in text for term in ("invoice", "payment", "billing", "subscription")):
        return {"intent": "Billing", "complexity": "Medium", "priority": "P2"}

    if any(term in text for term in ("cannot log in", "can't log in", "account locked", "password", "login")):
        return {"intent": "Login / Access", "complexity": "Medium", "priority": "P2"}

    if any(term in text for term in ("dark mode", "feature request", "new feature", "add a new")):
        return {"intent": "Feature Request", "complexity": "Low", "priority": "P4"}

    if any(term in text for term in ("server error", "export", "application error", "unknown error")):
        return {"intent": "Technical Error", "complexity": "Medium", "priority": "P2"}

    return {"intent": "General Information", "complexity": "Low", "priority": "P3"}
