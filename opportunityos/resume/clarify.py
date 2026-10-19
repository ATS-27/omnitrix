from .gap import DEMONSTRATED

# Candidate Clarification Agent: one focused question per unclear/absent requirement.
def build_questions(gaps):
    qs = []
    for g in gaps:
        if g["status"] == DEMONSTRATED:
            continue
        t = g["requirement"]
        qs.append({
            "requirement": t, "kind": g["kind"], "status": g["status"],
            "question": (f"Have you used {t} in a course, personal project, internship or deployment? "
                         f"If yes, name the project, say what you personally did, and your level."),
        })
    return qs

# A confirmation counts only when the user says yes AND gives a concrete description.
def usable_confirmation(ans):
    return bool(ans and ans.get("has") and len(str(ans.get("what", "")).strip()) >= 15 and str(ans.get("project", "")).strip())

# Honest, non-fabricating suggestion for requirements the user does not have
def learning_suggestion(req):
    return (f"Do not list {req}. Highlight adjacent experience you really have, or plan a small "
            f"project that uses {req} before applying.")
