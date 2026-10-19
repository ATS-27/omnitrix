import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LISTINGS_CSV = os.path.join(ROOT, "data", "listings.csv")
DB_PATH = os.path.join(ROOT, "data", "tracker.db")
SAMPLE_RESUME = os.path.join(ROOT, "data", "sample_resume.txt")
SAMPLE_JD = os.path.join(ROOT, "data", "sample_job_description.txt")

# Fixed "today" so the demo and tests are repeatable; the UI can switch to the real date.
DEMO_TODAY = date(2026, 10, 15)

# Documented, configurable score weights (must sum to 100)
WEIGHTS = {"skills": 50, "role": 20, "location_mode": 15, "opp_type": 10, "deadline": 5}

STATUSES = ["Saved", "Preparing", "Applied", "Assessment", "Interview", "Offer", "Rejected", "Withdrawn"]
TERMINAL_STATUSES = {"Offer", "Rejected", "Withdrawn"}

DEADLINE_SOON_DAYS = 7
NO_MATCH_THRESHOLD = 25   # best score below this => "no strong match" message
FOLLOWUP_GAP_DAYS = 7     # default follow-up gap suggested after applying

REQUIRED_FIELDS = ["job_id", "company", "role_title", "platform", "required_skills",
                   "location", "work_mode", "opportunity_type"]

# Suggested (never verified) next step per tracker status
NEXT_ACTION = {
    "Saved": "Review the listing and decide whether to apply",
    "Preparing": "Tailor resume and submit before the deadline",
    "Applied": "Check the application portal / follow up if no reply",
    "Assessment": "Complete the assessment before its due date",
    "Interview": "Prepare for the interview and send a thank-you note",
}
