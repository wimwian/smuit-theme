# MIT License · Copyright (c) 2026 wimwian
from coloraide import Color

from smuit_theme_generator.ramp import fmt, mirror, tone


def test_mirror():
    assert mirror(100) == 900
    assert mirror(950) == 50
    assert mirror(500) == 500


def test_ramp_orientation_is_black_to_white():
    # neutral L=0.5: 0 → black(L0), 500 → base(0.5), 1000 → white(L1)
    assert round(tone("oklch(0.5 0 0)", 0)["lightness"], 4) == 0.0
    assert round(tone("oklch(0.5 0 0)", 500)["lightness"], 4) == 0.5
    assert round(tone("oklch(0.5 0 0)", 1000)["lightness"], 4) == 1.0
    # high step = light, low step = dark
    assert round(tone("oklch(0.5 0 0)", 100)["lightness"], 4) == 0.1
    assert round(tone("oklch(0.5 0 0)", 900)["lightness"], 4) == 0.9


def test_tone_keeps_base_hue_when_mixing_with_an_achromatic_pole():
    assert round(tone("oklch(0.66 0.15 232)", 100)["hue"]) == 232
    assert round(tone("oklch(0.66 0.15 232)", 900)["hue"]) == 232


def test_tone_is_gamut_mapped_into_srgb():
    # a wildly out-of-gamut base is pulled back into sRGB
    assert tone("oklch(0.63 0.5 29)", 500).in_gamut("srgb")


def test_fmt_is_compact_and_alpha_only_when_translucent():
    assert fmt(Color("oklch", [0.5, 0, 0])) == "oklch(0.5 0 0)"
    assert fmt(Color("oklch", [1, 0, 0])) == "oklch(1 0 0)"
    assert fmt(Color("oklch", [0.5, 0.1, 120]), 0.75) == "oklch(0.5 0.1 120 / 0.75)"


def test_tone_is_memoised():
    assert tone("oklch(0.5 0 0)", 300) is tone("oklch(0.5 0 0)", 300)
