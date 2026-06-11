# MIT License · Copyright (c) 2026 wimwian
"""Parse the input TOML into a flat, emit-ready model.

The color groups (``[neutral]``, ``[palette]``, ``[rag]``) hold a tree of dotted
keys. Each leaf is one of:

  * an integer step >= 1 -> a color token: ``light = step``, ``dark = 1000 - step``
  * a ``{ light = ..., dark = ... }`` table -> a color token with explicit mirrors
    (a node may ALSO have child keys — e.g. ``surface.bg`` owns ``light``/``dark``
     AND nests ``hover``/``focus`` sub-tokens)
  * a float < 1 -> a *state alpha* on the parent (e.g., readonly)

``[neutral]`` samples the ``neutral`` hue with unprefixed names; ``[palette]`` fans
out over primary/secondary/tertiary and ``[rag]`` over error/warning/success, each
carrying its hue in the token name.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass

# group → the (hue, name-prefix) pairs it expands to. Neutral is unprefixed.
GROUPS: dict[str, list[tuple[str, str | None]]] = {
    "neutral": [("neutral", None)],
    "palette": [("primary", "primary"), ("secondary", "secondary"), ("tertiary", "tertiary")],
    "rag": [("error", "error"), ("warning", "warning"), ("success", "success")],
}

_RESERVED = ("light", "dark")  # a node's own mirror steps (not child tokens)
CORE_ROLES = ("bg", "fg", "border")  # surface roles a state alpha re-tints


@dataclass(frozen=True)
class ColorToken:
    """One color, named by its dotted ``path``, with light/dark ramp steps."""

    path: tuple[str, ...]
    light: int
    dark: int


@dataclass(frozen=True)
class StateAlpha:
    """A state (e.g. readonly) that renders its ``parent``'s core surfaces at ``alpha``."""

    parent: tuple[str, ...]
    name: str
    alpha: float


@dataclass(frozen=True)
class RefToken:
    """A theme-independent token whose value is a ``var(...)`` reference.

    Emitted for string leaves: ``surface.elevation = "md"`` becomes
    ``--surface[-<hue>]-shadow: var(--elevation-md)`` — a surface pointing at a
    named elevation/shadow ramp rather than a baked colour.
    """

    path: tuple[str, ...]
    value: str


@dataclass(frozen=True)
class Group:
    """A resolved color group: one hue + the tokens/states to emit for it."""

    name: str
    hue: str
    base: str  # the hue's oklch string, resolved from [hues]
    prefix: str | None
    colors: tuple[ColorToken, ...]
    states: tuple[StateAlpha, ...]
    refs: tuple[RefToken, ...]


@dataclass(frozen=True)
class TypeRamp:
    """A typographic role: per-label (size, line-height) pairs + a default weight.

    ``width`` is an optional per-role font-width ratio (1.0 = normal), emitted as a
    ``font-width`` percentage. ``capitalize`` / ``small_caps`` are per-role on/off
    flags → ``text-transform: capitalize`` / ``font-variant-caps: small-caps``.
    """

    role: str
    weight: int
    steps: tuple[tuple[str, str, str], ...]  # (label, font-size, line-height)
    width: float | None = None
    capitalize: bool = False
    small_caps: bool = False


def _mirror_of(light: int | None, dark: int | None) -> tuple[int, int]:
    """Resolve a (light, dark) pair, filling a missing side via ``1000 - other``."""
    if light is None and dark is None:  # pragma: no cover - guarded by callers
        raise ValueError("a colour token needs at least one of light/dark")
    if light is None:
        light = 1000 - dark
    if dark is None:
        dark = 1000 - light
    return light, dark


