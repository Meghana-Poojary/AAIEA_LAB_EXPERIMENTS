"""Decision rules for automated resolution, review and escalation."""
def route_query(classification, match_score, article_found):
    priority = classification["priority"]
    complexity = classification["complexity"]
    if priority == "P1":
        return "URGENT_HUMAN_ESCALATION"
    if complexity == "High":
        return "TECHNICAL_HUMAN_REVIEW"
    if not article_found:
        return "CREATE_TICKET_AND_ESCALATE"
    if match_score >= 70 and complexity == "Low":
        return "PROPOSE_AUTO_RESOLUTION"
    if match_score >= 40:
        return "HUMAN_REVIEW"
    return "REQUEST_INFORMATION_OR_ESCALATE"
