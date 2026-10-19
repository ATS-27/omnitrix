"""Omnitrix Streamlit interface."""

from datetime import date
import hashlib
import tempfile

import pandas as pd
import streamlit as st

from opportunityos import db
from opportunityos.agents.tracker import TrackerAgent
from opportunityos.config import DB_PATH, DEMO_TODAY, SAMPLE_JD, SAMPLE_RESUME, STATUSES, WEIGHTS
from opportunityos.data import load_listings
from opportunityos.orchestrator import run_workflow
from opportunityos.resume import clarify, export, gap, jd as jdmod, parser, tailor, truth
from opportunityos.ui_components import apply_theme, chip, icon_svg, metric_card, render_action, render_opportunity, safe_text


st.set_page_config(page_title="Omnitrix", layout="wide", initial_sidebar_state="auto")
apply_theme()


@st.cache_data(show_spinner=False)
def get_listings():
    """Load the bundled listing file once per file version."""
    return load_listings()


@st.cache_data(show_spinner=False)
def get_sample(path):
    with open(path, encoding="utf-8") as source:
        return source.read()


@st.cache_data(show_spinner=False)
def extract_resume(name, content):
    return parser.extract_text(name, content)


@st.cache_data(show_spinner=False)
def analyze_resume(resume_text, job_description):
    resume = parser.parse_resume(resume_text)
    job = jdmod.analyze_jd(job_description)
    gaps = gap.analyze_gaps(resume, job)
    return resume, job, gaps


@st.cache_data(show_spinner=False)
def export_resume_bytes(resume):
    """Build a draft in a temporary directory and return its bytes."""
    with tempfile.TemporaryDirectory(prefix="omnitrix_resume_") as temp_dir:
        path = f"{temp_dir}/tailored_resume.docx"
        export.export_docx(resume, path)
        with open(path, "rb") as document:
            return document.read()


def profile_defaults():
    return {
        "skills": "Python, SQL, PyTorch, NLP, Machine Learning, OWASP, Burp Suite, Git",
        "roles": "AI, NLP, Security, Data",
        "locations": ["Pune", "Remote"],
        "modes": ["Hybrid", "Remote"],
        "types": ["Internship"],
    }


def init_state():
    state = st.session_state
    defaults = profile_defaults()
    state.setdefault(
        "profile",
        {
            "skills": [s.strip() for s in defaults["skills"].split(",")],
            "preferred_roles": [s.strip() for s in defaults["roles"].split(",")],
            "preferred_locations": defaults["locations"],
            "preferred_modes": defaults["modes"],
            "preferred_types": defaults["types"],
        },
    )
    state.setdefault("workflow_result", None)
    state.setdefault("resume_analysis", None)
    state.setdefault("active_page", "dashboard")


def parse_csv_list(value):
    return [part.strip() for part in value.split(",") if part.strip()]


