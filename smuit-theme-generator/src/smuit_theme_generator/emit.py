# MIT License · Copyright (c) 2026 wimwian
"""Render a parsed :class:`~smuit_theme_generator.model.Model` to flat CSS.

Output shape (matches the proven light/dark structure):

    :root { … }                                  /* light (default) + theme-independent */
    [data-theme='dark'] { … }                    /* explicit dark override            */
    @media (prefers-color-scheme: dark) {
        :root:not([data-theme='light']) { … }    /* OS dark fallback                  */
    }
    [data-readonly] { … }                        /* state alpha, per theme            */
    [data-theme='dark'] [data-readonly] { … }
    @media (prefers-color-scheme: dark) { :root:not([data-theme='light']) [data-readonly] { … } }

Every colour is a baked ``oklch()`` literal — no runtime ``color-mix()`` /
``light-dark()``. :func:`render` returns ``(standard, minified)``.
"""

from __future__ import annotations

import re

from .model import CORE_ROLES, Model, Group
from .ramp import fmt, tone

_BANNER = """/* ============================================================================
 *   GENERATED — DO NOT EDIT.  Produced from theme-input.toml by smuit-theme-generator.
 *   This STANDARD build is readable + inert: the package consumes output.min.css,
 *   so editing this file has no effect. Change theme-input.toml and regenerate.
 * ============================================================================ */"""

_LIGHT = "light"
_DARK = "dark"


def var_name(path: tuple[str, ...], prefix: str | None) -> str:
    """Dotted ``path`` → CSS custom property; the hue rides after the first segment.

    >>> var_name(("page", "bg"), None)
    '--page-bg'
    >>> var_name(("surface", "bg", "hover"), "primary")
    '--surface-primary-bg-hover'
    """
    segs = list(path)
    if prefix:
        segs = [segs[0], prefix, *segs[1:]]
    return "--" + "-".join(segs)


def _decl(name: str, value: str) -> str:
    return f"    {name}: {value};"


def _pct(ratio: float) -> str:
    """A width ratio → compact CSS percentage: 0.95→'95%', 1.0062→'100.62%'."""
    pct = round(ratio * 100, 4)
    body = str(int(pct)) if pct == int(pct) else f"{pct:.4f}".rstrip("0").rstrip(".")
    return f"{body}%"


def _color_decls(groups: tuple[Group, ...], theme: str) -> list[str]:
    """Every group's colour tokens for one theme (light|dark), as declarations."""
    lines: list[str] = []
    for g in groups:
        if not g.colors:
            continue
        lines.append(f"    /* {g.prefix or g.name} */")
        for tok in g.colors:
            step = tok.light if theme == _LIGHT else tok.dark
            lines.append(_decl(var_name(tok.path, g.prefix), fmt(tone(g.base, step))))
    return lines


def _state_decls(groups: tuple[Group, ...], state: str, theme: str) -> list[str]:
    """For one state (readonly|disabled) + theme: re-tint each group's core surfaces."""
    lines: list[str] = []
    for g in groups:
        alpha = next((s.alpha for s in g.states if s.name == state), None)
        if alpha is None:
            continue
        parent = next((s.parent for s in g.states if s.name == state), ())
        core = [
            t
            for t in g.colors
            if len(t.path) == len(parent) + 1 and t.path[:-1] == parent and t.path[-1] in CORE_ROLES
        ]
        if not core:
            continue
        lines.append(f"    /* {g.prefix or g.name} */")
        for tok in core:
            step = tok.light if theme == _LIGHT else tok.dark
            lines.append(_decl(var_name(tok.path, g.prefix), fmt(tone(g.base, step), alpha)))
    return lines


def _primitive_decls(model: Model) -> list[str]:
    """Theme-independent tokens: hue primitives, fonts, type ramps, elevation."""
    lines: list[str] = ["    /* hues */"]
    for name, value in model.hues.items():
        lines.append(_decl(f"--{name}", fmt(tone(value, 500))))

    if model.fonts:
        lines.append("    /* fonts */")
        for key, value in model.fonts:
            lines.append(_decl(f"--font-{key}", value))

    if model.elevation:
        lines.append("    /* elevation */")
        for label, shadow in model.elevation:
            lines.append(_decl(f"--elevation-{label}", shadow))
    return lines


