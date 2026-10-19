"""Small, reusable presentation helpers for the Streamlit interface."""

import html

import pandas as pd
import streamlit as st


def safe_text(value):
    return html.escape(str(value or ""))


def chip(label, kind="syn"):
    return f'<span class="chip {kind}">{safe_text(label)}</span>'


ICON_PATHS = {
    "briefcase-business": '<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 12h18M10 12v2h4v-2"/>',
    "send": '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
    "calendar-days": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18M8 15h.01M12 15h.01M16 15h.01M8 18h.01M12 18h.01"/>',
    "list-checks": '<path d="m3 6 2 2 4-4M3 12l2 2 4-4M3 18l2 2 4-4M13 6h8M13 12h8M13 18h8"/>',
    "circle-check": '<circle cx="12" cy="12" r="10"/><path d="m8 12 2.5 2.5L16 9"/>',
    "file-clock": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h6"/><path d="M14 2v6h6M14 2l6 6M8 13h4M8 17h3"/><circle cx="18" cy="18" r="3"/><path d="M18 16.5V18l1 1"/>',
}


def icon_svg(name, size=18):
    """Small, inline Lucide-style stroke icon from a fixed allow-list."""
    paths = ICON_PATHS.get(name, ICON_PATHS["briefcase-business"])
    return (
        f'<svg class="line-icon" width="{int(size)}" height="{int(size)}" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{paths}</svg>'
    )


def metric_card(label, value, icon_name, help_text=""):
    title = f' title="{safe_text(help_text)}"' if help_text else ""
    st.markdown(
        f'<div class="kpi-card"{title}><div class="kpi-top"><span>{safe_text(label)}</span>'
        f'<span class="kpi-icon">{icon_svg(icon_name, 17)}</span></div>'
        f'<div class="kpi-value">{safe_text(value)}</div></div>',
        unsafe_allow_html=True,
    )


