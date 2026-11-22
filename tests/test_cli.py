"""Tests for the CLI and reports."""
import json
from pathlib import Path

from resumescreener.cli import main
from resumescreener import parse_job_description, parse_resume, rank, render_json, render_markdown

ROOT = Path(__file__).resolve().parents[1]


def test_demo_runs_and_writes_outputs(tmp_path):
    assert main(["demo"]) == 0
    report = ROOT / "outputs" / "report.md"
    summary = ROOT / "outputs" / "summary.json"
    assert report.exists() and summary.exists()
    data = json.loads(summary.read_text())
    assert data["role"].startswith("Python Backend Developer")
    assert len(data["results"]) == 4
    assert data["results"][0]["candidate"] == "Ayesha Khan"
    assert data["results"][0]["verdict"] == "Strong match"
    assert data["results"][-1]["candidate"] == "Chen Wei"


def test_demo_ranking_is_deterministic():
    jd = parse_job_description((ROOT / "examples" / "job_description.txt").read_text())
    resumes = [parse_resume(p.read_text()) for p in sorted((ROOT / "examples" / "resumes").glob("*.txt"))]
    first = [r.resume.name for r in rank(resumes, jd)]
    second = [r.resume.name for r in rank(resumes, jd)]
    assert first == second == ["Ayesha Khan", "Sara Malik", "Bilal Ahmed", "Chen Wei"]


def test_markdown_report_lists_evidence_and_not_considered():
    jd = parse_job_description((ROOT / "examples" / "job_description.txt").read_text())
    resumes = [parse_resume(p.read_text()) for p in sorted((ROOT / "examples" / "resumes").glob("*.txt"))]
    md = render_markdown(rank(resumes, jd))
    assert "Evidence" in md
    assert "Not considered" in md
    assert "Missing required skills" in md
    assert "Ayesha Khan" in md


def test_json_report_round_trips():
    jd = parse_job_description((ROOT / "examples" / "job_description.txt").read_text())
    resumes = [parse_resume(p.read_text()) for p in sorted((ROOT / "examples" / "resumes").glob("*.txt"))]
    data = json.loads(render_json(rank(resumes, jd)))
    assert data["shortlisted"] == 2
    assert all("criteria" in r for r in data["results"])


def test_screen_cli_json_output(tmp_path):
    out = tmp_path / "out.json"
    rc = main(["screen", str(ROOT / "examples" / "job_description.txt"),
               str(ROOT / "examples" / "resumes"), "--format", "json", "--output", str(out)])
    assert rc == 0
    data = json.loads(out.read_text())
    assert len(data["results"]) == 4


def test_fail_under_exits_nonzero_when_top_score_low(tmp_path):
    jd = tmp_path / "jd.txt"
    jd.write_text("Role\nRequired skills:\n- Rust\n- Kubernetes\nExperience:\n- Minimum 5 years of experience\n")
    resume = tmp_path / "r.txt"
    resume.write_text("Zed\nJava developer with 1 year of experience.\nBachelor of Science.")
    assert main(["screen", str(jd), str(resume), "--fail-under", "80"]) == 1
