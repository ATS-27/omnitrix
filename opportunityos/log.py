# Shared workflow log: every agent writes one or more lines here, the UI shows them in order.
class WorkflowLog:
    def __init__(self):
        self.entries = []

    def add(self, agent, message):
        self.entries.append({"agent": agent, "message": message})

    def lines(self):
        return [f"[{e['agent']}] {e['message']}" for e in self.entries]
