import io, re

BULLETS = ("- ", "• ", "* ", "– ")
HEADINGS = {"EDUCATION": "education", "SKILLS": "skills", "TECHNICAL SKILLS": "skills",
            "PROJECTS": "projects", "EXPERIENCE": "experience", "WORK EXPERIENCE": "experience",
            "INTERNSHIPS": "experience", "CERTIFICATIONS": "certifications", "CERTIFICATES": "certifications"}

# Reads PDF / DOCX / text into plain text with "- " bullets. The original bytes are never modified.
def extract_text(name, data):
    ext = name.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        from pypdf import PdfReader
        pages = [p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages]
        text = "\n".join(pages)
    elif ext == "docx":
        import docx
        lines = []
        for p in docx.Document(io.BytesIO(data)).paragraphs:
            t = p.text.strip()
            if not t:
                lines.append("")
            elif "List" in (p.style.name or ""):
                lines.append("- " + t)
            else:
                lines.append(t)
        text = "\n".join(lines)
    else:
        text = data.decode("utf-8", errors="replace")
    return text.replace("\r", "").replace("•", "- ")

def _is_bullet(line):
    return line.lstrip().startswith(BULLETS)

def _strip_bullet(line):
    s = line.strip()
    for b in BULLETS:
        if s.startswith(b):
            return s[len(b):].strip()
    return s

# Splits text into a structured resume: header, education, skills, projects/experience (name + bullets), certifications.
def parse_resume(text):
    r = {"header": [], "education": [], "skills": [], "projects": [], "experience": [],
         "certifications": [], "other": {}, "source_text": text}
    current, cur_item = "header", None
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        key = HEADINGS.get(line.upper().rstrip(":"))
        if key or (line.isupper() and len(line) < 40 and line.replace(" ", "").isalpha()):
            current = key or line.title()
            cur_item = None
            if not key:
                r["other"].setdefault(current, [])
            continue
        if current in ("projects", "experience"):
            if _is_bullet(raw):
                if cur_item is None:
                    cur_item = {"name": "(untitled)", "bullets": []}
                    r[current].append(cur_item)
                cur_item["bullets"].append(_strip_bullet(raw))
            else:
                cur_item = {"name": line, "bullets": []}
                r[current].append(cur_item)
        elif current == "skills":
            r["skills"] += [s.strip() for s in re.split(r"[,;|]", _strip_bullet(line)) if s.strip()]
        elif current in r and isinstance(r[current], list):
            r[current].append(_strip_bullet(line))
        else:
            r["other"].setdefault(current, []).append(_strip_bullet(line))
    return r

# Flat list of (section, item, text) evidence lines used by the gap analysis.
def evidence_lines(resume):
    out = []
    for sec in ("projects", "experience"):
        for item in resume[sec]:
            for b in item["bullets"]:
                out.append((sec, item["name"], b))
    for c in resume["certifications"]:
        out.append(("certifications", "", c))
    return out
