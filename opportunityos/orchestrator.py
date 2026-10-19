from dataclasses import dataclass, field
from .config import DEMO_TODAY, NO_MATCH_THRESHOLD, DB_PATH
from .log import WorkflowLog
from .agents.planner import plan_request
from .agents.discovery import discover
from .agents.matching import match
from .agents.followup import followups
from .agents.critic import validate, validate_actions
from . import db

@dataclass
class RunResult:
    plan: object = None
    results: list = field(default_factory=list)      # validated, ranked listings
    excluded: list = field(default_factory=list)     # excluded with reasons
    warnings: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    log: WorkflowLog = None
    counts: dict = field(default_factory=dict)
    message: str = ""
    no_match: bool = False

# Runs the plan step by step over shared state. Steps the Planner did not choose are skipped.
def run_workflow(request_text, profile, records, filters=None, as_of=DEMO_TODAY, db_path=DB_PATH, weights=None):
    log = WorkflowLog()
    plan = plan_request(request_text, log)
    # explicit UI filters override anything the Planner inferred from the wording
    merged = {**plan.inferred_filters, **{k: v for k, v in (filters or {}).items() if v not in (None, "", [])}}
    res = RunResult(plan=plan, log=log)
    candidates, scored = [], []

    if "discovery" in plan.steps:
        candidates = discover(records, merged, as_of, log)
        if not candidates:
            res.no_match = True
            res.message = "No listings matched. Try widening filters (type, location, work mode or deadline window)."
            log.add("Planner", "Decision: no candidates, returning a 'no match' result.")

    if "matching" in plan.steps and candidates:
        scored = match(candidates, profile, as_of, log, weights)
        if scored[0]["score"] < NO_MATCH_THRESHOLD:
            res.no_match = True
            res.message = (f"No strong matches: the best score is {scored[0]['score']}/100. "
                           "Add skills to your profile or relax preferences.")
            log.add("Planner", "Decision: best score below threshold, flagging 'no strong match'.")
    elif plan.task == "deadlines":
        # deadline view needs no scoring; give records neutral fields so the Critic can still validate them
        scored = [dict(r, score=0, matched=[], missing=[], explanation="") for r in candidates]

    apps = []
    try:
        apps = db.list_applications(db_path)
    except Exception as e:  # tracker problems must not hide search results
        log.add("Follow-up", f"Tracker unavailable: {e}")

    if "follow-up" in plan.steps:
        res.actions = followups(apps, scored, as_of, log, include_listings=plan.task != "followups")

    if "critic" in plan.steps:
        if plan.task == "deadlines":
            # deadline mode has no scores to explain; validate fields/dates/duplicates only
            res.results, res.excluded, res.warnings = _validate_light(scored, profile, as_of, log)
        else:
            res.results, res.excluded, res.warnings = validate(scored, profile, as_of, log)
        res.actions = validate_actions(res.actions, log)

    res.counts = {"retrieved": len(candidates), "scored": len(scored), "validated": len(res.results),
                  "excluded": len(res.excluded), "actions": len(res.actions)}
    log.add("UI", f"Displaying {len(res.results)} validated opportunities and {len(res.actions)} suggested action(s).")
    return res

def _validate_light(scored, profile, as_of, log):
    # reuse the full Critic but give it a skills-consistent view so the explanation check passes trivially
    from .agents.matching import score_listing, explain
    fixed = []
    for r in scored:
        s = score_listing(r, profile, as_of)
        rr = dict(r); rr.update(s); rr["explanation"] = explain(r, s)
        fixed.append(rr)
    fixed.sort(key=lambda x: (x["job_id"]))
    return validate(fixed, profile, as_of, log)
