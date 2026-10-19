import os
from opportunityos.config import SAMPLE_JD, SAMPLE_RESUME
from opportunityos.resume import clarify, export, gap, jd as J, parser, tailor, truth

def load():
    r = parser.parse_resume(open(SAMPLE_RESUME).read())
    jd = J.analyze_jd(open(SAMPLE_JD).read())
    return r, jd, gap.analyze_gaps(r, jd)

def status(gaps):
    return {g["requirement"]: g["status"] for g in gaps}

def test_gap_statuses_match_plan_example():
    _, _, g = load()
    s = status(g)
    assert s["python"] == s["sql"] == "Demonstrated"
    assert s["docker"] == "Not found in resume"
    assert s["deployment"] == "Mentioned but unclear"   # only "deployed" wording
    assert s["git"] == "Mentioned but unclear"          # listed in skills only

def test_questions_only_for_gaps():
    _, _, g = load()
    assert {q["requirement"] for q in clarify.build_questions(g)} == {"docker", "deployment", "git"}

CONF = {"docker": {"has": True, "project": "SolveStack",
                   "what": "containerised the question-answering service with Docker and ran it via docker-compose"}}

def test_confirmed_fact_is_added_and_passes_critic():
    r, jd, g = load()
    ch, notes = tailor.propose_changes(r, jd, g, CONF)
    new = tailor.apply_changes(r, ch, {c["id"]: "accept" for c in ch})
    assert "Docker" in new["skills"]
    assert any("Docker" in b for p in new["projects"] for b in p["bullets"])
    assert truth.check_resume(r, new, jd, CONF) == []

def test_unconfirmed_docker_is_never_added():
    r, jd, g = load()
    ch, _ = tailor.propose_changes(r, jd, g, {"docker": {"has": False}})
    new = tailor.apply_changes(r, ch, {c["id"]: "accept" for c in ch})
    assert "docker" not in [s.lower() for s in new["skills"]]

def test_vague_confirmation_adds_nothing():
    r, jd, g = load()
    ch, notes = tailor.propose_changes(r, jd, g, {"docker": {"has": True, "project": "SolveStack", "what": "used it"}})
    assert not any(c["type"] == "add_bullet" for c in ch) and notes

def test_unknown_project_adds_nothing():
    r, jd, g = load()
    ch, notes = tailor.propose_changes(r, jd, g, {"docker": {"has": True, "project": "Imaginary", "what": "containerised something real here"}})
    assert not any(c["type"] == "add_bullet" for c in ch) and notes

def test_critic_catches_fabricated_rewrite():
    r, jd, g = load()
    ch, _ = tailor.propose_changes(r, jd, g, {}, rewriter=lambda b, t: b.rstrip(".") + ", using Docker and improving speed by 40%")
    new = tailor.apply_changes(r, ch, {c["id"]: "accept" for c in ch})
    checks = {i["check"] for i in truth.check_resume(r, new, jd, {})}
    assert {"unsupported claim", "invented metric"} <= checks

def test_critic_catches_injected_skill_and_changed_facts():
    r, jd, g = load()
    bad = parser.parse_resume(open(SAMPLE_RESUME).read())
    bad["skills"].append("Kubernetes"); bad["education"][0] = bad["education"][0].replace("2027", "2025")
    checks = {i["check"] for i in truth.check_resume(r, bad, jd, {})}
    assert {"unsupported skill", "changed fact"} <= checks

def test_rejected_changes_leave_resume_identical_and_master_untouched():
    r, jd, g = load()
    before = parser.parse_resume(open(SAMPLE_RESUME).read())
    ch, _ = tailor.propose_changes(r, jd, g, CONF)
    new = tailor.apply_changes(r, ch, {c["id"]: "reject" for c in ch})
    assert new["skills"] == r["skills"] and new["projects"] == r["projects"]
    assert r["skills"] == before["skills"]   # apply_changes works on a copy

def test_gap_report_never_hides_unmet():
    r, jd, g = load()
    rows = truth.build_gap_report(g, {}, set())
    finals = {x["requirement"]: x["final"] for x in rows}
    assert finals["docker"].startswith("UNMET") and len(rows) == len(g)

def test_docx_export_roundtrip(tmp_path):
    r, jd, g = load()
    p = str(tmp_path / "out.docx"); export.export_docx(r, p)
    text = parser.extract_text("out.docx", open(p, "rb").read())
    parsed = parser.parse_resume(text)
    assert [x["name"] for x in parsed["projects"]] == [x["name"] for x in r["projects"]]
    assert parsed["education"] == r["education"]