def render_setup_sidebar(records):
    locations = sorted({row["location"] for row in records})
    modes = sorted({row["work_mode"] for row in records})
    types = sorted({row["opportunity_type"] for row in records})
    current = st.session_state.profile

    with st.sidebar:
        st.markdown("<div class='brand-mark'>O</div><div class='brand-name'>Omnitrix</div>", unsafe_allow_html=True)
        st.caption("CAREER WORKSPACE")
        st.markdown("<div class='side-label'>WORKSPACE</div>", unsafe_allow_html=True)
        pages = {
            "Dashboard": ("dashboard", ":material/dashboard:"),
            "Find opportunities": ("search", ":material/search:"),
            "My applications": ("applications", ":material/work:"),
            "Deadlines & follow-ups": ("deadlines", ":material/event:"),
            "Resume tailor": ("resume", ":material/description:"),
            "Agent workflow": ("workflow", ":material/account_tree:"),
        }
        for label, (page, icon) in pages.items():
            if st.button(label, key=f"nav_{page}", icon=icon, type="primary" if st.session_state.get("active_page", "dashboard") == page else "secondary", width="stretch"):
                st.session_state.active_page = page
                st.rerun()
        st.markdown("<div class='side-label setup-label'>PROFILE & SETTINGS</div>", unsafe_allow_html=True)
        st.caption("Your profile shapes role matching and resume review.")
        with st.expander("Edit student profile", expanded=False):
            with st.form("profile_form", border=False):
                skills_text = st.text_area("Skills", ", ".join(current["skills"]), key="profile_skills_input",
                                           help="Separate skills with commas.")
                roles_text = st.text_input("Preferred roles", ", ".join(current["preferred_roles"]), key="profile_roles_input")
                selected_locations = st.multiselect(
                    "Preferred locations", locations, default=[x for x in current["preferred_locations"] if x in locations],
                    key="profile_locations_input",
                )
                selected_modes = st.multiselect(
                    "Preferred work modes", modes, default=[x for x in current["preferred_modes"] if x in modes],
                    key="profile_modes_input",
                )
                selected_types = st.multiselect(
                    "Opportunity types", types, default=[x for x in current["preferred_types"] if x in types],
                    key="profile_types_input",
                )
                submitted = st.form_submit_button("Save profile", type="primary", width="stretch")
            if submitted:
                st.session_state.profile = {
                    "skills": parse_csv_list(skills_text),
                    "preferred_roles": parse_csv_list(roles_text),
                    "preferred_locations": selected_locations,
                    "preferred_modes": selected_modes,
                    "preferred_types": selected_types,
                }
                st.toast("Profile saved for this session.")

        st.divider()
        use_real_date = st.toggle("Use today's date", value=False, key="use_real_date",
                                  help="Turn this off for repeatable demo dates.")
        as_of = date.today() if use_real_date else DEMO_TODAY
        st.caption(f"Workflow date: **{as_of.isoformat()}**")
        with st.expander("Scoring weights"):
            st.json(WEIGHTS)
        with st.expander("Demo tracker tools"):
            seed_col, clear_col = st.columns(2)
            if seed_col.button("Seed examples", width="stretch", help="Add three synthetic applications to the local tracker."):
                tracker = TrackerAgent(DB_PATH)
                tracker.save({"job_id": "SYN-002", "company": "Finverse", "role_title": "Data Science Intern",
                              "platform": "Workday", "source_url": "", "deadline": "2026-10-18"}, "Preparing")
                tracker.save({"job_id": "SYN-013", "company": "EduSpark", "role_title": "NLP Engineer Intern",
                              "platform": "LinkedIn", "source_url": "", "deadline": "2026-11-20"}, "Applied")
                tracker.update("SYN-013", date_applied="2026-10-01", follow_up_date="2026-10-10")
                tracker.save({"job_id": "SYN-003", "company": "CyberShield", "role_title": "Security Analyst Intern",
                              "platform": "LinkedIn", "source_url": "", "deadline": "2026-10-30"}, "Applied")
                tracker.update("SYN-003", date_applied="2026-10-06")
                st.rerun()
            if clear_col.button("Clear tracker", width="stretch", help="Remove all application rows from the local demo tracker."):
                for application in db.list_applications(DB_PATH):
                    db.delete_application(application["job_id"], DB_PATH)
                st.rerun()
    return as_of


