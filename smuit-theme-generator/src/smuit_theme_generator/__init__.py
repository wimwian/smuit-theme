# MIT License · Copyright (c) 2026 wimwian
"""TOML → flat CSS theme generator for @wimwian-org/theme.

Pipeline (each stage is a pure, independently-testable module):

    theme-input.toml ──parse──▶ model ──emit──▶ standard CSS ──minify──▶ minified CSS
                      (model)            (emit)               (emit)

  * ramp   — a step (0..1000) on a hue → a gamut-mapped oklch color (coloraide).
  * model  — parse the TOML into colour tokens + state alphas, per group.
  * emit   — render the model to readable + minified CSS.
  * cli    — read theme-input.toml, write output.css (standard) + output.min.css (consumed).
"""

from .cli import build, main
from .emit import minify, render
from .model import GROUPS, ColorToken, Group, RefToken, StateAlpha, parse
from .ramp import fmt, mirror, tone

__all__ = [
    "tone",
    "fmt",
    "mirror",
    "parse",
    "Group",
    "ColorToken",
    "StateAlpha",
    "RefToken",
    "GROUPS",
    "render",
    "minify",
    "build",
    "main",
]
