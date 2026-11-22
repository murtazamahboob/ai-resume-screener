"""Reports: Markdown and JSON renderings of a screening.

The Markdown report is the explainability surface: a candidate (or a
hiring manager) can see every point, where it came from, and what was
never used. The JSON report carries the same data for tooling.
"""
from __future__ import annotations

import json

from .score import NOT_CONSIDERED, Screening


def render_markdown(results: list[Screening], threshold: float = 65.0) -> str:
    job = results[0].job if results else None
    title = job.title if job else "Role"
    lines = [
        f"# Resume Screening — {title}",
        "",
        f"**{len(results)} candidates screened · shortlist threshold {threshold:g}/100 "
        f"· {sum(1 for r in results if r.score >= threshold)} shortlisted**",
        "",
        "## Ranking",
        "",
        "| Rank | Candidate | Score | Verdict |",
        "|---|---|---|---|",
    ]
    for i, r in enumerate(results, 1):
        mark = "✅" if r.score >= threshold else "—"
        lines.append(f"| {i} | {r.resume.name} | **{r.score:g}** | {r.verdict} {mark} |")
    lines += ["", "---", ""]
    for i, r in enumerate(results, 1):
        lines += [
            f"## {i}. {r.resume.name} — {r.score:g}/100 ({r.verdict})",
            "",
            "| Criterion | Points | Why |",
            "|---|---|---|",
        ]
        for c in r.criteria:
            lines.append(f"| {c.name} | {c.earned:g}/{c.maximum:g} | {c.reason} |")
        lines += [
            "",
            f"**Matched required skills:** {', '.join(r.matched_required) or 'none'}",
            "",
            f"**Missing required skills:** {', '.join(r.missing_required) or 'none'}",
            "",
            f"**Matched preferred skills:** {', '.join(r.matched_preferred) or 'none'}",
            "",
            "**Evidence (exact resume lines):**",
            "",
        ]
        for skill, line in r.evidence.items():
            lines.append(f"- **{skill}**: “{line}”")
        if not r.evidence:
            lines.append("- _No skill evidence found._")
        lines += [
            "",
            "**Strengths:**",
            "",
        ]
        lines += [f"- {s}" for s in r.strengths]
        lines += ["", "**Gaps:**", ""]
        lines += [f"- {g}" for g in r.gaps]
        lines += [
            "",
            "**Not considered in this score:** "
            + ", ".join(NOT_CONSIDERED)
            + ". The score uses only skills, experience, education and JD keyword overlap.",
            "",
            "---",
            "",
        ]
    return "\n".join(lines)


def render_json(results: list[Screening], threshold: float = 65.0) -> str:
    return json.dumps(
        {
            "role": results[0].job.title if results else None,
            "threshold": threshold,
            "shortlisted": sum(1 for r in results if r.score >= threshold),
            "results": [r.to_dict() for r in results],
        },
        indent=2,
    )
