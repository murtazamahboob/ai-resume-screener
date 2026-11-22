"""Skill taxonomy: canonical skill -> aliases matched in text.

Matching is case-insensitive, whole-phrase, and deterministic. Aliases
collapse common variants (e.g. "postgres" -> "postgresql") onto one
canonical skill so a resume is never double-credited for the same skill.
"""
from __future__ import annotations

SKILL_ALIASES: dict[str, list[str]] = {
    "python": ["python", "python3"],
    "django": ["django"],
    "flask": ["flask"],
    "fastapi": ["fastapi"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "react.js", "reactjs"],
    "node.js": ["node.js", "nodejs", "node"],
    "java": ["java"],
    "c++": ["c++"],
    "c#": ["c#", "csharp"],
    "go": ["go", "golang"],
    "rust": ["rust"],
    "sql": ["sql"],
    "postgresql": ["postgresql", "postgres"],
    "mysql": ["mysql"],
    "sqlite": ["sqlite"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "rest api": ["rest api", "rest apis", "restful api", "restful apis"],
    "graphql": ["graphql"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud"],
    "git": ["git"],
    "github": ["github"],
    "ci/cd": ["ci/cd", "ci cd", "continuous integration"],
    "linux": ["linux"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "opencv": ["opencv"],
    "nlp": ["nlp", "natural language processing"],
    "data analysis": ["data analysis"],
    "excel": ["excel"],
    "html": ["html"],
    "css": ["css"],
    "agile": ["agile", "scrum"],
    "testing": ["testing", "unit testing", "pytest", "test-driven development"],
    "terraform": ["terraform"],
    "jenkins": ["jenkins"],
    "airflow": ["airflow", "apache airflow"],
    "spark": ["spark", "apache spark"],
    "kafka": ["kafka", "apache kafka"],
    "elasticsearch": ["elasticsearch"],
    "figma": ["figma"],
    "photoshop": ["photoshop"],
    "seo": ["seo"],
    "project management": ["project management"],
    "communication": ["communication"],
    "leadership": ["leadership"],
    "problem solving": ["problem solving"],
}

# Education levels, lowest to highest. Each entry: level, keywords.
EDUCATION_LEVELS: list[tuple[int, str, list[str]]] = [
    (1, "High School", ["high school", "high-school", "ged", "matric", "intermediate"]),
    (2, "Associate / Diploma", ["associate", "diploma"]),
    (3, "Bachelor's", ["bachelor", "b.sc", "bsc", "b.s.", "bba", "b.e.", "btech", "b.tech"]),
    (4, "Master's", ["master", "m.sc", "msc", "m.s.", "mba", "m.tech", "mtech"]),
    (5, "PhD / Doctorate", ["phd", "ph.d", "doctorate", "doctoral"]),
]

# Words ignored when measuring keyword overlap (skills are scored separately).
STOPWORDS = frozenset(
    "a an the and or of to in for with on at by from as is are was were be been "
    "we you our your they he she it its this that these those will would can could "
    "should must may might have has had do does did not no yes if then than so such "
    "more most other some any all each per via using use used based including include "
    "experience years year strong excellent good team work working ability skills "
    "knowledge understanding developer engineer role position job company looking "
    "join join us apply please".split()
)
