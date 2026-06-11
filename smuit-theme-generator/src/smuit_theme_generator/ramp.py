# MIT License · Copyright (c) 2026 wimwian
"""Tonal ramp + oklch formatting — the color maths, coloraide-backed.

A *step* is a number 0..1000 on a hue's ramp, tracking lightness like the L of
black (0) and white (1):

    0 ───────── 500 ───────── 1000
   black      base hue       white

The color at a step is a linear oklch interpolation toward the black/white pole
(``|step-500|/500`` of the way), then gamut-mapped into sRGB so a browser paints
exactly what we computed. So a *high* step is a light colour, and a *low* step is
dark — which is why a token's light value mirrors to ``1000 - light`` for dark.
Steps are never enumerated up front — any step is computed (and memoised) on demand.
"""

from __future__ import annotations

from functools import lru_cache
from math import isnan, nan

from coloraide import Color

# Ramp poles. White / black anchor the two ends of every hue's ramp. Their hue is
# left UNDEFINED (NaN), so interpolation carries the base hue instead of mixing
# toward an arbitrary 0° — a dark/light step keeps its hue, just loses lightness.
_WHITE = Color("oklch", [1, 0, nan])
_BLACK = Color("oklch", [0, 0, nan])


def mirror(step: int) -> int:
    """The light↔dark mirror of a step: 0↔1000, 100↔900, 250↔750, 500↔500.

    >>> mirror(100), mirror(800), mirror(500)
    (900, 200, 500)
    """
    return 1000 - step


@lru_cache(maxsize=8192)
def tone(base: str, step: int) -> Color:
    """Color at ``step`` on ``base``'s ramp, gamut-mapped into sRGB.

    ``base`` is any CSS color string (typically an ``oklch(...)``). 500 returns
    the base hue itself; below 500 darkens toward black, above lightens toward
    white. Memoised — the same (base, step) is computed once.

    >>> round(tone("oklch(0.5 0 0)", 100)["lightness"], 4)  # 80% toward black
    0.1
    >>> round(tone("oklch(0.5 0 0)", 900)["lightness"], 4)  # 80% toward white
    0.9
    """
    b = Color(base).convert("oklch")
    if step == 500:
        c = b.clone()
    elif step < 500:
        # position 0..1 from black(0) to base(500)
        c = Color(Color.interpolate([_BLACK, b], space="oklch")(step / 500))
    else:
        # position 0..1 from base(500) to white(1000)
        c = Color(Color.interpolate([b, _WHITE], space="oklch")((step - 500) / 500))
    c = c.convert("oklch")
    # CSS Color 4 "oklch-chroma" gamut mapping: reduce chroma until in sRGB.
    c.fit("srgb")
    return c


def _num(x: float) -> str:
    """Compact CSS number: 232.0→'232', 0.1500→'0.15', 0.1216→'0.1216', 0→'0'."""
    x = round(x, 4)
    if x == int(x):
        return str(int(x))
    return f"{x:.4f}".rstrip("0").rstrip(".")


def fmt(c: Color, alpha: float = 1.0) -> str:
    """Serialize an oklch ``Color`` to a compact ``oklch(L C H[ / A])`` string.

    L is clamped to [0,1], C floored at 0, H normalised to [0,360); the alpha is
    appended only when < 1 (so opaque colors stay terse).

    >>> fmt(Color("oklch", [0.5, 0, 0]))
    'oklch(0.5 0 0)'
    >>> fmt(Color("oklch", [0.5, 0.1, 120]), 0.75)
    'oklch(0.5 0.1 120 / 0.75)'
    """
    c = c.convert("oklch")
    lightness = max(0.0, min(1.0, c["lightness"]))
    chroma = max(0.0, c["chroma"])
    hue = c["hue"]
    hue = 0.0 if isnan(hue) else hue % 360
    body = f"{_num(lightness)} {_num(chroma)} {_num(hue)}"
    if alpha >= 1:
        return f"oklch({body})"
    return f"oklch({body} / {_num(round(alpha, 3))})"
