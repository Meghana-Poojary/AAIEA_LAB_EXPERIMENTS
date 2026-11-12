"""Human-in-the-loop ticket review actions."""
ALLOWED_ACTIONS = {"APPROVE","EDIT","HOLD","REQUEST_INFORMATION","ESCALATE","RESOLVE"}

def apply_review_action(ticket, action, reviewer_id, edited_response=None):
    if action not in ALLOWED_ACTIONS:
        raise ValueError("Invalid review action")
    ticket = dict(ticket)
    ticket["last_reviewer"] = reviewer_id
    ticket["review_action"] = action
    if action == "APPROVE":
        ticket["status"] = "APPROVED_FOR_RESPONSE"
    elif action == "EDIT":
        ticket["status"] = "IN_REVIEW"
        if edited_response: ticket["resolution_summary"] = edited_response
    elif action == "HOLD": ticket["status"] = "ON_HOLD"
    elif action == "REQUEST_INFORMATION": ticket["status"] = "AWAITING_CUSTOMER"
    elif action == "ESCALATE": ticket["status"] = "ESCALATED"
    elif action == "RESOLVE": ticket["status"] = "RESOLVED"
    return ticket
