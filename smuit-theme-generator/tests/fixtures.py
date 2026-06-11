# MIT License · Copyright (c) 2026 wimwian
"""A small, self-contained input used across the test suite."""

SAMPLE = """
[hues]
black = "oklch(0 0 0)"
white = "oklch(1 0 0)"
neutral = "oklch(0.5 0 0)"
primary = "oklch(0.66 0.15 232)"
secondary = "oklch(0.62 0.19 328)"
tertiary = "oklch(0.59 0.17 71)"
error = "oklch(0.63 0.26 29)"
warning = "oklch(0.8 0.18 103)"
success = "oklch(0.74 0.25 142)"

[neutral]
page.bg.light = 950
page.bg.dark = 100
page.fg = 100
surface.bg.light = 800
surface.bg.dark = 250
surface.bg.hover.light = 850
surface.bg.hover.dark = 200
surface.fg = 100
surface.border.light = 300
surface.border.bold = 150
surface.readonly = 0.75
surface.disabled = 0.6
surface.elevation = "md"

[palette]
surface.bg.light = 850
surface.bg.hover = 900
surface.fg = 100
surface.border = 300
surface.readonly = 0.75
surface.elevation = "md"

[rag]
surface.bg.light = 850
surface.fg = 100
surface.border = 300

[type]
capitalize = 0
small-caps = 0

[type.display]
weight = 600
width = 0.95
md.size = "36px / 44px"
lg.size = "44px / 60px"

[type.title]
capitalize = 1
small-caps = 1
weight = 600
md.size = "24px / 32px"

[elevation]
sm = "0 1px 8px -2px rgba(0,0,0,0.2)"
"""
