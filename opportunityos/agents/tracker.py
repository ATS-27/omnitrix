from .. import db

# The only agent that writes to SQLite, and only when the UI passes an explicit user action.
class TrackerAgent:
    def __init__(self, path, log=None):
        self.path, self.log = path, log

    def _note(self, msg):
        if self.log:
            self.log.add("Tracker", msg)

    def save(self, job, status="Saved"):
        created = db.save_role(job, status, self.path)
        self._note(f"{'Saved' if created else 'Already tracked:'} {job['job_id']} ({job['company']})")
        return created

    def update(self, job_id, **fields):
        db.update_application(job_id, self.path, **fields)
        self._note(f"Updated {job_id}: {', '.join(f'{k}={v}' for k, v in fields.items())}")

    def all(self):
        return db.list_applications(self.path)
