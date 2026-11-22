"""CLI: screen resumes against a job description; demo on bundled data."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from resumescreener import (
    parse_job_description,
    parse_resume,
    rank,
    render_json,
    render_markdown,
)

BUNDLED = Path(__file__).resolve().parents[2] / "examples"


def _load_resumes(paths: list[Path]) -> list:
    resumes = []
    for p in paths:
        if p.is_dir():
            resumes += [parse_resume(f.read_text(encoding="utf-8")) for f in sorted(p.glob("*.txt"))]
        else:
            resumes.append(parse_resume(p.read_text(encoding="utf-8")))
    return resumes


def _emit(results, fmt: str, output: Path | None, threshold: float) -> None:
    text = render_json(results, threshold) if fmt == "json" else render_markdown(results, threshold)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        shortlisted = sum(1 for r in results if r.score >= threshold)
        print(f"Wrote {output} ({len(results)} screened, {shortlisted} shortlisted)")
    else:
        print(text)


def _demo() -> int:
    jd = parse_job_description((BUNDLED / "job_description.txt").read_text(encoding="utf-8"))
    resumes = _load_resumes([BUNDLED / "resumes"])
    results = rank(resumes, jd)
    out_dir = Path(__file__).resolve().parents[2] / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text(render_markdown(results), encoding="utf-8")
    (out_dir / "summary.json").write_text(render_json(results), encoding="utf-8")
    print(f"Role: {jd.title}")
    print(f"Required skills: {', '.join(sorted(jd.required_skills))}")
    print(f"Preferred skills: {', '.join(sorted(jd.preferred_skills))}")
    print(f"Minimum: {jd.min_years:g} years, {jd.min_education[1] if jd.min_education else 'no education minimum'}")
    print()
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.resume.name}: {r.score:g}/100 — {r.verdict}")
    print()
    print(f"Wrote outputs/report.md and outputs/summary.json "
          f"({sum(1 for r in results if r.score >= 65)} shortlisted at 65+)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="resumescreen", description="Explainable offline resume screening.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_screen = sub.add_parser("screen", help="Screen resumes against a job description.")
    p_screen.add_argument("job", type=Path, help="Job description .txt file")
    p_screen.add_argument("resumes", type=Path, nargs="+", help="Resume .txt files or a directory")
    p_screen.add_argument("--format", choices=["md", "json"], default="md")
    p_screen.add_argument("--output", type=Path, default=None)
    p_screen.add_argument("--threshold", type=float, default=65.0, help="Shortlist threshold (default 65)")
    p_screen.add_argument("--fail-under", type=float, default=None,
                          help="Exit non-zero if the top score is below this value")

    sub.add_parser("demo", help="Run the bundled demo and write outputs/.")

    args = parser.parse_args(argv)
    if args.command == "demo":
        return _demo()

    jd = parse_job_description(args.job.read_text(encoding="utf-8"))
    resumes = _load_resumes(args.resumes)
    if not resumes:
        print("No resumes found.", file=sys.stderr)
        return 2
    results = rank(resumes, jd)
    _emit(results, args.format, args.output, args.threshold)
    if args.fail_under is not None and results[0].score < args.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
