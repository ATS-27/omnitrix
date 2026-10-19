from urllib.parse import urlparse
from ..config import REQUIRED_FIELDS
from ..data import split_skills
from ..dates import parse_date

def _norm_text(s):
    return " ".join("".join(c if c.isalnum() else " " for c in str(s).lower()).split())

def _norm_url(u):
    u = str(u or "").strip().lower()
    if not u:
        return ""
    p = urlparse(u)
    host = p.netloc.removeprefix("www.")
    return f"{host}{p.path.rstrip('/')}"

def dup_keys(r):
    return {("role", _norm_text(r["company"]), _norm_text(r["role_title"])), ("url", _norm_url(r["source_url"]))} - {("url", "")}

# Re-derives the explanation facts and compares them with what the Matching Agent said.
def check_explanation(r, profile_skills):
    have = set(split_skills(",".join(profile_skills)))
    req = split_skills(r["required_skills"])
    problems = []
    if not (0 <= r["score"] <= 100):
        problems.append("score outside 0-100")
    if set(r["matched"]) != {s for s in req if s in have}:
        problems.append("matched skills do not agree with listing/profile")
    if set(r["missing"]) != {s for s in req if s not in have}:
        problems.append("missing skills do not agree with listing/profile")
    for s in r["matched"] + r["missing"]:
        if s not in r["explanation"]:
            problems.append(f"explanation omits '{s}'")
    return problems

# Validates, flags, groups or excludes records. Returns (validated, excluded, warnings).
def validate(results, profile, as_of, log):
    validated, excluded, warnings = [], [], []
    seen = {}  # dup key -> kept record

    def exclude(r, reason):
        excluded.append({"job_id": r["job_id"], "company": r.get("company"), "role_title": r.get("role_title"), "reason": reason})

    for r in results:  # results arrive sorted best-first, so the first copy of a duplicate is the best-scored
        r = dict(r)
        r["warnings"] = []

        missing = [f for f in REQUIRED_FIELDS if not str(r.get(f, "")).strip()]
        if missing:
            exclude(r, f"missing required field(s): {', '.join(missing)}")
            continue

        _, p_state = parse_date(r.get("posted_date"))
        d, d_state = parse_date(r.get("deadline"))
        if p_state == "invalid" or d_state == "invalid":
            exclude(r, "invalid date format (expected YYYY-MM-DD)")
            continue
        if str(r.get("listing_status", "")).strip().lower() == "closed":
            exclude(r, "listing is marked Closed")
            continue

        keys = dup_keys(r)
        hit = next((seen[k] for k in keys if k in seen), None)
        if hit is not None:
            exclude(r, f"duplicate of {hit['job_id']}")
            hit.setdefault("also_listed_on", []).append(f"{r['platform']} ({r['job_id']})")
            continue

        if d_state == "missing":
            r["warnings"].append("Deadline unknown")
        elif d < as_of:
            r["warnings"].append("Expired - needs verification")
            r["expired"] = True
        if str(r.get("listing_status", "")).strip().lower() in ("", "unknown"):
            r["warnings"].append("Listing status unclear")
        if not _norm_url(r.get("source_url")):
            r["warnings"].append("Source unavailable - not verified")
        if str(r.get("is_synthetic", "")).lower() == "true":
            r["label"] = "SYNTHETIC"
        else:
            r["label"] = "Imported (unverified)"
            r["warnings"].append("Not marked synthetic; verify before relying on it")

        problems = check_explanation(r, profile.get("skills", []))
        if problems:
            exclude(r, "explanation failed validation: " + "; ".join(problems))
            continue

        for k in keys:
            seen[k] = r
        validated.append(r)

    # expired listings sink below the rest so they never look like top picks
    validated.sort(key=lambda x: (x.get("expired", False), -x["score"], x["job_id"]))
    for r in validated:
        for wmsg in r["warnings"]:
            warnings.append(f"{r['job_id']}: {wmsg}")
    n_dup = sum(1 for e in excluded if e["reason"].startswith("duplicate"))
    n_unknown = sum(1 for r in validated if "Deadline unknown" in r["warnings"])
    n_exp = sum(1 for r in validated if r.get("expired"))
    log.add("Critic", f"Excluded {len(excluded)} ({n_dup} duplicate); flagged {n_unknown} missing deadline, {n_exp} expired; "
                      f"{len(validated)} records passed validation.")
    return validated, excluded, warnings

# Action list check: every suggestion must point at a recorded date and be labelled as a suggestion.
def validate_actions(actions, log):
    ok, dropped = [], 0
    for a in actions:
        if a.get("due") and a.get("basis") and a.get("suggested") is True:
            ok.append(a)
        else:
            dropped += 1
    if dropped:
        log.add("Critic", f"Dropped {dropped} action(s) lacking a recorded-date basis.")
    return ok