@st.fragment
def render_dashboard(records, profile, as_of):
    applications = db.list_applications(DB_PATH)
    summary = run_workflow("what applications need follow-up?", profile, records, as_of=as_of, db_path=DB_PATH)
    counts = {status: sum(row["status"] == status for row in applications) for status in STATUSES}
    kpis = [
        ("Tracked roles", len(applications), "briefcase-business", "Roles saved to your local application tracker."),
        ("Applied", counts["Applied"], "send", "Applications marked Applied in your tracker."),
        ("Interviews", counts["Interview"], "calendar-days", "Applications currently marked Interview."),
        ("Suggested actions", len(summary.actions), "list-checks", "Suggestions based only on dates you recorded."),
    ]
    with st.container(key="dashboard-kpi"):
        cols = st.columns(4, gap="small")
        for col, (label, value, glyph, help_text) in zip(cols, kpis):
            with col:
                metric_card(label, value, glyph, help_text)

    with st.container(key="dashboard-overview-row"):
        pipeline_col, priority_col = st.columns([1.2, 1], gap="medium")
        with pipeline_col:
            st.markdown("<div class='section-heading'><h2>Application overview</h2><span>From your tracker</span></div>", unsafe_allow_html=True)
            if applications:
                with st.container(border=True):
                    active_statuses = [(status, counts[status]) for status in STATUSES if counts[status]]
                    for index, (status, count) in enumerate(active_statuses):
                        row_cols = st.columns([2, 5, .45], vertical_alignment="center")
                        row_cols[0].markdown(f"<span class='status-dot status-{status.lower()}'></span>{safe_text(status)}", unsafe_allow_html=True)
                        row_cols[1].progress(count / max(len(applications), 1), text="")
                        row_cols[2].markdown(f"<span class='status-count'>{count}</span>", unsafe_allow_html=True)
                        if index < len(active_statuses) - 1:
                            st.markdown("<div class='row-separator'></div>", unsafe_allow_html=True)
            else:
                with st.container(border=True):
                    st.markdown(
                        f"<div class='empty-state'><div class='empty-icon'>{icon_svg('briefcase-business', 24)}</div>"
                        "<div><h3>Your tracker is ready</h3><p>Save a role to keep its status, deadline, and next step together.</p></div></div>",
                        unsafe_allow_html=True,
                    )
                    if st.button("Find opportunities", type="primary", icon=":material/search:", key="dashboard_empty_find"):
                        st.session_state.active_page = "search"
                        st.rerun()
        with priority_col:
            st.markdown("<div class='section-heading'><h2>Priority actions</h2><span>Based on recorded dates</span></div>", unsafe_allow_html=True)
            if summary.actions:
                with st.container(border=True):
                    for index, action in enumerate(summary.actions[:3]):
                        render_action(action)
                        if index < min(len(summary.actions), 3) - 1:
                            st.markdown("<div class='row-separator'></div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div class='status-panel'>{icon_svg('circle-check', 20)}<div><strong>Nothing needs attention</strong>"
                    "<p>No follow-ups or deadlines are due for the selected workflow date.</p></div></div>",
                    unsafe_allow_html=True,
                )
            st.caption("Suggestions reflect your records and are not employer updates.")

    st.markdown("<div class='section-heading section-spaced'><h2>Recent applications</h2><span>Your latest tracker updates</span></div>", unsafe_allow_html=True)
    if applications:
        recent = sorted(applications, key=lambda row: row.get("updated_at") or "", reverse=True)[:4]
        with st.container(key="dashboard-recent-grid"):
            recent_cols = st.columns(min(4, len(recent)), gap="small")
            for col, application in zip(recent_cols, recent):
                with col:
                    with st.container(border=True):
                        st.markdown(f"<div class='recent-role'>{safe_text(application.get('role_title'))}</div><div class='recent-company'>{safe_text(application.get('company'))}</div>", unsafe_allow_html=True)
                        st.markdown(f"{chip(application.get('status', 'Unknown'), 'ok')}<span class='muted'>Updated {safe_text((application.get('updated_at') or '—')[:10])}</span>", unsafe_allow_html=True)
                        deadline = application.get("deadline") or "Not recorded"
                        st.caption(f"Deadline · {deadline}")
        if st.button("View all applications", key="dashboard_view_applications"):
            st.session_state.active_page = "applications"
            st.rerun()
    else:
        with st.container(border=True):
            st.markdown(
                f"<div class='empty-state'><div class='empty-icon'>{icon_svg('file-clock', 23)}</div>"
                "<div><h3>No recent applications yet</h3><p>Run a search and save an opportunity to start building your application history.</p></div></div>",
                unsafe_allow_html=True,
            )
            if st.button("Browse opportunities", type="primary", icon=":material/search:", key="dashboard_recent_find"):
                st.session_state.active_page = "search"
                st.rerun()

    st.markdown("<div class='section-heading section-spaced'><h2>Recommended opportunities</h2><span>Ranked for your profile</span></div>", unsafe_allow_html=True)
    st.caption("Synthetic demo listings · illustrative data only, not live or verified openings.")
    with st.spinner("Preparing profile matches…"):
        recommendations = recommend_opportunities(profile, records, as_of)
    tracked_ids = {row["job_id"] for row in applications}
    recommendations = [row for row in recommendations if row["job_id"] not in tracked_ids][:3]
    if recommendations:
        with st.container(key="dashboard-recommendation-grid"):
            rec_cols = st.columns(len(recommendations), gap="small")
            for col, record in zip(rec_cols, recommendations):
                with col:
                    with st.container(border=True):
                        st.markdown(f"{chip('SYNTHETIC DEMO', 'syn')}<div class='recent-role'>{safe_text(record['role_title'])}</div><div class='recent-company'>{safe_text(record['company'])}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='recommendation-score'>Profile match <strong>{int(record['score'])}/100</strong></div>", unsafe_allow_html=True)
                        st.caption(f"{record['location']} · {record['work_mode']} · deadline {record.get('deadline') or 'Not listed'}")
                        st.button("Open in search", key=f"dashboard_rec_{record['job_id']}", on_click=set_active_page, args=("search",))
    else:
        with st.container(border=True):
            st.markdown("<div class='compact-empty'>No untracked recommendations are available for this profile right now. Try a broader search.</div>", unsafe_allow_html=True)
            if st.button("Adjust search", key="dashboard_recommendations_search"):
                st.session_state.active_page = "search"
                st.rerun()


