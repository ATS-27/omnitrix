from datetime import timedelta
from ..dates import parse_date
from ..data import split_skills, norm_skill

# Filters the local dataset only; it never touches the network.
# Records with bad data are NOT dropped here, the Critic decides that later.
def discover(records, filters, as_of, log):
    f = filters or {}
    out = []
    for r in records:
        if f.get("types") and r["opportunity_type"].lower() not in [x.lower() for x in f["types"]]:
            continue
        if f.get("modes") and r["work_mode"].lower() not in [x.lower() for x in f["modes"]]:
            continue
        if f.get("locations") and r["location"].lower() not in [x.lower() for x in f["locations"]]:
            continue
        if f.get("role_keyword") and f["role_keyword"].lower() not in r["role_title"].lower():
            continue
        if f.get("skill"):
            if norm_skill(f["skill"]) not in split_skills(r["required_skills"]):
                continue
        if f.get("max_days") is not None:
            # "closing soon" needs a real deadline; unknown deadlines cannot qualify
            d, state = parse_date(r["deadline"])
            if state != "ok" or not (as_of <= d <= as_of + timedelta(days=int(f["max_days"]))):
                continue
        out.append(dict(r))
    log.add("Discovery", f"Retrieved {len(out)} of {len(records)} records from the demo dataset.")
    return out
