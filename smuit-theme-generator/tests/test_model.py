# MIT License · Copyright (c) 2026 wimwian
import pytest

from smuit_theme_generator.model import parse

from .fixtures import SAMPLE


def _group(model, **kw):
    return next(g for g in model.groups if all(getattr(g, k) == v for k, v in kw.items()))


def _tok(group, path):
    return next(t for t in group.colors if t.path == path)


def test_explicit_mirror_pair():
    g = _group(parse(SAMPLE), name="neutral")
    bg = _tok(g, ("page", "bg"))
    assert (bg.light, bg.dark) == (950, 100)


def test_scalar_mirrors_to_1000_minus_light():
    g = _group(parse(SAMPLE), name="neutral")
    assert _tok(g, ("surface", "fg")).light == 100
    assert _tok(g, ("surface", "fg")).dark == 900  # 1000 - 100


def test_node_owns_value_and_nests_children():
    g = _group(parse(SAMPLE), name="neutral")
    assert (_tok(g, ("surface", "bg")).light, _tok(g, ("surface", "bg")).dark) == (800, 250)
    assert (_tok(g, ("surface", "bg", "hover")).light, _tok(g, ("surface", "bg", "hover")).dark) == (850, 200)
    assert (_tok(g, ("surface", "border", "bold")).light, _tok(g, ("surface", "border", "bold")).dark) == (150, 850)


def test_value_below_one_is_a_state_alpha_on_the_parent():
    g = _group(parse(SAMPLE), name="neutral")
    states = {s.name: s for s in g.states}
    assert states["readonly"].alpha == 0.75
    assert states["readonly"].parent == ("surface",)
    assert states["disabled"].alpha == 0.6


def test_palette_fans_over_three_hues_with_prefixes():
    palette = [g for g in parse(SAMPLE).groups if g.name == "palette"]
    assert sorted(g.hue for g in palette) == ["primary", "secondary", "tertiary"]
    assert all(g.prefix == g.hue for g in palette)


def test_palette_scalar_with_modifier_resolves_both():
    g = _group(parse(SAMPLE), hue="primary")
    assert (_tok(g, ("surface", "bg")).light, _tok(g, ("surface", "bg")).dark) == (850, 150)
    assert (_tok(g, ("surface", "bg", "hover")).light, _tok(g, ("surface", "bg", "hover")).dark) == (900, 100)


def test_type_and_elevation_parsed():
    m = parse(SAMPLE)
    display = next(r for r in m.type if r.role == "display")
    assert display.weight == 600
    assert ("md", "36px", "44px") in display.steps
    assert ("sm", "0 1px 8px -2px rgba(0,0,0,0.2)") in m.elevation


def test_type_width_captured_not_a_step():
    display = next(r for r in parse(SAMPLE).type if r.role == "display")
    assert display.width == 0.95
    assert "width" not in [s[0] for s in display.steps]


def test_string_elevation_leaf_becomes_a_shadow_ref():
    g = _group(parse(SAMPLE), name="neutral")
    refs = {r.path: r.value for r in g.refs}
    assert refs[("surface", "shadow")] == "var(--elevation-md)"


def test_unknown_string_leaf_raises():
    bad = '[hues]\nneutral = "oklch(0.5 0 0)"\n[neutral]\nsurface.kind = "fancy"\n'
    with pytest.raises(ValueError, match="unknown string reference"):
        parse(bad)


def test_type_skips_non_size_scalar_keys():
    # a `width = 0.95` config key must not become a --text-<role>-width token
    src = '[hues]\nneutral = "oklch(0.5 0 0)"\n[type.display]\nweight = 600\nwidth = 0.95\nmd.size = "36px / 44px"\n'
    display = next(r for r in parse(src).type if r.role == "display")
    assert [s[0] for s in display.steps] == ["md"]


def test_missing_hue_raises():
    bad = '[hues]\nneutral = "oklch(0.5 0 0)"\n[palette]\nsurface.fg = 100\n'
    with pytest.raises(ValueError, match="needs hue 'primary'"):
        parse(bad)


def test_no_hues_raises():
    with pytest.raises(ValueError, match="no \\[hues\\]"):
        parse("[neutral]\nsurface.fg = 100\n")