@st.cache_data(show_spinner=False)
def recommend_opportunities(profile, records, as_of):
    """Return Critic-validated profile matches from the bundled demo dataset."""
    return run_workflow("find suitable opportunities", profile, records, as_of=as_of, db_path=DB_PATH).results


def set_active_page(page):
    st.session_state.active_page = page


@st.fragment
def render_search(records, profile, as_of):
    st.caption("The Planner turns your request into a task. Discovery searches the local synthetic dataset, Matching explains fit, and the Critic checks the results.")
    with st.form("search_form", border=False):
        request = st.text_input("What are you looking for?", "Find suitable AI/NLP internships",
                                key="search_request", help="Examples: urgent internships closing soon, show deadlines this week")
        with st.expander("Filters", expanded=False):
            c1, c2, c3 = st.columns(3)
            types = sorted({row["opportunity_type"] for row in records})
            modes = sorted({row["work_mode"] for row in records})
            locations = sorted({row["location"] for row in records})
            selected_types = c1.multiselect("Opportunity type", types, key="search_types")
            selected_modes = c2.multiselect("Work mode", modes, key="search_modes")
            selected_locations = c3.multiselect("Location", locations, key="search_locations")
            f1, f2, f3 = st.columns(3)
            role_keyword = f1.text_input("Role title contains", key="search_role")
            days = f2.number_input("Closing within (days)", 0, 90, 0, help="0 means any deadline window.", key="search_days")
            required_skill = f3.text_input("Must require this skill", key="search_skill")
        submit = st.form_submit_button("Run workflow", type="primary", width="stretch")

    if submit:
        filters = {
            "types": selected_types,
            "modes": selected_modes,
            "locations": selected_locations,
            "max_days": days or None,
            "skill": required_skill.strip(),
            "role_keyword": role_keyword.strip(),
        }
        with st.spinner("Planning, searching, ranking, and validating opportunities…"):
            st.session_state.workflow_result = run_workflow(
                request, profile, records, as_of=as_of, db_path=DB_PATH, filters=filters
            )

    result = st.session_state.workflow_result
    if result is None:
        st.info("Your ranked shortlist and validation summary will appear here after you run the workflow.")
        return
    if result.message:
        (st.warning if result.no_match else st.info)(result.message)
    metrics = st.columns(4)
    metrics[0].metric("Retrieved", result.counts.get("retrieved", 0))
    metrics[1].metric("Validated", result.counts.get("validated", 0))
    metrics[2].metric("Excluded", result.counts.get("excluded", 0))
    metrics[3].metric("Suggested actions", result.counts.get("actions", 0))
    if not result.results:
        st.info("No opportunities passed validation for this request. Try widening your filters.")
    tracked_ids = {row["job_id"] for row in db.list_applications(DB_PATH)}
    for record in result.results:
        if render_opportunity(record, record["job_id"] in tracked_ids):
            TrackerAgent(DB_PATH, result.log).save(record)
            st.toast(f"Saved {record['role_title']} to your tracker.")
            st.rerun()
    if result.excluded:
        with st.expander(f"Critic exclusions ({len(result.excluded)})"):
            st.dataframe(pd.DataFrame(result.excluded), hide_index=True, width="stretch")


