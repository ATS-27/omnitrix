from datetime import date
from opportunityos import db
from opportunityos.agents.tracker import TrackerAgent
from opportunityos.config import DEMO_TODAY
from opportunityos.orchestrator import run_workflow

def run(text, records, profile, dbpath, **kw):
    return run_workflow(text, profile, records, as_of=DEMO_TODAY, db_path=dbpath, **kw)

def ids(res):
    return [r["job_id"] for r in res.results]

def test_exact_duplicate_is_excluded(records, profile, dbpath):
    res = run("Find internships", records, profile, dbpath)
    reasons = {e["job_id"]: e["reason"] for e in res.excluded}
    assert reasons["SYN-029"] == "duplicate of SYN-003"
    assert "SYN-029" not in ids(res) and "SYN-003" in ids(res)

def test_cross_platform_duplicate_grouped(records, profile, dbpath):
    res = run("Find internships", records, profile, dbpath)
    kept = next(r for r in res.results if r["job_id"] == "SYN-001")
    assert any("SYN-005" in x for x in kept["also_listed_on"])

def test_missing_deadline_is_flagged_not_invented(records, profile, dbpath):
    res = run("Find internships", records, profile, dbpath)
    r = next(r for r in res.results if r["job_id"] == "SYN-012")
    assert r["deadline"] == "" and "Deadline unknown" in r["warnings"]

def test_expired_listing_marked_and_ranked_last(records, profile, dbpath):
    res = run("Find internships", records, profile, dbpath, filters={"types": ["Internship", "Full-time"]})
    r = next(r for r in res.results if r["job_id"] == "SYN-019")
    assert "Expired - needs verification" in r["warnings"]
    flags = [x.get("expired", False) for x in res.results]
    assert flags == sorted(flags)  # all non-expired first

def test_invalid_date_and_closed_are_excluded(records, profile, dbpath):
    res = run("Find internships", records, profile, dbpath)
    reasons = {e["job_id"]: e["reason"] for e in res.excluded}
    assert "invalid date" in reasons["SYN-027"]
    assert "Closed" in reasons["SYN-021"]

def test_missing_url_not_implied_verified(records, profile, dbpath):
    res = run("Find internships", records, profile, dbpath)
    r = next(r for r in res.results if r["job_id"] == "SYN-015")
    assert "Source unavailable - not verified" in r["warnings"]

def test_all_results_labelled_synthetic(records, profile, dbpath):
    res = run("Find internships", records, profile, dbpath)
    assert res.results and all(r["label"] == "SYNTHETIC" for r in res.results)

def test_no_matching_skills_gives_low_score_message(records, dbpath):
    nobody = {"skills": ["cobol"], "preferred_roles": ["chef"], "preferred_locations": ["Atlantis"],
              "preferred_modes": ["Onsite-only"], "preferred_types": ["Apprenticeship"]}
    res = run("Find internships", records, nobody, dbpath)
    assert res.no_match and "No strong matches" in res.message
    assert max(r["score"] for r in res.results) < 25

def test_no_candidates_returns_no_match(records, profile, dbpath):
    res = run("Find internships", records, profile, dbpath, filters={"locations": ["Atlantis"]})
    assert res.no_match and res.results == [] and "widening" in res.message

def test_scores_in_range_and_explanations_checked(records, profile, dbpath):
    res = run("Find internships", records, profile, dbpath)
    assert all(0 <= r["score"] <= 100 and r["explanation"] for r in res.results)

def test_planner_routes_follow_up_only(records, profile, dbpath):
    res = run("what applications need follow-up?", records, profile, dbpath)
    assert res.plan.task == "followups" and res.counts["retrieved"] == 0

def test_urgent_request_limits_to_deadline_window(records, profile, dbpath):
    res = run("urgent internships closing soon", records, profile, dbpath)
    assert res.results
    for r in res.results:
        assert 0 <= (date.fromisoformat(r["deadline"]) - DEMO_TODAY).days <= 14

def test_log_counts_come_from_data(records, profile, dbpath):
    res = run("Find internships", records, profile, dbpath)
    text = "\n".join(res.log.lines())
    assert f"Retrieved {res.counts['retrieved']} of {len(records)}" in text

# ---- tracker + follow-up ----
JOB = {"job_id": "SYN-013", "company": "EduSpark", "role_title": "NLP Engineer Intern", "platform": "LinkedIn",
       "source_url": "", "deadline": "2026-11-20"}

def test_status_update_persists(dbpath):
    t = TrackerAgent(dbpath)
    assert t.save(JOB) is True
    t.update("SYN-013", status="Interview")
    assert db.get_application("SYN-013", dbpath)["status"] == "Interview"

def test_saving_twice_does_not_duplicate(dbpath):
    t = TrackerAgent(dbpath)
    t.save(JOB); assert t.save(JOB) is False
    assert len(db.list_applications(dbpath)) == 1

def test_bad_status_rejected(dbpath):
    TrackerAgent(dbpath).save(JOB)
    try:
        db.update_application("SYN-013", dbpath, status="Hired!")
        assert False
    except ValueError:
        pass

def test_past_follow_up_flagged_for_active_application(records, profile, dbpath):
    t = TrackerAgent(dbpath); t.save(JOB, "Applied")
    t.update("SYN-013", date_applied="2026-10-01", follow_up_date="2026-10-10")
    res = run("what applications need follow-up?", records, profile, dbpath)
    a = res.actions[0]
    assert a["kind"] == "Follow-up due" and a["suggested"] is True and a["basis"] == "recorded follow_up_date"

def test_terminal_status_has_no_follow_up(records, profile, dbpath):
    t = TrackerAgent(dbpath); t.save(JOB, "Applied")
    t.update("SYN-013", follow_up_date="2026-10-01", status="Rejected")
    assert run("what applications need follow-up?", records, profile, dbpath).actions == []

def test_saved_role_deadline_soon(records, profile, dbpath):
    TrackerAgent(dbpath).save({**JOB, "job_id": "SYN-002", "deadline": "2026-10-18"}, "Preparing")
    kinds = [a["kind"] for a in run("what applications need follow-up?", records, profile, dbpath).actions]
    assert "Deadline soon" in kinds
