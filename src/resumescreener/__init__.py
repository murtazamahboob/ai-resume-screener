"""AI Resume Screener — explainable, offline resume screening.

Scores every resume against a job description with a transparent,
weighted rubric and prints the evidence behind every point.
"""
from __future__ import annotations

from .parse import JobDescription, Resume, parse_job_description, parse_resume
from .report import render_json, render_markdown
from .score import rank, screen

__all__ = [
    "Resume",
    "JobDescription",
    "parse_resume",
    "parse_job_description",
    "screen",
    "rank",
    "render_markdown",
    "render_json",
]

__version__ = "1.0.0"
