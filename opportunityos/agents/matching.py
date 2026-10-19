from ..config import WEIGHTS
from ..data import split_skills
from ..dates import parse_date

def _words(s):
    return {w for w in str(s).lower().replace("/", " ").replace("-", " ").split() if w}

# Scores one listing against the profile. Every number comes from listing/profile fields only.
def score_listing(rec, profile, as_of, weights=None):
    w = weights or WEIGHTS
    req = split_skills(rec["required_skills"])
    have = set(split_skills(",".join(profile.get("skills", []))))
    matched = [s for s in req if s in have]
    missing = [s for s in req if s not in have]
    # no listed skills => no evidence of a skill match (flagged by the Critic, not assumed)
    skill_pts = w["skills"] * (len(matched) / len(req)) if req else 0.0

    # role preference: full credit if a preferred role phrase sits inside the title, half for shared words
    title = rec["role_title"].lower()
    role_pts, role_note = 0.0, "no preferred role matched"
    for pref in profile.get("preferred_roles", []):
        p = pref.lower().strip()
        if p and p in title:
            role_pts, role_note = float(w["role"]), f"title contains preferred role '{pref}'"
            break
        if p and _words(p) & _words(title):
            role_pts, role_note = w["role"] * 0.5, f"title shares words with preferred role '{pref}'"
    # location vs work mode share the 15 points
    half = w["location_mode"] / 2
    locs = [x.lower() for x in profile.get("preferred_locations", [])]
    loc_ok = rec["location"].lower() in locs or (rec["location"].lower() == "remote" and "remote" in
             [m.lower() for m in profile.get("preferred_modes", [])])
    mode_ok = rec["work_mode"].lower() in [m.lower() for m in profile.get("preferred_modes", [])]
    lm_pts = (half if loc_ok else 0) + (half if mode_ok else 0)

    type_ok = rec["opportunity_type"].lower() in [t.lower() for t in profile.get("preferred_types", [])]
    type_pts = w["opp_type"] if type_ok else 0.0

    d, state = parse_date(rec["deadline"])
    dl_pts, dl_note = 0.0, "deadline unknown"
    if state == "ok":
        days = (d - as_of).days
        if days < 0:
            dl_note = "deadline has passed"
        elif days < 7:
            dl_pts, dl_note = w["deadline"] * 0.6, f"closes in {days} day(s)"
        else:
            dl_pts, dl_note = float(w["deadline"]), f"closes in {days} days"
    elif state == "invalid":
        dl_note = "deadline format invalid"

    score = round(skill_pts + role_pts + lm_pts + type_pts + dl_pts)
    return {
        "score": max(0, min(100, score)),
        "matched": matched, "missing": missing,
        "breakdown": {"skills": round(skill_pts, 1), "role": round(role_pts, 1),
                      "location_mode": round(lm_pts, 1), "opp_type": round(type_pts, 1),
                      "deadline": round(dl_pts, 1)},
        "role_note": role_note, "deadline_note": dl_note,
        "loc_ok": loc_ok, "mode_ok": mode_ok, "type_ok": type_ok,
    }

# Builds the explanation text strictly from the scored fields, so the Critic can re-check it.
def explain(rec, s):
    parts = []
    if s["matched"]:
        parts.append(f"Matching skills: {', '.join(s['matched'])}.")
    else:
        parts.append("No listed skill overlaps with your profile.")
    if s["missing"]:
        parts.append(f"Missing skills: {', '.join(s['missing'])}.")
    parts.append(f"Role: {s['role_note']}.")
    parts.append(f"Work mode {'matches' if s['mode_ok'] else 'does not match'} your preference "
                 f"({rec['work_mode']}); location {'matches' if s['loc_ok'] else 'does not match'} ({rec['location']}).")
    parts.append(f"Type {'matches' if s['type_ok'] else 'does not match'} ({rec['opportunity_type']}).")
    parts.append(f"Deadline: {s['deadline_note']}.")
    return " ".join(parts)

def match(records, profile, as_of, log, weights=None):
    out = []
    for r in records:
        s = score_listing(r, profile, as_of, weights)
        rec = dict(r)
        rec.update(s)
        rec["explanation"] = explain(r, s)
        out.append(rec)
    out.sort(key=lambda x: (-x["score"], x["job_id"]))
    top = out[0]["score"] if out else 0
    log.add("Matching", f"Scored {len(out)} records against the profile (top score {top}).")
    return out
