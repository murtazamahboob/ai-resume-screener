"""Tests for resume and job-description parsing."""
from resumescreener import parse_job_description, parse_resume


def test_name_email_phone_extracted():
    r = parse_resume("Dana Lee\ndana@example.com | +1 555 123 4567\nPython developer")
    assert r.name == "Dana Lee"
    assert r.email == "dana@example.com"
    assert r.phone is not None and "555" in r.phone


def test_skill_aliases_collapse_to_canonical():
    r = parse_resume("X\nWorked with Postgres and PostgreSQL databases.")
    assert r.skills == {"postgresql"}


def test_java_does_not_match_javascript():
    r = parse_resume("X\nJavaScript and React developer.")
    assert "javascript" in r.skills
    assert "java" not in r.skills


def test_years_from_explicit_claim():
    r = parse_resume("X\nBackend developer with 4 years of experience.")
    assert r.years_experience == 4


def test_years_from_claim_beats_date_ranges():
    r = parse_resume("X\n6 years of experience.\nDeveloper, Acme (2019 - 2021)")
    assert r.years_experience == 6


def test_years_from_date_ranges_when_no_claim():
    r = parse_resume("X\nDeveloper, Acme (2019 - 2022)\nDeveloper, Beta (2022 - Present)")
    assert r.years_experience == 7  # 3 + 4 (present = 2026)


def test_years_none_when_unstated():
    assert parse_resume("X\nPython developer.").years_experience is None


def test_education_highest_level_wins():
    r = parse_resume("X\nMSc Data Science\nBachelor of Science (2018)")
    assert r.education == (4, "Master's")


def test_education_none_when_unstated():
    assert parse_resume("X\nPython developer.").education is None


def test_jd_sections_split_required_and_preferred():
    jd = parse_job_description(
        "Backend Developer\nRequired skills:\n- Python\n- Django\n"
        "Preferred skills:\n- AWS\n- Redis\n"
        "Experience:\n- Minimum 3 years of experience\n"
        "Education:\n- Bachelor's degree required\n"
    )
    assert jd.required_skills == {"python", "django"}
    assert jd.preferred_skills == {"aws", "redis"}
    assert jd.min_years == 3
    assert jd.min_education == (3, "Bachelor's")


def test_jd_without_sections_treats_all_skills_as_required():
    jd = parse_job_description("Data Analyst\nWe need pandas, SQL and Excel skills.")
    assert jd.required_skills == {"pandas", "sql", "excel"}
    assert jd.preferred_skills == set()


def test_jd_min_years_variants():
    assert parse_job_description("Role\nAt least 2 years of experience.").min_years == 2
    assert parse_job_description("Role\n5+ years of experience required.").min_years == 5
