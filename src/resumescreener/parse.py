"""Parsing: resumes and job descriptions into structured, scored inputs.

Everything here is deterministic and text-only. No model, no network, no
guessing: a skill counts only when its exact phrase appears, years of
experience come from explicit claims or dated ranges, and education comes
from explicit degree words. Fields the parser cannot find stay empty and
are reported as such instead of being invented.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .taxonomy import EDUCATION_LEVELS, SKILL_ALIASES

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
_YEARS_CLAIM_RE = re.compile(
    r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp\b)", re.I
)
_YEARS_BARE_RE = re.compile(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+experience", re.I)
_RANGE_RE = re.compile(r"\b(19|20)\d{2}\s*(?:[-–—]|to)\s*((?:19|20)\d{2}|present|current|now)\b", re.I)
_MIN_YEARS_RE = re.compile(
    r"(?:minimum|min\.?|at least|atleast|requires?|required|with)\s+"
    r"(?:of\s+)?(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)", re.I
)
_MIN_YEARS_ALT_RE = re.compile(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+of\s+experience\s+(?:required|needed|minimum)", re.I)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _find_phrase(normalized: str, phrase: str) -> bool:
    """Whole-phrase match on word boundaries (so 'java' never matches 'javascript')."""
    pattern = r"(?<![a-z0-9+#.])" + re.escape(phrase) + r"(?![a-z0-9+#.])"
    return re.search(pattern, normalized) is not None


def find_skills(text: str) -> set[str]:
    """Canonical skills whose phrase appears in the text."""
    normalized = _normalize(text)
    found = set()
    for canonical, aliases in SKILL_ALIASES.items():
        if any(_find_phrase(normalized, alias) for alias in aliases):
            found.add(canonical)
    return found


def skill_evidence(text: str, skill: str) -> str:
    """First resume line containing the skill — the evidence for the score."""
    for line in text.splitlines():
        if _find_phrase(_normalize(line), skill) or any(
            _find_phrase(_normalize(line), alias)
            for alias in SKILL_ALIASES.get(skill, [skill])
        ):
            return line.strip()
    return ""


def extract_years_experience(text: str) -> float | None:
    """Years of experience, or None when the resume never states any."""
    claims = [float(m.group(1)) for m in _YEARS_CLAIM_RE.finditer(text)]
    if claims:
        return max(claims)
    # Fall back to summing dated employment ranges (present = 2026).
    total = 0.0
    for m in _RANGE_RE.finditer(text):
        start = int(m.group(0)[:4])
        end_raw = m.group(2).lower()
        end = 2026 if end_raw in ("present", "current", "now") else int(end_raw)
        if end > start:
            total += end - start
    return total if total > 0 else None


def extract_education(text: str) -> tuple[int, str] | None:
    """Highest education level found: (level 1-5, label), or None."""
    normalized = _normalize(text)
    best: tuple[int, str] | None = None
    for level, label, keywords in EDUCATION_LEVELS:
        if any(_find_phrase(normalized, kw) for kw in keywords):
            if best is None or level > best[0]:
                best = (level, label)
    return best


@dataclass
class Resume:
    name: str
    email: str | None
    phone: str | None
    skills: set[str] = field(default_factory=set)
    years_experience: float | None = None
    education: tuple[int, str] | None = None
    text: str = ""
    lines: list[str] = field(default_factory=list)

    @property
    def education_label(self) -> str:
        return self.education[1] if self.education else "Not stated"


def parse_resume(text: str) -> Resume:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    name = lines[0] if lines else "Unnamed candidate"
    email_m = _EMAIL_RE.search(text)
    phone_m = _PHONE_RE.search(text)
    return Resume(
        name=name,
        email=email_m.group(0) if email_m else None,
        phone=phone_m.group(0) if phone_m else None,
        skills=find_skills(text),
        years_experience=extract_years_experience(text),
        education=extract_education(text),
        text=text,
        lines=lines,
    )


@dataclass
class JobDescription:
    title: str
    required_skills: set[str] = field(default_factory=set)
    preferred_skills: set[str] = field(default_factory=set)
    min_years: float | None = None
    min_education: tuple[int, str] | None = None
    keywords: set[str] = field(default_factory=set)
    text: str = ""

    @property
    def all_skills(self) -> set[str]:
        return self.required_skills | self.preferred_skills


_SECTION_HEADERS = {
    "required": ("required", "must have", "must-have", "requirements", "what you need", "qualifications"),
    "preferred": ("preferred", "nice to have", "nice-to-have", "bonus", "plus", "desirable"),
    "education": ("education",),
    "experience": ("experience",),
}


def _section_of(line: str) -> str | None:
    low = line.strip().lower().rstrip(":")
    for section, headers in _SECTION_HEADERS.items():
        if low in headers or low.startswith(headers):
            return section
    return None


def parse_job_description(text: str) -> JobDescription:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = lines[0] if lines else "Untitled role"
    required: set[str] = set()
    preferred: set[str] = set()
    section: str | None = None
    for line in lines[1:]:
        found = _section_of(line)
        if found is not None:
            section = found
            continue
        skills = find_skills(line)
        if section == "preferred":
            preferred |= skills
        else:
            required |= skills
    # A JD with no sections at all: every skill mentioned is required.
    if section is None and not required and not preferred:
        required = find_skills(text)
    preferred -= required

    min_years: float | None = None
    m = _MIN_YEARS_RE.search(text) or _MIN_YEARS_ALT_RE.search(text)
    if m:
        min_years = float(m.group(1))
    min_education = extract_education(text)

    from .taxonomy import STOPWORDS

    words = set(re.findall(r"[a-z][a-z+#]{1,}", text.lower()))
    keywords = {w for w in words if w not in STOPWORDS and len(w) > 2}
    return JobDescription(
        title=title,
        required_skills=required,
        preferred_skills=preferred,
        min_years=min_years,
        min_education=min_education,
        keywords=keywords,
        text=text,
    )
