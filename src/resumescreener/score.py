"""Scoring: transparent, weighted, fully explainable.

Weights (out of 100) — every point is traceable to one criterion:
  Skills      45  (40 required-skill coverage + 5 preferred-skill coverage)
  Experience  25  (years vs the JD minimum)
  Education   15  (level vs the JD minimum)
  Keywords    15  (overlap of the JD's other content words with the resume)

Nothing else ever enters the score. Name, email, phone, location, photo,
age, gender and university prestige are never read by the scorer — the
report says so explicitly, so a candidate can audit exactly what counted.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .parse import JobDescription, Resume, skill_evidence
from .taxonomy import STOPWORDS

WEIGHTS = {"skills": 45.0, "experience": 25.0, "education": 15.0, "keywords": 15.0}

VERDICTS = [
    (80, "Strong match"),
    (65, "Good fit"),
    (50, "Borderline"),
    (0, "Not a match"),
]

# Fields the scorer never uses — printed in every report.
NOT_CONSIDERED = [
    "name", "email", "phone", "location", "photo",
    "age", "gender", "university prestige",
]


@dataclass
class Criterion:
    name: str
    earned: float
    maximum: float
    reason: str

    @property
    def pct(self) -> float:
        return round(100 * self.earned / self.maximum, 1) if self.maximum else 0.0


@dataclass
class Screening:
    resume: Resume
    job: JobDescription
    score: float
    verdict: str
    criteria: list[Criterion] = field(default_factory=list)
    matched_required: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    matched_preferred: list[str] = field(default_factory=list)
    evidence: dict[str, str] = field(default_factory=dict)
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "candidate": self.resume.name,
            "score": self.score,
            "verdict": self.verdict,
            "criteria": [
                {"name": c.name, "earned": c.earned, "max": c.maximum, "reason": c.reason}
                for c in self.criteria
            ],
            "matched_required_skills": self.matched_required,
            "missing_required_skills": self.missing_required,
            "matched_preferred_skills": self.matched_preferred,
            "evidence": self.evidence,
            "strengths": self.strengths,
            "gaps": self.gaps,
            "not_considered": NOT_CONSIDERED,
        }


def _verdict(score: float) -> str:
    for threshold, label in VERDICTS:
        if score >= threshold:
            return label
    return "Not a match"


def _score_skills(resume: Resume, job: JobDescription) -> Criterion:
    matched_req = sorted(job.required_skills & resume.skills)
    missing_req = sorted(job.required_skills - resume.skills)
    matched_pref = sorted(job.preferred_skills & resume.skills)
    req_cov = len(matched_req) / len(job.required_skills) if job.required_skills else 1.0
    pref_cov = len(matched_pref) / len(job.preferred_skills) if job.preferred_skills else 0.0
    earned = round(40 * req_cov + 5 * pref_cov, 1)
    if job.required_skills:
        reason = (
            f"{len(matched_req)}/{len(job.required_skills)} required skills matched"
            + (f"; {len(matched_pref)}/{len(job.preferred_skills)} preferred matched"
               if job.preferred_skills else "")
        )
    else:
        reason = "JD lists no required skills — skills criterion neutral"
    return Criterion("Skills", earned, 45.0, reason), matched_req, missing_req, matched_pref


def _score_experience(resume: Resume, job: JobDescription) -> Criterion:
    years = resume.years_experience
    if job.min_years is None:
        if years is None:
            return Criterion("Experience", 12.5, 25.0, "Neither JD nor resume states years — neutral half marks")
        earned = round(25 * min(years / 5.0, 1.0), 1)
        return Criterion("Experience", earned, 25.0, f"{years:g} years stated; no minimum in JD (scored vs 5 years)")
    if years is None:
        return Criterion("Experience", 0.0, 25.0, f"No experience stated; JD asks for {job.min_years:g}+ years")
    earned = round(25 * min(years / job.min_years, 1.0), 1)
    return Criterion(
        "Experience", earned, 25.0,
        f"{years:g} years vs {job.min_years:g}+ required"
        + (" — meets requirement" if years >= job.min_years else " — shortfall"),
    )


def _score_education(resume: Resume, job: JobDescription) -> Criterion:
    if job.min_education is None:
        return Criterion("Education", 15.0, 15.0, "JD states no education minimum")
    if resume.education is None:
        return Criterion("Education", 7.0, 15.0, "No education stated on resume — neutral, not penalised as a fail")
    diff = resume.education[0] - job.min_education[0]
    if diff >= 0:
        return Criterion("Education", 15.0, 15.0,
                         f"{resume.education[1]} meets {job.min_education[1]} requirement")
    if diff == -1:
        return Criterion("Education", 8.0, 15.0,
                         f"{resume.education[1]} is one level below {job.min_education[1]}")
    return Criterion("Education", 3.0, 15.0,
                     f"{resume.education[1]} is two or more levels below {job.min_education[1]}")


def _score_keywords(resume: Resume, job: JobDescription) -> Criterion:
    resume_words = set(re.findall(r"[a-z][a-z+#]{1,}", resume.text.lower()))
    resume_words = {w for w in resume_words if w not in STOPWORDS}
    overlap = job.keywords & resume_words
    ratio = len(overlap) / len(job.keywords) if job.keywords else 0.0
    earned = round(15 * ratio, 1)
    return Criterion("Keywords", earned, 15.0,
                     f"{len(overlap)}/{len(job.keywords)} JD content words appear in the resume")


def screen(resume: Resume, job: JobDescription) -> Screening:
    skills_c, matched_req, missing_req, matched_pref = _score_skills(resume, job)
    exp_c = _score_experience(resume, job)
    edu_c = _score_education(resume, job)
    kw_c = _score_keywords(resume, job)
    criteria = [skills_c, exp_c, edu_c, kw_c]
    score = round(sum(c.earned for c in criteria), 1)

    evidence = {s: skill_evidence(resume.text, s) for s in matched_req + matched_pref}

    strengths: list[str] = []
    gaps: list[str] = []
    if matched_req:
        strengths.append(f"Matches {len(matched_req)} required skills: {', '.join(matched_req)}")
    if resume.years_experience is not None and job.min_years is not None \
            and resume.years_experience >= job.min_years:
        strengths.append(f"Meets experience requirement ({resume.years_experience:g} vs {job.min_years:g}+ years)")
    if resume.education is not None and job.min_education is not None \
            and resume.education[0] >= job.min_education[0]:
        strengths.append(f"Meets education requirement ({resume.education[1]})")
    if matched_pref:
        strengths.append(f"Brings preferred skills: {', '.join(matched_pref)}")
    if missing_req:
        gaps.append(f"Missing required skills: {', '.join(missing_req)}")
    if job.min_years is not None:
        if resume.years_experience is None:
            gaps.append("No years of experience stated on resume")
        elif resume.years_experience < job.min_years:
            gaps.append(f"Experience shortfall: {resume.years_experience:g} vs {job.min_years:g}+ years required")
    if resume.education is None and job.min_education is not None:
        gaps.append("No education stated on resume")
    if not strengths:
        strengths.append("No criterion fully met — see gaps")
    if not gaps:
        gaps.append("No gaps found against this JD")

    return Screening(
        resume=resume, job=job, score=score, verdict=_verdict(score),
        criteria=criteria, matched_required=matched_req, missing_required=missing_req,
        matched_preferred=matched_pref, evidence=evidence,
        strengths=strengths, gaps=gaps,
    )


def rank(resumes: list[Resume], job: JobDescription) -> list[Screening]:
    """Score every resume; highest first, name breaks ties deterministically."""
    results = [screen(r, job) for r in resumes]
    return sorted(results, key=lambda s: (-s.score, s.resume.name.lower()))
