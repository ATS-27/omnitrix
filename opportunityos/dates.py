from datetime import date

# Returns (date_or_None, state) where state is "ok", "missing" or "invalid".
# Strict ISO (YYYY-MM-DD) only, so "31/13/2026" is flagged instead of guessed.
def parse_date(value):
    s = str(value or "").strip()
    if not s:
        return None, "missing"
    try:
        return date.fromisoformat(s), "ok"
    except ValueError:
        return None, "invalid"
