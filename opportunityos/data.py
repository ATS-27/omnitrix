import pandas as pd
from .config import LISTINGS_CSV

ALIASES = {"ml": "machine learning", "natural language processing": "nlp",
           "burpsuite": "burp suite", "py": "python", "js": "javascript",
           "powerbi": "power bi", "deep-learning": "deep learning"}

def norm_skill(s):
    s = str(s).strip().lower()
    return ALIASES.get(s, s)

def split_skills(value):
    # accepts "a;b;c" or "a, b, c"
    raw = str(value or "").replace(",", ";").split(";")
    out = []
    for x in raw:
        n = norm_skill(x)
        if n and n not in out:
            out.append(n)
    return out

# Everything stays a string on load: validation (not pandas) decides what is a valid date.
def load_listings(path=LISTINGS_CSV):
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return df.to_dict("records")