def _walk(
    node: dict,
    path: tuple[str, ...],
    colors: list[ColorToken],
    states: list[StateAlpha],
    refs: list[RefToken],
) -> None:
    """Recursively collect color tokens, state alphas, and refs from a TOML subtree."""
    # A node's OWN value comes from explicit light/dark keys (it may still nest children).
    own_light, own_dark = node.get("light"), node.get("dark")
    if own_light is not None or own_dark is not None:
        light, dark = _mirror_of(own_light, own_dark)
        colors.append(ColorToken(path, light, dark))

    for key, val in node.items():
        if key in _RESERVED:
            continue
        child = path + (key,)
        if isinstance(val, dict):
            _walk(val, child, colors, states, refs)
        elif isinstance(val, bool):
            raise ValueError(f"{'.'.join(child)}: booleans are not valid token values")
        elif isinstance(val, (int, float)):
            if val < 1:
                # < 1 → an alpha applied to the parent's core surfaces (readonly/disabled).
                states.append(StateAlpha(path, key, float(val)))
            else:
                light, dark = _mirror_of(int(val), None)
                colors.append(ColorToken(child, light, dark))
        elif isinstance(val, str):
            # A string leaf is a reference to a named ramp. Only `elevation` is
            # known: it points the surface's shadow at --elevation-<label>.
            if key == "elevation":
                refs.append(RefToken(path + ("shadow",), f"var(--elevation-{val})"))
            else:
                raise ValueError(f"{'.'.join(child)}: unknown string reference {val!r}")
        else:
            raise ValueError(f"{'.'.join(child)}: unexpected value {val!r}")


def _parse_groups(data: dict, hues: dict) -> list[Group]:
    groups: list[Group] = []
    for gname, fan in GROUPS.items():
        gdata = data.get(gname)
        if not gdata:
            continue
        colors: list[ColorToken] = []
        states: list[StateAlpha] = []
        refs: list[RefToken] = []
        _walk(gdata, (), colors, states, refs)
        for hue, prefix in fan:
            if hue not in hues:
                raise ValueError(f"group [{gname}] needs hue '{hue}', missing from [hues]")
            groups.append(Group(gname, hue, hues[hue], prefix, tuple(colors), tuple(states), tuple(refs)))
    return groups


def _parse_type(data: dict) -> list[TypeRamp]:
    """Type roles are tables carrying a ``weight`` + ``<label>.size = "Npx / Mpx"``.

    Accepts them nested under ``[type.<role>]`` or as top-level ``[<role>]`` tables.
    """
    roles: list[TypeRamp] = []
    candidates: dict[str, dict] = {}
    nested = data.get("type")
    # `[type]` scalar entries are defaults every role inherits unless it overrides.
    def_cap = def_sc = False
    if isinstance(nested, dict):
        def_cap = bool(nested.get("capitalize", 0))
        def_sc = bool(nested.get("small-caps", 0))
        candidates.update({k: v for k, v in nested.items() if isinstance(v, dict)})
    candidates.update({k: v for k, v in data.items() if isinstance(v, dict) and "weight" in v})

    meta = ("weight", "width", "capitalize", "small-caps")
    for role, table in candidates.items():
        weight = int(table.get("weight", 400))
        width = float(table["width"]) if "width" in table else None
        capitalize = bool(table["capitalize"]) if "capitalize" in table else def_cap
        small_caps = bool(table["small-caps"]) if "small-caps" in table else def_sc
        steps: list[tuple[str, str, str]] = []
        for label, spec in table.items():
            if label in meta:
                continue
            # Only size specs carry a "<font-size> / <line-height>" string (or a
            # nested {size = "..."}). Skip any other scalar config keys.
            if isinstance(spec, dict):
                if "size" not in spec:
                    continue
                size = spec["size"]
            elif isinstance(spec, str):
                size = spec
            else:
                continue
            font_size, _, line_height = (p.strip() for p in str(size).partition("/"))
            steps.append((label, font_size, line_height))
        roles.append(TypeRamp(role, weight, tuple(steps), width, capitalize, small_caps))
    return roles


@dataclass(frozen=True)
class Model:
    """The whole parsed theme, ready for :func:`smuit_theme_generator.emit.render`."""

    hues: dict[str, str]
    groups: tuple[Group, ...]
    type: tuple[TypeRamp, ...]
    elevation: tuple[tuple[str, str], ...]
    fonts: tuple[tuple[str, str], ...]


def parse(text: str) -> Model:
    """Parse the input TOML text into a :class:`Model`."""
    data = tomllib.loads(text)
    hues = dict(data.get("hues", {}))
    if not hues:
        raise ValueError("input has no [hues]")
    elevation = tuple((k, str(v)) for k, v in data.get("elevation", {}).items())
    fonts = tuple((k, str(v)) for k, v in data.get("fonts", {}).items())
    return Model(
        hues=hues,
        groups=tuple(_parse_groups(data, hues)),
        type=tuple(_parse_type(data)),
        elevation=elevation,
        fonts=fonts,
    )
