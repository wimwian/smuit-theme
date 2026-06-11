# MIT License · Copyright (c) 2026 wimwian
"""CLI: read theme-input.toml → write output.css (standard) + output.min.css (consumed)."""

from __future__ import annotations

import sys
from pathlib import Path

from .emit import render
from .model import parse

# src/smuit_theme_generator/cli.py → <repo>/smuit-theme-generator → <repo>/src/assets
_ASSETS = Path(__file__).resolve().parents[3] / "src" / "assets"


def build(assets: Path = _ASSETS) -> tuple[Path, Path]:
    """Generate both CSS artifacts from ``assets/theme-input.toml`` and return their paths."""
    standard, minified = render(parse((assets / "theme-input.toml").read_text(encoding="utf-8")))
    std_path, min_path = assets / "output.css", assets / "output.min.css"
    std_path.write_text(standard, encoding="utf-8")
    min_path.write_text(minified + "\n", encoding="utf-8")
    return std_path, min_path


def main(argv: list[str] | None = None) -> int:
    std, mn = build()
    print(f"Wrote {std.name} ({std.stat().st_size} B, readable) + {mn.name} ({mn.stat().st_size} B, consumed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
