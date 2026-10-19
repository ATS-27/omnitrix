import re
from ..data import norm_skill

# Vocabulary used when a JD has no explicit "Required:" line
VOCAB = ["python", "sql", "docker", "kubernetes", "aws", "git", "pytorch", "tensorflow", "nlp", "transformers",
         "machine learning", "deep learning", "pandas", "react", "javascript", "fastapi", "spark", "airflow",
         "langchain", "rag", "llm", "owasp", "burp suite", "linux", "opencv", "statistics", "excel", "tableau",
         "power bi", "deployment", "streamlit", "java", "c++"]

# "Deployment experience" -> "deployment": drop filler words so the term can be matched in a resume
def _terms(s):
    out = []
    for x in re.split(r"[,;]", s):
        x = re.sub(r"\s+(experience|skills|knowledge|exposure)$", "", x.strip(), flags=re.I)
        if x:
            out.append(norm_skill(x))
    return out

def _find(term, text):
    return re.search(r"(?<![\w+])" + re.escape(term) + r"(?![\w+])", text, re.I) is not None

# Job Description Analyzer: separates required from preferred. Explicit lines win; otherwise vocabulary scan
# (everything found is treated as required, and the UI says so).
def analyze_jd(text):
    req, pref, explicit = [], [], False
    for line in text.split("\n"):
        m = re.match(r"\s*(required|requirements|must have)\s*:\s*(.+)", line, re.I)
        p = re.match(r"\s*(preferred|nice to have|bonus)\s*:\s*(.+)", line, re.I)
        if m:
            req += _terms(m.group(2)); explicit = True
        elif p:
            pref += _terms(p.group(2)); explicit = True
    if not explicit:
        req = [t for t in VOCAB if _find(t, text)]
    req = list(dict.fromkeys(req))
    pref = [t for t in dict.fromkeys(pref) if t not in req]
    title = text.strip().split("\n")[0].strip() if text.strip() else ""
    return {"title": title, "required": req, "preferred": pref, "explicit": explicit}

find_term = _find