@st.fragment
def render_applications(as_of):
    applications = db.list_applications(DB_PATH)
    if not applications:
        st.info("No applications saved yet. Save a role from the search results to start your tracker.")
        return
    for application in applications:
        with st.container(border=True):
            st.markdown(f"### {safe_text(application['company'])} · {safe_text(application['role_title'])}")
            st.caption(f"{safe_text(application['platform'])} · deadline {application['deadline'] or 'unknown'} · last updated {application['updated_at'] or 'unknown'}")
            with st.form(f"application_form_{application['job_id']}"):
                c1, c2, c3 = st.columns([1.1, 1, 1])
                status = c1.selectbox("Status", STATUSES, index=STATUSES.index(application["status"]), key=f"status_{application['job_id']}")
                applied = c2.date_input("Date applied", value=date.fromisoformat(application["date_applied"]) if application["date_applied"] else None,
                                         key=f"applied_{application['job_id']}")
                follow_up = c3.date_input("Follow-up date", value=date.fromisoformat(application["follow_up_date"]) if application["follow_up_date"] else None,
                                          key=f"followup_{application['job_id']}")
                notes = st.text_area("Notes", application["notes"] or "", key=f"notes_{application['job_id']}")
                next_action = st.text_input("Next action", application["next_action"] or "", key=f"next_{application['job_id']}")
                save = st.form_submit_button("Save changes", type="primary", width="stretch")
            if save:
                if status == "Applied" and not applied:
                    applied = as_of
                TrackerAgent(DB_PATH).update(
                    application["job_id"], status=status, notes=notes, next_action=next_action,
                    date_applied=applied.isoformat() if applied else None,
                    follow_up_date=follow_up.isoformat() if follow_up else None,
                )
                st.toast("Application details saved.")
                st.rerun()
            if st.button("Remove from tracker", key=f"remove_{application['job_id']}"):
                db.delete_application(application["job_id"], DB_PATH)
                st.rerun()
            st.caption("Status and employer updates reflect what you recorded. Omnitrix does not verify applications with employers.")


@st.fragment
def render_deadlines(records, profile, as_of):
    st.caption("Suggestions come from recorded application dates and listing deadlines. No employer status is inferred.")
    with st.spinner("Checking recorded dates…"):
        result = run_workflow("show deadlines this week and follow-ups", profile, records, as_of=as_of,
                              db_path=DB_PATH, filters={"types": profile["preferred_types"] or None})
    if result.actions:
        actions = pd.DataFrame(result.actions)[["kind", "company", "role_title", "due", "message", "basis"]]
        actions.columns = ["Type", "Company", "Role", "Due", "Suggested next step", "Based on"]
        st.dataframe(actions, hide_index=True, width="stretch")
    else:
        st.success("Nothing is due based on the dates currently recorded.")
    st.subheader("Listings closing soon")
    soon = [row for row in result.results if row.get("deadline")]
    if soon:
        listing_table = pd.DataFrame(soon)[["job_id", "company", "role_title", "platform", "deadline", "warnings"]]
        listing_table["warnings"] = listing_table["warnings"].apply(", ".join)
        st.dataframe(listing_table.sort_values("deadline"), hide_index=True, width="stretch")
    else:
        st.info("No validated listings are closing in the next seven days.")


