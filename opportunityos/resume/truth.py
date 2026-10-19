import re
from .jd import VOCAB, find_term
from .clarify import usable_confirmation

def _terms_in(text, extra=()):
    return {t for t in list(VOCAB) + list(extra) if find_term(t, text)}

def _all_text(resume):
    parts = list(resume["header"]) + resume["education"] + resume["skills"] + resume["certifications"]
    for sec in ("projects", "experience"):
        for i in resume[sec]:
            parts.append(i["name"]); parts += i["bullets"]
    return "\n".join(parts)

# Critic / Truthfulness Agent: compares the tailored resume against the original + confirmed facts.
# Returns a list of {severity: error|warning, check, detail}. Any "error" blocks export.
def check_resume(original, tailored, jd, confirmations):
    issues = []
    jd_terms = jd["required"] + jd["preferred"]
    confirmed = {r: a for r, a in confirmations.items() if usable_confirmation(a)}
    confirmed_text = " ".join(f"{r} {a['project']} {a['what']}" for r, a in confirmed.items())
    orig_text = _all_text(original)
    allowed_text = orig_text + "\n" + confirmed_text
    allowed_terms = _terms_in(allowed_text, jd_terms)

    # 1. skills must come from the original resume or a usable confirmation
    orig_skills = {s.lower() for s in original["skills"]}
    for s in tailored["skills"]:
        if s.lower() not in orig_skills and not any(find_term(r, s) for r in confirmed):
            issues.append({"severity": "error", "check": "unsupported skill", "detail": f"'{s}' is not in the resume or a confirmed fact"})

    # 2. new or changed bullets
    orig_bullets = {b for sec in ("projects", "experience") for i in original[sec] for b in i["bullets"]}
    for sec in ("projects", "experience"):
        for item in tailored[sec]:
            for b in item["bullets"]:
                if b in orig_bullets:
                    continue
                new_terms = _terms_in(b, jd_terms) - allowed_terms
                if new_terms:
                    issues.append({"severity": "error", "check": "unsupported claim",
                                   "detail": f"bullet in {item['name']} mentions {sorted(new_terms)} without support: \"{b}\""})
                nums = set(re.findall(r"\d[\d,.]*%?", b)) - set(re.findall(r"\d[\d,.]*%?", allowed_text))
                if nums:
                    issues.append({"severity": "error", "check": "invented metric", "detail": f"number(s) {sorted(nums)} not in resume or confirmation: \"{b}\""})
                hits = [t for t in jd_terms if find_term(t, b)]
                if len(hits) > 4 or any(len(re.findall(re.escape(t), b, re.I)) >= 3 for t in jd_terms):
                    issues.append({"severity": "warning", "check": "keyword stuffing", "detail": f"bullet packs many job keywords: \"{b}\""})
                if b not in orig_bullets and not any(a["what"].strip().rstrip(".").lower() in b.lower() for a in confirmed.values()):
                    issues.append({"severity": "warning", "check": "reworded bullet", "detail": f"review wording against your original: \"{b}\""})

    # 3. facts that must not move: header, education, certifications, project names, years
    if tailored["header"] != original["header"]:
        issues.append({"severity": "error", "check": "changed fact", "detail": "header changed"})
    if tailored["education"] != original["education"]:
        issues.append({"severity": "error", "check": "changed fact", "detail": "education changed"})
    if tailored["certifications"] != original["certifications"]:
        issues.append({"severity": "error", "check": "changed fact", "detail": "certifications changed"})
    for sec in ("projects", "experience"):
        if {i["name"] for i in tailored[sec]} != {i["name"] for i in original[sec]}:
            issues.append({"severity": "error", "check": "changed fact", "detail": f"{sec} names changed"})
    years_new = set(re.findall(r"\b(?:19|20)\d{2}\b", _all_text(tailored))) - set(re.findall(r"\b(?:19|20)\d{2}\b", allowed_text))
    if years_new:
        issues.append({"severity": "error", "check": "changed fact", "detail": f"new year(s) {sorted(years_new)}"})
    return issues

# Final gap report: nothing unmet is hidden behind wording.
def build_gap_report(gaps, confirmations, applied_reqs):
    rows = []
    for g in gaps:
        r = g["requirement"]
        if g["status"] == "Demonstrated":
            final = "Demonstrated in original resume"
        elif r in applied_reqs:
            final = "Confirmed by you and added"
        elif confirmations.get(r, {}) and confirmations[r].get("has"):
            final = "Confirmed but not added (needs detail or was rejected)"
        else:
            final = "UNMET - not added to the resume"
        rows.append({**g, "final": final})
    return rows