def _type_utilities(model: Model) -> list[str]:
    """Typographic roles as Tailwind ``@utility <role>-<label>`` blocks.

    Each block applies the resolved values directly — ``font-size`` / ``line-height``
    / ``font-weight`` (per role) / ``font-stretch`` (per-role ratio as a %) — rather than
    emitting ``--text-*`` custom properties.

    Width is emitted as ``font-stretch`` (not the newer ``font-width`` alias): Lightning
    CSS — Tailwind v4's engine — drops ``font-width`` as unrecognised, which would leave
    the width inert in the browser.
    """
    out: list[str] = []
    for ramp in model.type:
        for label, size, line_height in ramp.steps:
            body = [_decl("font-size", size)]
            if line_height:
                body.append(_decl("line-height", line_height))
            body.append(_decl("font-weight", str(ramp.weight)))
            if ramp.width is not None:
                body.append(_decl("font-stretch", _pct(ramp.width)))
            if ramp.capitalize:
                body.append(_decl("text-transform", "capitalize"))
            if ramp.small_caps:
                body.append(_decl("font-variant-caps", "small-caps"))
            out += _block(f"@utility {ramp.role}-{label}", body)
    return out


def _ref_decls(groups: tuple[Group, ...]) -> list[str]:
    """Theme-independent reference tokens (e.g. surface shadow → --elevation-*)."""
    lines: list[str] = []
    for g in groups:
        if not g.refs:
            continue
        lines.append(f"    /* {g.prefix or g.name} */")
        for ref in g.refs:
            lines.append(_decl(var_name(ref.path, g.prefix), ref.value))
    return lines


def _state_names(groups: tuple[Group, ...]) -> list[str]:
    """Distinct state names across groups, in first-seen order."""
    seen: list[str] = []
    for g in groups:
        for s in g.states:
            if s.name not in seen:
                seen.append(s.name)
    return seen


def _block(selector: str, body: list[str]) -> list[str]:
    return [f"{selector} {{", *body, "}", ""]


def render(model: Model) -> tuple[str, str]:
    """Render ``model`` to ``(standard_css, minified_css)``."""
    groups = model.groups
    out: list[str] = [_BANNER, ""]

    # color-scheme keeps native controls/scrollbars in step with the theme.
    out += [
        "/* color-scheme keeps native form controls / scrollbars in step with the theme */",
        ":root { color-scheme: light; }",
        "[data-theme='light'] { color-scheme: light; }",
        "[data-theme='dark'] { color-scheme: dark; }",
        "@media (prefers-color-scheme: dark) { :root:not([data-theme='light']) { color-scheme: dark; } }",
        "",
    ]

    # ── Light (default) + theme-independent primitives ─────────────────────────
    out += ["/* ── Light (default) + primitives ─────────────────────────────── */"]
    refs = _ref_decls(groups)
    root_body = _primitive_decls(model) + [""] + _color_decls(groups, _LIGHT)
    if refs:
        root_body += ["", "    /* shadow refs (theme-independent) */", *refs]
    out += _block(":root", root_body)

    # ── Dark (explicit toggle) ─────────────────────────────────────────────────
    out += ["/* ── Dark — explicit [data-theme='dark'] ─────────────────────────── */"]
    out += _block("[data-theme='dark']", _color_decls(groups, _DARK))

    # ── Dark (OS fallback) ─────────────────────────────────────────────────────
    out += ["/* ── Dark — prefers-color-scheme fallback ────────────────────────── */"]
    dark_body = _color_decls(groups, _DARK)
    out += [
        "@media (prefers-color-scheme: dark) {",
        "  :root:not([data-theme='light']) {",
        *[("  " + line if line else line) for line in dark_body],
        "  }",
        "}",
        "",
    ]

    # ── State alphas (readonly / disabled), per theme ──────────────────────────
    for state in _state_names(groups):
        light = _state_decls(groups, state, _LIGHT)
        dark = _state_decls(groups, state, _DARK)
        if not light and not dark:
            continue
        out += [f"/* ── State: {state} (core surfaces at the state alpha) ─────────── */"]
        out += _block(f"[data-{state}]", light)
        out += _block(f"[data-theme='dark'] [data-{state}]", dark)
        out += [
            "@media (prefers-color-scheme: dark) {",
            f"  :root:not([data-theme='light']) [data-{state}] {{",
            *[("  " + line if line else line) for line in dark],
            "  }",
            "}",
            "",
        ]

    # ── Typography utilities (theme-independent @utility classes) ──────────────
    if model.type:
        out += ["/* ── Typography utilities ─────────────────────────────────────── */"]
        out += _type_utilities(model)

    standard = "\n".join(out).rstrip() + "\n"
    return standard, minify(standard)


def minify(css: str) -> str:
    """Collapse CSS to one line. Value-safe: single spaces inside ``oklch(...)`` /
    shadows survive; only structural whitespace around ``{ } ; , :`` is dropped.

    >>> minify(".a {\\n  color: red;\\n}")
    '.a{color:red}'
    """
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)  # strip comments
    css = re.sub(r"\s+", " ", css)  # collapse whitespace runs to a single space
    css = re.sub(r"\s*([{};,])\s*", r"\1", css)  # drop space around { } ; ,
    css = re.sub(r":\s+", ":", css)  # drop space after a colon
    css = css.replace(";}", "}")  # drop the redundant final semicolon
    return css.strip()
