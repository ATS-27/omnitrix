from dataclasses import dataclass, field

URGENT_DAYS = 14
WEEK_DAYS = 7

@dataclass
class Plan:
    task: str                      # find | deadlines | followups
    steps: list
    urgent: bool = False
    inferred_filters: dict = field(default_factory=dict)
    summary: str = ""

# Turns free text into an ordered task plan. Keyword routing keeps it deterministic and testable;
# an LLM could replace this function without changing the rest of the pipeline.
def plan_request(text, log):
    t = (text or "").lower()
    inferred = {}
    if "follow" in t or "applications need" in t:
        task, steps = "followups", ["follow-up", "critic"]
    elif "deadline" in t:
        task, steps = "deadlines", ["discovery", "follow-up", "critic"]
        inferred["max_days"] = WEEK_DAYS if "this week" in t else URGENT_DAYS
    else:
        task, steps = "find", ["discovery", "matching", "follow-up", "critic"]

    urgent = any(w in t for w in ("urgent", "closing soon", "soon", "this week"))
    if urgent and task == "find":
        inferred["max_days"] = WEEK_DAYS if "this week" in t else URGENT_DAYS

    # opportunity type hints from the wording
    if "internship" in t or "intern" in t:
        inferred["types"] = ["Internship"]
    elif "research" in t:
        inferred["types"] = ["Research"]
    elif "fresher" in t or "full-time" in t or "full time" in t:
        inferred["types"] = ["Full-time"]

    summary = " -> ".join(steps)
    log.add("Planner", f"Task '{task}' (urgent={urgent}). Plan: {summary}")
    return Plan(task=task, steps=steps, urgent=urgent, inferred_filters=inferred, summary=summary)
