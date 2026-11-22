"""Tests for scoring, verdicts, explainability and ranking."""
from resumescreener import parse_job_description, parse_resume, rank, screen

JD = parse_job_description(
    "Python Backend Developer\nRequired skills:\n- Python\n- Django\n- PostgreSQL\n"
    "Preferred skills:\n- AWS\nExperience:\n- Minimum 3 years of experience\n"
    "Education:\n- Bachelor's degree required\n"
)


def _resume(text: str):
    return parse_resume(text)


def test_perfect_candidate_scores_high_and_strong_match():
    r = _resume(
        "Ana\nPython Django PostgreSQL AWS developer with 5 years of experience.\n"
        "Bachelor of Science in Computer Science. Built backend services, APIs, databases."
    )
    s = screen(r, JD)
    assert s.score >= 85
    assert s.verdict == "Strong match"
    assert s.missing_required == []
    assert s.matched_required == ["django", "postgresql", "python"]
    assert s.matched_preferred == ["aws"]


def test_missing_required_skill_costs_points_and_is_listed():
    r = _resume(
        "Ben\nPython Django developer with 4 years of experience.\n"
        "Bachelor of Science. Built backend services and APIs."
    )
    s = screen(r, JD)
    assert "postgresql" in s.missing_required
    assert s.score < 90
    assert any("postgresql" in g for g in s.gaps)


def test_experience_shortfall_is_proportional():
    full = screen(_resume("C\nPython Django PostgreSQL with 3 years of experience.\nBachelor of Science."), JD)
    half = screen(_resume("D\nPython Django PostgreSQL with 1 years of experience.\nBachelor of Science."), JD)
    exp_full = next(c for c in full.criteria if c.name == "Experience").earned
    exp_half = next(c for c in half.criteria if c.name == "Experience").earned
    assert exp_full == 25.0
    assert exp_half == 8.3  # 25 * 1/3


def test_education_below_requirement_loses_points():
    r = _resume("E\nPython Django PostgreSQL with 5 years of experience.\nHigh school diploma.")
    s = screen(r, JD)
    edu = next(c for c in s.criteria if c.name == "Education")
    assert edu.earned == 3.0


def test_education_unstated_is_neutral_not_zero():
    r = _resume("F\nPython Django PostgreSQL with 5 years of experience.")
    s = screen(r, JD)
    edu = next(c for c in s.criteria if c.name == "Education")
    assert edu.earned == 7.0


def test_criteria_sum_to_score():
    r = _resume("G\nPython developer with 2 years of experience.\nBachelor of Science.")
    s = screen(r, JD)
    assert abs(sum(c.earned for c in s.criteria) - s.score) < 0.01


def test_verdict_bands():
    assert screen(_resume("H\nPython Django PostgreSQL AWS with 5 years of experience.\nBachelor of Science. backend services APIs databases"), JD).verdict == "Strong match"
    assert screen(_resume("I\nJava developer with 1 year of experience.\nBachelor of Science."), JD).verdict == "Not a match"


def test_evidence_quotes_exact_resume_lines():
    r = _resume("J\nPython Django PostgreSQL with 3 years of experience.\nBachelor of Science.\nBuilt Django APIs for clients.")
    s = screen(r, JD)
    assert "Django" in s.evidence["django"]


def test_rank_orders_by_score_then_name():
    a = _resume("Zoe\nPython Django PostgreSQL with 5 years of experience.\nBachelor of Science.")
    b = _resume("Amy\nPython Django PostgreSQL with 5 years of experience.\nBachelor of Science.")
    c = _resume("Max\nJava developer with 1 year of experience.\nBachelor of Science.")
    ranked = rank([a, b, c], JD)
    assert ranked[0].resume.name == "Amy"  # tie with Zoe, name breaks it
    assert ranked[1].resume.name == "Zoe"
    assert ranked[2].resume.name == "Max"


def test_report_never_uses_protected_fields():
    r = _resume("K\nPython Django PostgreSQL with 3 years of experience.\nBachelor of Science.")
    s = screen(r, JD)
    d = s.to_dict()
    assert "name" in d["not_considered"]
    assert "gender" in d["not_considered"]
    assert "age" in d["not_considered"]
