import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from opportunityos.data import load_listings

@pytest.fixture
def records():
    return load_listings()

@pytest.fixture
def profile():
    return {"skills": ["python", "sql", "pytorch", "nlp", "machine learning", "owasp", "burp suite"],
            "preferred_roles": ["AI", "NLP", "Security"], "preferred_locations": ["Pune", "Remote"],
            "preferred_modes": ["Hybrid", "Remote"], "preferred_types": ["Internship"]}

@pytest.fixture
def dbpath(tmp_path):
    return str(tmp_path / "t.db")
