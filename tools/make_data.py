# Generates the synthetic listings CSV. All rows are fake (marked is_synthetic=True)
# and URLs use the reserved example.com domain.
import csv, os

# Dates are fixed so the demo is repeatable; the app treats 2026-10-15 as "today" by default.
ROWS = [
 # id, company, title, platform, skills, location, mode, type, posted, deadline, status
 ("SYN-001","NovaLabs","AI/ML Intern","LinkedIn","python;machine learning;pytorch;sql","Pune","Hybrid","Internship","2026-10-01","2026-10-20","Open"),
 ("SYN-002","Finverse","Data Science Intern","Workday","python;sql;pandas;statistics","Bengaluru","Onsite","Internship","2026-09-28","2026-10-18","Open"),
 ("SYN-003","CyberShield","Security Analyst Intern","LinkedIn","owasp;burp suite;python;networking","Pune","Hybrid","Internship","2026-10-05","2026-10-30","Open"),
 ("SYN-004","LexAI","NLP Research Intern","YC Jobs","python;nlp;transformers;pytorch","Remote","Remote","Research","2026-10-03","2026-11-05","Open"),
 ("SYN-005","NovaLabs","AI/ML Intern","Workday","python;machine learning;pytorch;sql","Pune","Hybrid","Internship","2026-10-02","2026-10-20","Open"),  # cross-platform duplicate of 001
 ("SYN-006","CloudNest","Backend Developer Intern","Workday","python;fastapi;sql;docker","Hyderabad","Hybrid","Internship","2026-10-04","2026-11-10","Open"),
 ("SYN-007","PixelForge","Frontend Intern","LinkedIn","javascript;react;css;html","Mumbai","Onsite","Internship","2026-10-06","2026-11-02","Open"),
 ("SYN-008","OldCorp","Junior Data Analyst","Workday","sql;excel;python","Pune","Onsite","Full-time","2026-08-20","2026-09-30","Open"),  # expired but still marked Open
 ("SYN-009","VisionWorks","Computer Vision Intern","YC Jobs","python;opencv;pytorch;deep learning","Remote","Remote","Internship","2026-10-07","2026-11-15","Open"),
 ("SYN-010","SecureStack","Web Pentest Trainee","LinkedIn","owasp;burp suite;sql injection;python","Pune","Onsite","Full-time","2026-10-08","2026-11-01","Open"),
 ("SYN-011","DataBridge","ML Engineer (Fresher)","Workday","python;machine learning;docker;aws;sql","Bengaluru","Hybrid","Full-time","2026-10-02","2026-10-22","Open"),
 ("SYN-012","MysteryCo","AI Intern","YC Jobs","python;machine learning","Remote","Remote","Internship","2026-10-09","","Open"),  # missing deadline
 ("SYN-013","EduSpark","NLP Engineer Intern","LinkedIn","python;nlp;spacy;sql","Pune","Hybrid","Internship","2026-10-10","2026-11-20","Open"),
 ("SYN-014","GreenGrid","Data Engineer Intern","Workday","python;sql;spark;airflow","Chennai","Onsite","Internship","2026-10-01","2026-10-25","Open"),
 ("SYN-015","NoLink Inc","Software Intern","Other","python;git;sql","Pune","Hybrid","Internship","2026-10-09","2026-11-08","Open"),  # missing source URL
 ("SYN-016","AgentWorks","LLM Application Intern","YC Jobs","python;langchain;llm;rag;docker","Remote","Remote","Internship","2026-10-11","2026-11-12","Open"),
 ("SYN-017","HealthAI","ML Research Assistant","Other","python;machine learning;statistics;pytorch","Pune","Onsite","Research","2026-10-05","2026-11-25","Open"),
 ("SYN-018","RetailRocket","Business Analyst Intern","LinkedIn","sql;excel;power bi;communication","Mumbai","Hybrid","Internship","2026-10-07","2026-10-28","Open"),
 ("SYN-019","StaleSoft","QA Automation Intern","Workday","selenium;python;sql","Pune","Hybrid","Internship","2026-08-30","2026-10-05","Open"),  # expired
 ("SYN-020","AutoDrive","Perception Intern","LinkedIn","python;opencv;c++;deep learning","Bengaluru","Onsite","Internship","2026-10-03","2026-11-18","Open"),
 ("SYN-021","ClosedCo","Security Intern","LinkedIn","owasp;python","Pune","Hybrid","Internship","2026-09-20","2026-11-30","Closed"),  # status says closed
 ("SYN-022","InfraLoop","DevOps Intern","Workday","docker;kubernetes;linux;aws","Hyderabad","Hybrid","Internship","2026-10-08","2026-11-06","Open"),
 ("SYN-023","TextTrail","Applied NLP Intern","YC Jobs","python;nlp;transformers;docker;sql","Remote","Remote","Internship","2026-10-12","2026-10-19","Open"),
 ("SYN-024","DriftData","Analytics Intern","Other","python;sql;tableau","Pune","Onsite","Internship","2026-10-10","","Unknown"),  # missing deadline + status
 ("SYN-025","BlueHarbor","Threat Intel Intern","LinkedIn","python;networking;owasp;linux","Pune","Remote","Internship","2026-10-06","2026-11-14","Open"),
 ("SYN-026","MobiTech","Android Intern","Workday","kotlin;java;android","Pune","Onsite","Internship","2026-10-02","2026-11-04","Open"),
 ("SYN-027","BadDate Ltd","Data Intern","Other","python;sql","Remote","Remote","Internship","2026-10-09","31/13/2026","Open"),  # invalid date format
 ("SYN-028","Quantix","Quant Research Intern","LinkedIn","python;statistics;c++;probability","Mumbai","Onsite","Internship","2026-10-04","2026-11-09","Open"),
 ("SYN-029","CyberShield","Security Analyst Intern","LinkedIn","owasp;burp suite;python;networking","Pune","Hybrid","Internship","2026-10-05","2026-10-30","Open"),  # exact duplicate of 003
 ("SYN-030","VoiceLoop","Speech/NLP Intern","YC Jobs","python;nlp;pytorch;audio","Remote","Remote","Research","2026-10-11","2026-11-22","Open"),
]
# Same URL slug for cross-platform duplicate pair (001/005) so URL normalisation is exercised.
NO_URL = {"SYN-015"}

def main():
    out = os.path.join(os.path.dirname(__file__), "..", "data", "listings.csv")
    cols = ["job_id","company","role_title","platform","source_url","required_skills","location",
            "work_mode","opportunity_type","posted_date","deadline","listing_status","description","is_synthetic"]
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in ROWS:
            jid, co, title, plat, skills, loc, mode, typ, posted, dl, st = r
            slug = f"{co}-{title}".lower().replace(" ", "-").replace("/", "-").replace("(", "").replace(")", "")
            url = "" if jid in NO_URL else f"https://example.com/jobs/{slug}"
            desc = f"[SYNTHETIC] {title} at {co}. Work with {', '.join(skills.split(';'))}."
            w.writerow([jid, co, title, plat, url, skills, loc, mode, typ, posted, dl, st, desc, True])
    print("wrote", len(ROWS), "rows")

if __name__ == "__main__":
    main()
