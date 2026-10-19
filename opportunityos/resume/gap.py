from .parser import evidence_lines
from .jd import find_term

DEMONSTRATED, UNCLEAR, NOT_FOUND = "Demonstrated", "Mentioned but unclear", "Not found in resume"

# Related wording counts only as "unclear": it hints at the skill but does not prove it.
RELATED = {
    "deployment": ["deploy", "deployed", "deploying", "hosted", "hosting", "released"],
    "docker": ["container", "containerise", "containerize", "containerised", "containerized"],
    "nlp": ["natural language", "text classification", "tokenisation", "tokenization"],
    "machine learning": ["ml model", "classifier", "model training"],
    "sql": ["database", "queries"],
    "aws": ["cloud"],
    "git": ["version control", "github"],
}

# Gap Analysis Agent: maps each JD requirement to resume evidence. "Not found" is NOT "user lacks the skill".
def analyze_gaps(resume, jd):
    ev = evidence_lines(resume)
    skills_lower = [s.lower() for s in resume["skills"]]
    rows = []
    for kind, terms in (("required", jd["required"]), ("preferred", jd["preferred"])):
        for t in terms:
            hits = [(sec, item, text) for sec, item, text in ev if find_term(t, text)]
            in_skills = any(find_term(t, s) for s in skills_lower)
            related = [(sec, item, text) for sec, item, text in ev
                       if any(r in text.lower() for r in RELATED.get(t, []))]
            if hits:
                status, evidence = DEMONSTRATED, hits
                note = f"used in {hits[0][1] or hits[0][0]}"
            elif in_skills:
                status, evidence = UNCLEAR, []
                note = "listed under Skills but no project/experience bullet shows it"
            elif related:
                status, evidence = UNCLEAR, related
                note = f"only related wording found in {related[0][1] or related[0][0]}"
            else:
                status, evidence = NOT_FOUND, []
                note = "no evidence in the resume (ask before assuming the skill is absent)"
            rows.append({"requirement": t, "kind": kind, "status": status, "evidence": evidence, "note": note})
    return rows
