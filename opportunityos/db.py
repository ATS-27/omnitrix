import sqlite3
from datetime import datetime
from .config import DB_PATH, STATUSES

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,
    company TEXT, role_title TEXT, platform TEXT, source_url TEXT,
    deadline TEXT,
    status TEXT NOT NULL,
    date_applied TEXT, follow_up_date TEXT,
    notes TEXT DEFAULT '', next_action TEXT DEFAULT '',
    updated_at TEXT
)"""

def connect(path=DB_PATH):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute(SCHEMA)
    return con

def _now():
    return datetime.now().isoformat(timespec="seconds")

# Save a listing to the tracker; saving the same job twice is a no-op (no duplicate rows).
def save_role(job, status="Saved", path=DB_PATH):
    if status not in STATUSES:
        raise ValueError(f"unknown status {status}")
    with connect(path) as con:
        cur = con.execute("SELECT application_id FROM applications WHERE job_id=?", (job["job_id"],))
        if cur.fetchone():
            return False
        con.execute(
            "INSERT INTO applications (job_id, company, role_title, platform, source_url, deadline, status, updated_at)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (job["job_id"], job.get("company"), job.get("role_title"), job.get("platform"),
             job.get("source_url"), job.get("deadline"), status, _now()))
        return True

def update_application(job_id, path=DB_PATH, **fields):
    allowed = {"status", "date_applied", "follow_up_date", "notes", "next_action"}
    bad = set(fields) - allowed
    if bad:
        raise ValueError(f"cannot update {bad}")
    if "status" in fields and fields["status"] not in STATUSES:
        raise ValueError(f"unknown status {fields['status']}")
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields) + ", updated_at=?"
    with connect(path) as con:
        con.execute(f"UPDATE applications SET {sets} WHERE job_id=?", (*fields.values(), _now(), job_id))

def list_applications(path=DB_PATH):
    with connect(path) as con:
        return [dict(r) for r in con.execute("SELECT * FROM applications ORDER BY updated_at DESC")]

def get_application(job_id, path=DB_PATH):
    with connect(path) as con:
        r = con.execute("SELECT * FROM applications WHERE job_id=?", (job_id,)).fetchone()
        return dict(r) if r else None

def delete_application(job_id, path=DB_PATH):
    with connect(path) as con:
        con.execute("DELETE FROM applications WHERE job_id=?", (job_id,))
