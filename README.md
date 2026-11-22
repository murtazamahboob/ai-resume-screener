# AI Resume Screener — Explainable, Offline Resume Screening

**Screen resumes like a careful hiring manager — fully offline, no LLM, no API key, deterministic.** Most AI screeners are black boxes: a score appears and nobody can say why. This one shows its work: every point is traced to skills, experience, education or keyword overlap, every matched skill is quoted from the exact resume line it came from, and the report states plainly what was *never* used — name, email, phone, location, photo, age, gender, university prestige.

## Results (measured, not claimed)

The bundled demo screens 4 fictional resumes against a Python Backend Developer JD (6 required skills, 3 preferred, 3+ years, Bachelor's required):

| Candidate | Score | Verdict | Missing required skills |
|---|---|---|---|
| Ayesha Khan | **94.6** | Strong match | none |
| Sara Malik | **80.3** | Strong match | Docker |
| Bilal Ahmed | **64.8** | Borderline | Docker, PostgreSQL, REST API |
| Chen Wei | **42.0** | Not a match | Django, Docker, PostgreSQL, Python |

2 of 4 shortlisted at the default 65/100 threshold. Bilal misses it by 0.2 — the report shows exactly why.

| Metric | Measured |
|---|---|
| Test suite | **28/28 tests pass**, verified twice — including in a fresh venv |
| Demo | identical scores in both runs (94.6 / 80.3 / 64.8 / 42.0) |
| Runtime dependencies | **none** (stdlib only) |

## Features

- **Transparent weighted rubric (100 points)** — Skills 45 (40 required-skill coverage + 5 preferred), Experience 25 (years vs the JD minimum), Education 15 (level vs the JD minimum), Keywords 15 (JD content-word overlap). The criteria always sum exactly to the score.
- **Evidence for every point** — each matched skill carries the exact resume line that proved it; missing required skills are listed, not hidden.
- **Strengths and gaps, in plain language** — the top reasons for and against each candidate, e.g. "Experience shortfall: 1 vs 3+ years required".
- **Fair by construction** — the scorer never reads name, email, phone, location, photo, age, gender or university prestige. Unstated education scores neutral (7/15), never zero — a missing field is not treated as a failure.
- **Deterministic ranking** — highest score first, candidate name breaks ties, so the same inputs always produce the same order.
- **Honest parsing** — skills match whole phrases only (`java` never matches `javascript`; `postgres` collapses to `postgresql`, never double-counted). Years come from explicit claims or dated ranges; unstated fields stay empty instead of being invented.
- **CLI-ready** — screen a JD against files or a whole directory, Markdown or JSON output, `--threshold` for shortlisting, `--fail-under N` to gate a pipeline.

## Quickstart

```bash
pip install -r requirements.txt
pip install -e .

# Screen resumes against a job description
resumescreen screen job_description.txt ./resumes --format md --output report.md

# JSON for tooling, and fail if nobody clears 80
resumescreen screen job_description.txt ./resumes --format json --fail-under 80

# Run the full demo (screens 4 bundled resumes, writes outputs/)
python examples/demo.py
```

## Python API

```python
from resumescreener import parse_job_description, parse_resume, rank

jd = parse_job_description(open("job_description.txt").read())
resumes = [parse_resume(open(f).read()) for f in ["ayesha.txt", "bilal.txt"]]

for result in rank(resumes, jd):
    print(result.resume.name, result.score, result.verdict)
    print("missing:", result.missing_required)
    print("evidence:", result.evidence["django"])  # exact resume line
```

## How scoring works

| Criterion | Max | Rule |
|---|---|---|
| Skills | 45 | 40 × required-skill coverage + 5 × preferred-skill coverage |
| Experience | 25 | 25 × min(years ÷ JD minimum, 1); no minimum in JD scores vs 5 years |
| Education | 15 | Meets requirement 15 · one level below 8 · two or more below 3 · unstated 7 |
| Keywords | 15 | 15 × share of JD content words (stopwords and skills excluded) that appear in the resume |

Verdicts: ≥80 Strong match · ≥65 Good fit · ≥50 Borderline · below 50 Not a match.

## Project layout

```
src/resumescreener/
  taxonomy.py   # 60-skill taxonomy with aliases + education levels
  parse.py      # resume + JD parsing (skills, years, education)
  score.py      # weighted scoring, verdicts, strengths/gaps
  report.py     # Markdown + JSON reports
  cli.py        # `screen` and `demo` commands
examples/
  job_description.txt
  resumes/      # 4 fictional resumes (Ayesha, Sara, Bilal, Chen)
tests/          # 28 tests: parsing, scoring, CLI, reports
```

## License

MIT — see `LICENSE`.
