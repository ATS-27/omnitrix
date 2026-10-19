from datetime import timedelta
from ..config import DEADLINE_SOON_DAYS, FOLLOWUP_GAP_DAYS, NEXT_ACTION, TERMINAL_STATUSES
from ..dates import parse_date

def _action(priority, kind, app_or_rec, message, due, basis):
    # "suggested" is always True: nothing here is a verified employer update
    return {"priority": priority, "kind": kind, "job_id": app_or_rec["job_id"],
            "company": app_or_rec.get("company"), "role_title": app_or_rec.get("role_title"),
            "message": message, "due": due, "basis": basis, "suggested": True}

# Builds a prioritised action list from RECORDED dates only (deadlines, applied/follow-up dates).
def followups(apps, results, as_of, log, include_listings=True):
    actions = []
    tracked_ids = {a["job_id"] for a in apps}

    for a in apps:
        if a["status"] in TERMINAL_STATUSES:
            continue
        fu, fu_state = parse_date(a.get("follow_up_date"))
        dl, dl_state = parse_date(a.get("deadline"))
        applied, ap_state = parse_date(a.get("date_applied"))

        if a["status"] in ("Applied", "Assessment", "Interview"):
            if fu_state == "ok" and fu <= as_of:
                late = (as_of - fu).days
                actions.append(_action(late, "Follow-up due", a,
                    f"{NEXT_ACTION.get(a['status'], 'Follow up')} (follow-up date passed {late} day(s) ago)",
                    fu.isoformat(), "recorded follow_up_date"))
            elif fu_state == "missing" and ap_state == "ok" and (as_of - applied).days >= FOLLOWUP_GAP_DAYS:
                n = (as_of - applied).days
                actions.append(_action(n - FOLLOWUP_GAP_DAYS, "Consider following up", a,
                    f"Applied {n} days ago and no follow-up date is set; consider checking the portal",
                    (applied + timedelta(days=FOLLOWUP_GAP_DAYS)).isoformat(), "recorded date_applied"))
        elif a["status"] in ("Saved", "Preparing") and dl_state == "ok":
            left = (dl - as_of).days
            if left < 0:
                actions.append(_action(1000 + abs(left), "Deadline passed", a,
                    f"Deadline passed {abs(left)} day(s) ago; verify the listing is still open or withdraw",
                    dl.isoformat(), "listing deadline"))
            elif left <= DEADLINE_SOON_DAYS:
                actions.append(_action(500 - left, "Deadline soon", a,
                    f"{NEXT_ACTION[a['status']]} (deadline in {left} day(s))", dl.isoformat(), "listing deadline"))

    # untracked listings from the current search that close within the window
    if include_listings:
        for r in results:
            if r["job_id"] in tracked_ids:
                continue
            dl, st = parse_date(r.get("deadline"))
            if st == "ok" and 0 <= (dl - as_of).days <= DEADLINE_SOON_DAYS:
                left = (dl - as_of).days
                actions.append(_action(300 - left, "Listing closing soon", r,
                    f"Closes in {left} day(s); save it if you plan to apply", dl.isoformat(), "listing deadline"))

    actions.sort(key=lambda x: -x["priority"])
    log.add("Follow-up", f"Identified {len(actions)} suggested action(s) from recorded dates "
                         f"({len(apps)} tracked application(s) checked).")
    return actions