def apply_theme():
    st.markdown(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400..750&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <style>
        :root {
          --ink:#252735; --muted:#667085; --teal:#23877d; --coral:#f1806b;
          --mint:#f1f6f5; --line:#dfe6e8;
          --font-body:'Inter',Arial,Helvetica,sans-serif;
        }
        .block-container {max-width:1440px; padding:1rem 2rem 2.5rem;}
        html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
          font-family:var(--font-body); color:var(--ink); font-synthesis:weight;
        }
        [data-testid="stAppViewContainer"] p, [data-testid="stSidebar"] p,
        [data-testid="stAppViewContainer"] li {font-family:var(--font-body); font-size:15px; font-weight:400; line-height:1.6;}
        h1, h2, h3, h4, button, input, textarea, select, [role="combobox"], [role="tab"] {
          font-family:var(--font-body);
        }
        h1 {font-size:30px; font-weight:750; line-height:1.2; letter-spacing:-.025em; color:var(--ink);}
        h2 {font-size:22px; font-weight:700; line-height:1.3; letter-spacing:-.015em; color:var(--ink);}
        h3 {font-size:21px; font-weight:650; line-height:1.35; color:var(--ink);}
        h4 {font-size:16px; font-weight:600; line-height:1.4; color:var(--ink);}
        [data-testid="stAppViewContainer"] {background:var(--mint);}
        [data-testid="stHeader"] {background:#fff; border-bottom:1px solid var(--line); min-height:2.5rem;}
        [data-testid="stSidebar"] {background:#252735; border-right:0;}
        [data-testid="stSidebar"] > div:first-child {background:#252735;}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"], [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] .stCaption {color:#e7e9f0;}
        [data-testid="stSidebar"] [data-testid="stExpander"] {border-color:#414351; background:#2d2f3d;}
        [data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea,
        [data-testid="stSidebar"] [data-baseweb="select"] > div {background:#343644; color:#f3f4f7; border-color:#515361;}
        [data-testid="stSidebar"] [data-testid="stButton"] button {text-align:left; justify-content:flex-start; border:0; background:transparent; color:#c6c9d2; font-size:14px; font-weight:600;}
        [data-testid="stSidebar"] [data-testid="stButton"] button:hover {background:#343644; color:#fff; border:0;}
        [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {background:#23877d; color:#fff;}
        [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] p {color:#fff;}
        [data-testid="stIconMaterial"] {font-variation-settings:'FILL' 0,'wght' 350,'GRAD' 0,'opsz' 20;}
        .brand-mark {display:inline-flex; width:34px; height:34px; align-items:center; justify-content:center; border-radius:10px; background:#23877d; color:#fff; font-weight:700; font-size:19px; vertical-align:middle; margin-right:.6rem;}
        .brand-name {display:inline-block; vertical-align:middle; color:#fff; font-weight:700; font-size:16px;}
        .side-label {color:#b9bdc9; font-size:12px; font-weight:600; letter-spacing:.1em; margin:1.35rem 0 .45rem;}
        .setup-label {border-top:1px solid #414351; padding-top:1rem;}
        .page-eyebrow {font-size:12px; letter-spacing:.1em; color:var(--muted); font-weight:600; line-height:1.45;}
        h1.page-title {font-size:30px; font-weight:750; line-height:1.2; color:var(--ink); margin:.15rem 0 .1rem;}
        .page-subtitle {font-size:15px; font-weight:400; line-height:1.6; color:var(--muted);}
        .page-rule {height:1px; background:var(--line); margin:.8rem 0 1.05rem;}
        .kpi-card {background:#fff; border:1px solid var(--line); border-radius:11px; padding:.7rem .85rem; min-height:94px; box-shadow:0 1px 2px rgba(37,39,53,.025);}
        .kpi-top {display:flex; align-items:center; justify-content:space-between; gap:.4rem; color:#667085; font-size:13px; font-weight:600; line-height:1.45;}
        .kpi-icon {display:flex; align-items:center; justify-content:center; width:30px; height:30px; color:var(--teal); background:#e7f2f0; border-radius:8px;}
        .kpi-value {font-family:var(--font-body); color:var(--ink); font-size:32px; font-weight:750; line-height:1.15; font-variant-numeric:tabular-nums; margin-top:.35rem;}
        [data-testid="stMetric"] {background:#fff; border:1px solid var(--line); border-radius:12px; padding:.75rem 1rem; box-shadow:0 1px 2px rgba(37,39,53,.025);}
        [data-testid="stMetricLabel"] {color:#667085 !important; font-family:var(--font-body); font-size:13px !important; font-weight:600; line-height:1.45;}
        [data-testid="stMetricValue"] {color:var(--ink) !important; font-family:var(--font-body); font-size:32px !important; font-weight:700; line-height:1.15; font-variant-numeric:tabular-nums;}
        [data-testid="stVerticalBlockBorderWrapper"] {background:#fff; border-color:var(--line); border-radius:12px;}
        [data-testid="stDataFrame"] {border:1px solid var(--line); border-radius:10px; overflow:hidden;}
        .chip {display:inline-block; padding:3px 9px; margin:0 4px 4px 0; border-radius:999px;
               font-size:12px; line-height:1.35; font-weight:600;}
        .chip.syn {background:#e8eefc;color:#2b4ea2;} .chip.warn {background:#fff1d6;color:#805400;}
        .chip.ok {background:#dff5e6;color:#1d6b3a;} .chip.bad {background:#fde2e1;color:#a02320;}
        .score {font-size:30px; font-weight:750; line-height:1.15; color:var(--ink); font-variant-numeric:tabular-nums;}
        .muted {color:#667085; font-size:13px; font-weight:400; line-height:1.5;}
        .section-heading {display:flex; align-items:baseline; justify-content:space-between; gap:.7rem; margin:.35rem 0 .6rem;}
        .section-heading h2 {font-family:var(--font-body); color:var(--ink); font-size:22px; font-weight:700; line-height:1.3; margin:0;}
        .section-heading > span {color:var(--muted); font-size:13px; font-weight:400; line-height:1.45; text-align:right;}
        .section-spaced {margin-top:1.25rem;}
        .empty-state {display:flex; align-items:center; gap:.9rem; padding:.25rem 0 .65rem;}
        .empty-icon {display:flex; flex:0 0 44px; width:44px; height:44px; align-items:center; justify-content:center; border-radius:12px; color:var(--teal); background:#e8f3f1;}
        .empty-state h3 {font-family:var(--font-body); font-size:16px; font-weight:600; line-height:1.4; color:var(--ink); margin:0 0 .2rem;}
        .empty-state p, .status-panel p {margin:0; color:var(--muted); font-size:14px; font-weight:400; line-height:1.55;}
        .status-panel {display:flex; align-items:flex-start; gap:.7rem; color:var(--teal); background:#fff; border:1px solid var(--line); border-radius:9px; padding:.8rem .9rem;}
        .status-panel strong {display:block; color:var(--ink); font-size:15px; font-weight:600; line-height:1.45; margin-bottom:.12rem;}
        .status-dot {display:inline-block; width:8px; height:8px; border-radius:50%; margin:0 .45rem .05rem 0; background:var(--teal);}
        .status-assessment, .status-interview {background:#6486c0;} .status-offer {background:var(--teal);} .status-rejected, .status-withdrawn {background:#a1a5ad;} .status-preparing {background:var(--coral);}
        .status-count {color:var(--ink); font-size:14px; font-weight:700; font-variant-numeric:tabular-nums;}
        .row-separator {height:1px; background:#edf0f1; margin:.45rem 0;}
        .recent-role {font-family:var(--font-body); color:var(--ink); font-size:16px; line-height:1.4; font-weight:600; margin:.35rem 0 .2rem; overflow-wrap:anywhere;}
        .recent-company {font-size:14px; line-height:1.5; color:#667085; margin-bottom:.55rem;}
        .recommendation-score {font-size:13px; line-height:1.5; color:var(--muted); margin:.35rem 0;}
        .recommendation-score strong {color:var(--teal); float:right;}
        .compact-empty {padding:.45rem .1rem; color:var(--muted); font-size:14px; line-height:1.55;}
        [data-testid="stWidgetLabel"] {font-family:var(--font-body); font-size:14px; font-weight:600; line-height:1.45; color:var(--ink);}
        [data-testid="stWidgetLabel"] p {font-family:var(--font-body); font-size:14px; font-weight:600; line-height:1.45;}
        [data-testid="stCaptionContainer"] {font-family:var(--font-body); font-size:13px; font-weight:400; line-height:1.5; color:#667085;}
        [data-testid="stMarkdownContainer"] {font-family:var(--font-body); color:var(--ink); font-size:15px; line-height:1.6;}
        [data-testid="stMarkdownContainer"] p {font-family:var(--font-body); font-size:15px; line-height:1.6;}
        [data-testid="stButton"] button, [data-testid="stDownloadButton"] button, [data-testid="stFormSubmitButton"] button {
          font-family:var(--font-body); font-size:14px; font-weight:600; line-height:1.35; border-radius:8px; min-height:2.5rem;
        }
        [data-testid="stButton"] button p, [data-testid="stDownloadButton"] button p, [data-testid="stFormSubmitButton"] button p {
          font-family:var(--font-body); font-size:14px; font-weight:600; line-height:1.35;
        }
        input, textarea, select, [role="combobox"] {font-family:var(--font-body); font-size:14px; line-height:1.5;}
        [data-testid="stExpander"] summary, [data-testid="stExpander"] button {font-family:var(--font-body); font-size:14px; font-weight:600; line-height:1.45;}
        [role="tab"] {font-family:var(--font-body); font-size:14px; font-weight:600;}
        [data-testid="stAlert"] {font-family:var(--font-body); font-size:15px; line-height:1.55; border-radius:10px;}
        [data-testid="stForm"] {border-color:var(--line); border-radius:12px;}
        @media (max-width: 900px) {
          .block-container {padding:.85rem 1rem 2rem;} h1.page-title {font-size:28px;}
          .section-heading > span {font-size:13px;}
          section[data-testid="stSidebar"] {width:250px !important; min-width:250px !important;}
          [data-testid="stMain"] [data-testid="stHorizontalBlock"] {flex-wrap:wrap !important; row-gap:.75rem;}
          [data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {flex:1 1 260px !important; min-width:min(100%,260px) !important;}
          .st-key-dashboard-kpi [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {flex:1 1 calc(50% - .4rem) !important; min-width:calc(50% - .4rem) !important;}
          .st-key-dashboard-overview-row [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {flex:1 1 100% !important; min-width:100% !important;}
          .st-key-dashboard-recent-grid [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {flex:1 1 calc(50% - .4rem) !important; min-width:calc(50% - .4rem) !important;}
          .st-key-dashboard-recommendation-grid [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {flex:1 1 100% !important; min-width:100% !important;}
        }
        @media (max-width: 640px) {
          .block-container {padding:.7rem .75rem 1.5rem;} .section-heading {align-items:flex-start; flex-direction:column; gap:.15rem;}
          .empty-state {align-items:flex-start;} .kpi-card {padding:.6rem .65rem; min-height:84px;}
          h1.page-title {font-size:26px;} .kpi-value {font-size:30px;} .kpi-top {font-size:12px;} .kpi-icon {width:26px;height:26px;}
          .st-key-dashboard-recent-grid [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {flex:1 1 100% !important; min-width:100% !important;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">Agentic AI · Education and Career Operations</div>
          <h1>Omnitrix</h1>
          <p>Find relevant roles, check listing quality, and keep application next steps visible. Demo listings are synthetic.</p>
        </div>
        <div class="section-note"><b>The problem:</b> internship searches, deadlines, and application notes are spread across platforms.
        <b> The PoC:</b> a visible agent workflow ranks and checks opportunities, while students approve tracker and resume changes.</div>
        """,
        unsafe_allow_html=True,
    )


def render_opportunity(record, already_tracked=False):
    """Render one validated listing. Return True only when the user selects save."""
    with st.container(border=True):
        score_col, detail_col = st.columns([1, 6], vertical_alignment="center")
        score_col.markdown(
            f"<div class='score'>{int(record['score'])}</div><div class='muted'>match / 100</div>",
            unsafe_allow_html=True,
        )
        badges = chip(record["label"], "syn")
        badges += chip(record["platform"], "ok" if record.get("source_url") else "warn")
        badges += "".join(chip(w, "bad" if "Expired" in w else "warn") for w in record["warnings"])
        detail_col.markdown(
            f"**{safe_text(record['role_title'])}** · {safe_text(record['company'])}  \n"
            f"<span class='muted'>{safe_text(record['location'])} · {safe_text(record['work_mode'])} · "
            f"{safe_text(record['opportunity_type'])} · deadline {safe_text(record.get('deadline') or 'unknown')}</span>  \n{badges}",
            unsafe_allow_html=True,
        )
        if record.get("also_listed_on"):
            detail_col.caption("Also listed on: " + ", ".join(record["also_listed_on"]) + " (duplicates grouped)")
        with detail_col.expander("Why this score"):
            st.write(record["explanation"])
            st.dataframe(pd.DataFrame([record["breakdown"]]), hide_index=True, width="stretch")
            if record.get("source_url"):
                st.caption("Synthetic example URL. This is not a live or verified listing.")
            else:
                st.caption("Source unavailable. This listing is not verified.")
        if already_tracked:
            detail_col.caption("Already in your tracker")
            return False
        return detail_col.button("Save to tracker", key=f"save_{record['job_id']}")


def render_action(action):
    st.markdown(
        f"**{safe_text(action['company'])}** · {safe_text(action['role_title'])}  \n"
        f"{chip(action['kind'], 'warn')} <span class='muted'>due {safe_text(action['due'])}</span>  \n"
        f"{safe_text(action['message'])}",
        unsafe_allow_html=True,
    )