@st.fragment
def render_resume():
    st.caption("Review a job description against your resume. Every factual addition needs your confirmation, and nothing is submitted automatically.")
    upload = st.file_uploader("Master resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"], key="resume_upload")
    use_sample = st.checkbox("Use the sample resume", value=upload is None, key="resume_use_sample")
    with st.form("resume_analysis_form", border=False):
        jd_text = st.text_area("Job description", get_sample(SAMPLE_JD), height=180, key="resume_jd_text")
        analyze = st.form_submit_button("Analyze resume and job description", type="primary", width="stretch")

    if analyze:
        try:
            if upload is not None and not use_sample:
                resume_text = extract_resume(upload.name, upload.getvalue())
            else:
                resume_text = get_sample(SAMPLE_RESUME)
            with st.spinner("Mapping job requirements to resume evidence…"):
                parsed_resume, job, gaps = analyze_resume(resume_text, jd_text)
            signature = hashlib.sha256((resume_text + "\0" + jd_text).encode("utf-8")).hexdigest()
            st.session_state.resume_analysis = (signature, parsed_resume, job, gaps)
        except Exception as error:
            st.error(f"Could not read this resume: {error}")
            return

    if st.session_state.resume_analysis is None:
        st.info("Choose a resume and analyze it to see the evidence map and reviewable changes.")
        return

    signature, resume, job, gaps = st.session_state.resume_analysis
    current_text = extract_resume(upload.name, upload.getvalue()) if upload is not None and not use_sample else get_sample(SAMPLE_RESUME)
    current_signature = hashlib.sha256((current_text + "\0" + jd_text).encode("utf-8")).hexdigest()
    if current_signature != signature:
        st.info("Your resume or job description has changed. Run the analysis again to refresh the evidence map.")
        return

    st.markdown("#### 1. Evidence map")
    if not job["explicit"]:
        st.warning("No explicit Required line was found. Skills detected in the job description are treated as required.")
    state_kind = {"Demonstrated": "ok", "Mentioned but unclear": "warn", "Not found in resume": "bad"}
    if gaps:
        for row in gaps:
            st.markdown(
                f"`{safe_text(row['requirement'])}` · {safe_text(row['kind'])} "
                f"{chip(row['status'], state_kind[row['status']])} <span class='muted'>{safe_text(row['note'])}</span>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No requirements were detected. Add explicit Required or Preferred lines to the job description.")

    st.markdown("#### 2. Clarify missing or unclear evidence")
    questions = clarify.build_questions(gaps)
    project_names = [item["name"] for item in resume["projects"] + resume["experience"]]
    confirmations = {}
    if not questions:
        st.success("Every detected requirement has evidence in the resume.")
    for question in questions:
        requirement = question["requirement"]
        with st.container(border=True):
            st.write(question["question"])
            has_skill = st.checkbox(f"I have used {requirement}", key=f"confirm_{requirement}")
            if has_skill and project_names:
                project = st.selectbox("Project or experience", project_names, key=f"project_{requirement}")
                detail = st.text_area("What did you personally do?", key=f"detail_{requirement}")
                confirmations[requirement] = {"has": True, "project": project, "what": detail}
                if not clarify.usable_confirmation(confirmations[requirement]):
                    st.caption("Add a project and a concrete description of at least 15 characters before this can be used.")
            elif has_skill:
                confirmations[requirement] = {"has": True, "project": "", "what": ""}
                st.info("Add a project or experience section to your resume before attaching this confirmation.")
            else:
                confirmations[requirement] = {"has": False}
                st.caption(clarify.learning_suggestion(requirement))

    changes, notes = tailor.propose_changes(resume, job, gaps, confirmations)
    st.markdown("#### 3. Review proposed changes")
    for note in notes:
        st.warning(note)
    decisions, edits = {}, {}
    if not changes:
        st.info("No changes are proposed for this resume and job description.")
    for change in changes:
        with st.container(border=True):
            item_label = f" · {safe_text(change['item'])}" if change["item"] else ""
            st.markdown(
                f"**{safe_text(change['type'].replace('_', ' '))}**"
                f"{item_label}  \n"
                f"<span class='muted'>{safe_text(change['reason'])} · evidence: {safe_text(change['evidence'])}</span>",
                unsafe_allow_html=True,
            )
            if change["original"]:
                st.text_area("Before", change["original"], disabled=True, key=f"before_{change['id']}")
            st.text_area("Proposed wording", change["proposed"], disabled=True, key=f"proposal_{change['id']}")
            choice = st.radio("Decision", ["Review", "Accept", "Edit", "Reject"], index=0, horizontal=True,
                              key=f"decision_{change['id']}_{hashlib.sha256(change['proposed'].encode()).hexdigest()[:8]}")
            decisions[change["id"]] = choice.lower()
            if choice == "Edit":
                edits[change["id"]] = st.text_area("Your edit", change["proposed"], key=f"edit_{change['id']}")

    tailored = tailor.apply_changes(resume, changes, decisions, edits)
    issues = truth.check_resume(resume, tailored, job, confirmations)
    st.markdown("#### 4. Truthfulness check and export")
    errors = [issue for issue in issues if issue["severity"] == "error"]
    if not issues:
        st.success("No unsupported claims, invented metrics, or changed facts were found.")
    for issue in issues:
        (st.error if issue["severity"] == "error" else st.warning)(f"{issue['check']}: {issue['detail']}")
    applied = {change["requirement"] for change in changes if change.get("requirement") and decisions.get(change["id"]) in ("accept", "edit")}
    rows = truth.build_gap_report(gaps, confirmations, applied)
    st.dataframe(pd.DataFrame(rows)[["requirement", "kind", "status", "final"]], hide_index=True, width="stretch")
    if errors:
        st.error("Export is blocked until the truthfulness errors are fixed.")
        return
    col_docx, col_report = st.columns(2)
    col_docx.download_button("Download tailored resume (DOCX)", export_resume_bytes(tailored), "tailored_resume.docx")
    col_report.download_button("Download gap report (Markdown)", export.gap_report_md(job, rows, changes, decisions, issues), "gap_report.md")
    st.caption("The master resume stays unchanged. Review the draft before using it.")


