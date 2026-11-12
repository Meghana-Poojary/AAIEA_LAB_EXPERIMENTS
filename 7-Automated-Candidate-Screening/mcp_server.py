"""ACSRS MCP server. Tools are read-only except audit logging of screening actions."""
import json
from mcp.server.fastmcp import FastMCP
from screening import load_candidates, load_jobs, score_candidate, validate_candidate, append_audit, DATA_DIR, AUDIT_PATH

mcp = FastMCP("acsrs")

@mcp.tool()
def list_jobs() -> list[dict]:
    """List job IDs, titles, minimum experience/education, and role-related criteria."""
    return list(load_jobs().values())

@mcp.tool()
def validate_application(application: dict) -> dict:
    """Validate one structured candidate application; returns errors and valid flag."""
    errors = validate_candidate(application)
    append_audit("MCP_VALIDATE", str(application.get("application_id", "")), "mcp",
                 {"error_count": len(errors)})
    return {"valid": not errors, "errors": errors}

@mcp.tool()
def screen_application(application: dict) -> dict:
    """Score one application using published rules and return an explainable recommendation. Not a hiring decision."""
    result = score_candidate(application)
    append_audit("MCP_SCREEN", str(application.get("application_id", "")), "mcp",
                 {"recommended_stage": result["recommended_stage"], "score": result["score"]})
    return result

@mcp.tool()
def audit_summary(limit: int = 50) -> dict:
    """Return recent audit event metadata. Limit is clamped to 1..200; avoid sharing candidate data unnecessarily."""
    limit = max(1, min(int(limit), 200))
    if not AUDIT_PATH.exists():
        return {"count_returned": 0, "events": []}
    events = []
    for line in AUDIT_PATH.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            item = json.loads(line)
            events.append({k: item.get(k) for k in ("timestamp", "action", "application_id", "actor", "policy_version")})
        except json.JSONDecodeError:
            continue
    return {"count_returned": len(events), "events": events}

@mcp.resource("acsrs://policy/scoring")
def scoring_policy() -> str:
    """Published scoring policy JSON."""
    return (DATA_DIR / "rules.json").read_text(encoding="utf-8")

if __name__ == "__main__":
    mcp.run(transport="stdio")
