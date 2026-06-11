# MIT License · Copyright (c) 2026 wimwian
import re

from smuit_theme_generator.emit import minify, render, var_name
from smuit_theme_generator.model import parse

from .fixtures import SAMPLE


def test_var_name_inserts_hue_after_first_segment():
    assert var_name(("page", "bg"), None) == "--page-bg"
    assert var_name(("surface", "bg", "hover"), "primary") == "--surface-primary-bg-hover"
    assert var_name(("surface", "border", "bold"), "error") == "--surface-error-border-bold"


def test_render_emits_light_dark_and_state_layers():
    std, _ = render(parse(SAMPLE))
    assert ":root {" in std
    assert "[data-theme='dark'] {" in std
    assert "@media (prefers-color-scheme: dark)" in std
    assert "[data-readonly] {" in std
    assert "[data-disabled] {" in std
    assert "[data-theme='dark'] [data-readonly] {" in std


def test_neutral_unprefixed_palette_prefixed():
    std, _ = render(parse(SAMPLE))
    assert "--page-bg:" in std  # neutral, bare
    assert "--surface-primary-bg:" in std  # palette, hue-prefixed
    assert "--surface-error-bg:" in std  # rag


def test_high_step_is_light_low_step_is_dark():
    std, _ = render(parse(SAMPLE))
    # page.bg light step 950 → near-white (L high); the first --page-bg in the file
    # is the light one (:root precedes the dark block).
    light_l = float(re.search(r"--page-bg: oklch\(([0-9.]+)", std).group(1))
    dark_l = float(re.findall(r"--page-bg: oklch\(([0-9.]+)", std)[1])  # dark step 100
    assert light_l > 0.9 > dark_l  # bright in light, dark in dark


def test_state_alpha_applied_to_core_surfaces_only():
    std, _ = render(parse(SAMPLE))
    ro = std.split("[data-readonly] {")[1].split("}")[0]
    assert "--surface-bg:" in ro and "/ 0.75)" in ro
    assert "--surface-fg:" in ro
    assert "--surface-bg-hover:" not in ro  # hover is not a core role


def test_minify_is_one_line_and_value_safe():
    _, mn = render(parse(SAMPLE))
    assert "\n" not in mn
    assert "/* " not in mn  # comments stripped
    assert ";}" not in mn  # redundant trailing semicolons dropped
    assert re.search(r"oklch\([0-9.]+ [0-9.]+ [0-9.]+\)", mn)  # intra-value spaces survive
    assert "[data-theme='dark'] [data-readonly]" in mn  # descendant combinator preserved


def test_shadow_ref_emitted_once_and_theme_independent():
    std, _ = render(parse(SAMPLE))
    # neutral (bare) + palette/rag (prefixed) shadow refs, all pointing at --elevation-md
    assert "--surface-shadow: var(--elevation-md);" in std
    assert "--surface-primary-shadow: var(--elevation-md);" in std
    # theme-independent: appears only in the :root block, not duplicated per dark layer
    assert std.count("--surface-shadow: var(--elevation-md);") == 1


def test_type_emitted_as_utility_blocks_not_tokens():
    std, _ = render(parse(SAMPLE))
    # roles become @utility <role>-<label> blocks applying real properties …
    block = std.split("@utility display-md {")[1].split("}")[0]
    assert "font-size: 36px;" in block
    assert "line-height: 44px;" in block
    assert "font-weight: 600;" in block
    assert "font-stretch: 95%;" in block  # per-role width ratio → %
    # … and no longer --text-* custom properties
    assert "--text-display" not in std


def test_capitalize_and_small_caps_flags_emit_per_role():
    std, _ = render(parse(SAMPLE))
    # title enables both flags
    title = std.split("@utility title-md {")[1].split("}")[0]
    assert "text-transform: capitalize;" in title
    assert "font-variant-caps: small-caps;" in title
    # display inherits the [type] defaults (both off) → neither property
    display = std.split("@utility display-md {")[1].split("}")[0]
    assert "text-transform:" not in display
    assert "font-variant-caps:" not in display


def test_minify_doctest_example():
    assert minify(".a {\n  color: red;\n}") == ".a{color:red}"
