import copy, re
from .clarify import usable_confirmation
from .jd import find_term

ACRONYMS = {"sql": "SQL", "nlp": "NLP", "aws": "AWS", "rag": "RAG", "llm": "LLM", "owasp": "OWASP", "git": "Git",
            "c++": "C++", "css": "CSS", "html": "HTML", "pytorch": "PyTorch", "fastapi": "FastAPI", "opencv": "OpenCV"}

def display_skill(t):
    return ACRONYMS.get(t.lower(), t.title())

def _sentence(s):
    s = s.strip()
    s = s[0].upper() + s[1:] if s else s
    return s if s.endswith((".", "!", "?")) else s + "."

def _find_project(resume, name):
    for sec in ("projects", "experience"):
        for item in resume[sec]:
            if item["name"].lower() == name.strip().lower() or name.strip().lower() in item["name"].lower():
                return sec, item
    return None, None

# Resume Tailoring Agent: only proposes changes it can source (original resume or user confirmation).
# `rewriter` is an optional hook (e.g. a local LLM); whatever it returns is still checked by the Truthfulness Critic.
def propose_changes(resume, jd, gaps, confirmations, rewriter=None):
    changes, notes, n = [], [], 0
    all_terms = jd["required"] + jd["preferred"]

    def add(**kw):
        nonlocal n
        n += 1
        changes.append({"id": f"c{n}", "decision": "pending", **kw})

    # 1. skills: relevant ones first (reordering only, nothing new)
    skills = resume["skills"]
    ordered = sorted(skills, key=lambda s: (not any(find_term(t, s) for t in all_terms)))
    if ordered != skills:
        add(type="reorder_skills", section="skills", item="", original=", ".join(skills), proposed=", ".join(ordered),
            reason="Move skills the job asks for to the front", evidence="original resume (Skills)", source="original resume")

    # 2. projects: most relevant first
    def relevance(item):
        text = item["name"] + " " + " ".join(item["bullets"])
        return sum(1 for t in all_terms if find_term(t, text))
    for sec in ("projects",):
        items = resume[sec]
        order = sorted(items, key=lambda i: -relevance(i))
        if [i["name"] for i in order] != [i["name"] for i in items]:
            add(type="reorder_projects", section=sec, item="", original=" > ".join(i["name"] for i in items),
                proposed=" > ".join(i["name"] for i in order), reason="Lead with the project most relevant to the job",
                evidence="original resume (Projects)", source="original resume")

    # 3. user-confirmed additions
    for req, ans in confirmations.items():
        if not ans or not ans.get("has"):
            continue
        if not usable_confirmation(ans):
            notes.append(f"{req}: confirmation needs a project name and a concrete description (15+ characters); nothing added.")
            continue
        sec, item = _find_project(resume, ans["project"])
        if item is None:
            notes.append(f"{req}: project '{ans['project']}' is not in your resume; nothing added.")
            continue
        bullet = _sentence(ans["what"])
        add(type="add_bullet", section=sec, item=item["name"], original="", proposed=bullet,
            reason=f"You confirmed hands-on {req}; adds a specific bullet", evidence="your confirmation", source="user confirmation",
            requirement=req)
        if not any(find_term(req, s) for s in skills):
            add(type="add_skill", section="skills", item="", original="", proposed=display_skill(req),
                reason=f"{req} is now backed by a confirmed bullet", evidence="your confirmation", source="user confirmation",
                requirement=req)

    # 4. optional rewriter hook: only for bullets that already demonstrate a requirement
    if rewriter:
        for sec in ("projects", "experience"):
            for item in resume[sec]:
                for b in item["bullets"]:
                    if any(find_term(t, b) for t in all_terms):
                        new = rewriter(b, all_terms)
                        if new and new.strip() != b:
                            add(type="rewrite_bullet", section=sec, item=item["name"], original=b, proposed=new.strip(),
                                reason="Clearer wording aligned to the job description", evidence="original bullet", source="rewriter")
    return changes, notes

# Applies only accepted/edited changes to a COPY; the master resume object is never mutated.
def apply_changes(resume, changes, decisions, edits=None):
    edits = edits or {}
    out = copy.deepcopy(resume)
    for c in changes:
        d = decisions.get(c["id"], "pending")
        if d not in ("accept", "edit"):
            continue
        text = edits.get(c["id"], c["proposed"]) if d == "edit" else c["proposed"]
        c["final"] = text
        if c["type"] == "reorder_skills":
            out["skills"] = [s.strip() for s in text.split(",") if s.strip()]
        elif c["type"] == "reorder_projects":
            names = [x.strip() for x in text.split(" > ")]
            by = {i["name"]: i for i in out["projects"]}
            if set(names) == set(by):
                out["projects"] = [by[n] for n in names]
        elif c["type"] == "add_skill":
            if text.lower() not in [s.lower() for s in out["skills"]]:
                out["skills"].append(text)
        elif c["type"] == "add_bullet":
            _, item = _find_project(out, c["item"])
            if item is not None:
                item["bullets"].append(text)
        elif c["type"] == "rewrite_bullet":
            _, item = _find_project(out, c["item"])
            if item is not None and c["original"] in item["bullets"]:
                item["bullets"][item["bullets"].index(c["original"])] = text
    return out