@st.fragment
def render_workflow():
    result = st.session_state.workflow_result
    if result is None:
        st.info("Run a search first to inspect the plan, agent hand-offs, and validation decisions.")
        return
    st.caption(f"Planner task: **{result.plan.task}** · Ordered steps: {' → '.join(result.plan.steps)}")
    st.caption(f"Inferred filters: {result.plan.inferred_filters or 'none'}")
    roles = {
        "Planner": "Routes the request and chooses the workflow.",
        "Discovery": "Filters the local synthetic listings.",
        "Matching": "Scores profile fit and explains each result.",
        "Follow-up": "Suggests actions from recorded dates.",
        "Critic": "Checks fields, dates, duplicates, sources, and explanations.",
        "UI": "Presents validated results and decisions.",
    }
    agents = list(dict.fromkeys(entry["agent"] for entry in result.log.entries))
    for start in range(0, len(agents), 3):
        cols = st.columns(3)
        for col, agent in zip(cols, agents[start:start + 3]):
            with col:
                st.markdown(f"**{safe_text(agent)}**")
                st.caption(roles.get(agent, "Records the workflow hand-off."))
    st.subheader("Workflow record")
    log_table = pd.DataFrame(result.log.entries).rename(columns={"agent": "Agent", "message": "Decision or result"})
    st.dataframe(log_table, hide_index=True, width="stretch")
    with st.expander("Plan details"):
        st.json({"task": result.plan.task, "ordered_steps": result.plan.steps,
                 "urgent": result.plan.urgent, "inferred_filters": result.plan.inferred_filters})
    summary = st.columns(4)
    summary[0].metric("Retrieved", result.counts.get("retrieved", 0))
    summary[1].metric("Scored", result.counts.get("scored", 0))
    summary[2].metric("Passed Critic", result.counts.get("validated", 0))
    summary[3].metric("Excluded", result.counts.get("excluded", 0))
    if result.warnings:
        st.subheader("Warnings")
        for warning in result.warnings:
            st.warning(warning)
    if result.excluded:
        with st.expander(f"Excluded records ({len(result.excluded)})"):
            st.dataframe(pd.DataFrame(result.excluded), hide_index=True, width="stretch")


def main():
    init_state()
    records = get_listings()
    profile = st.session_state.profile
    as_of = render_setup_sidebar(records)
    profile = st.session_state.profile
    page = st.session_state.get("active_page", "dashboard")
    titles = {
        "dashboard": ("Overview", "Your application pipeline and next steps at a glance."),
        "search": ("Find opportunities", "Search, rank, and validate roles against your profile."),
        "applications": ("My applications", "Keep your saved roles and application notes in one place."),
        "deadlines": ("Deadlines & follow-ups", "Review upcoming dates recorded in your tracker and listings."),
        "resume": ("Resume tailor", "Compare your resume with a role and review evidence-backed edits."),
        "workflow": ("Agent workflow", "Inspect how Omnitrix plans, searches, scores, and validates."),
    }
    title, subtitle = titles[page]
    header_left, header_right = st.columns([5, 1], vertical_alignment="center")
    with header_left:
        st.markdown(f"<div class='page-eyebrow'>OMNITRIX / WORKSPACE</div><h1 class='page-title'>{safe_text(title)}</h1><div class='page-subtitle'>{safe_text(subtitle)}</div>", unsafe_allow_html=True)
    if page == "dashboard":
        with header_right:
            if st.button("Find roles", type="primary", icon=":material/search:", width="stretch"):
                st.session_state.active_page = "search"
                st.rerun()
    st.markdown("<div class='page-rule'></div>", unsafe_allow_html=True)
    if page == "dashboard":
        render_dashboard(records, profile, as_of)
    elif page == "search":
        render_search(records, profile, as_of)
    elif page == "applications":
        render_applications(as_of)
    elif page == "deadlines":
        render_deadlines(records, profile, as_of)
    elif page == "resume":
        render_resume()
    elif page == "workflow":
        render_workflow()


main()
