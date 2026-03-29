"""
KiCad .kicad_mod footprint file writer.

Generates KiCad footprint files (format version 20260206) from calculated
land pattern dimensions. Handles pads, silkscreen, courtyard, fabrication
layer, paste mask, and 3D model references.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum


# --- Data types for footprint elements ---

class PadShape(Enum):
    ROUNDRECT = "roundrect"
    RECT = "rect"
    CIRCLE = "circle"
    OVAL = "oval"


class PadType(Enum):
    SMD = "smd"
    THT = "thru_hole"
    NPTH = "np_thru_hole"


class PadProperty(Enum):
    NONE = None
    BGA = "pad_prop_bga"
    HEATSINK = "pad_prop_heatsink"
    TESTPOINT = "pad_prop_testpoint"


@dataclass
class Pad:
    number: str
    pad_type: PadType
    shape: PadShape
    x: float
    y: float
    width: float
    height: float
    layers: list[str]
    drill: float | None = None
    roundrect_ratio: float | None = 0.25
    property: PadProperty = PadProperty.NONE


@dataclass
class FpLine:
    x1: float
    y1: float
    x2: float
    y2: float
    layer: str
    width: float


@dataclass
class FpRect:
    x1: float
    y1: float
    x2: float
    y2: float
    layer: str
    width: float
    fill: bool = False


@dataclass
class FpCircle:
    cx: float
    cy: float
    radius: float
    layer: str
    width: float
    fill: bool = False


@dataclass
class FpText:
    text: str
    x: float
    y: float
    layer: str
    font_size: float = 1.0
    font_thickness: float = 0.15
    hide: bool = False


@dataclass
class Model3D:
    path: str
    offset: tuple[float, float, float] = (0, 0, 0)
    scale: tuple[float, float, float] = (1, 1, 1)
    rotate: tuple[float, float, float] = (0, 0, 0)


@dataclass
class Footprint:
    """Complete KiCad footprint definition."""
    name: str
    description: str = ""
    tags: str = ""
    smd: bool = True
    pads: list[Pad] = field(default_factory=list)
    lines: list[FpLine] = field(default_factory=list)
    rects: list[FpRect] = field(default_factory=list)
    circles: list[FpCircle] = field(default_factory=list)
    texts: list[FpText] = field(default_factory=list)
    model: Model3D | None = None
    properties: dict[str, str] = field(default_factory=dict)


# --- Serializer ---

def _fmt(value: float) -> str:
    """Format a float for KiCad output, avoiding unnecessary trailing zeros."""
    # KiCad uses up to 6 decimal places but typically 2-4
    s = f"{value:.6f}".rstrip("0").rstrip(".")
    # Ensure at least one decimal place for clean output
    if "." not in s:
        s += ".0"
    return s


def _indent(level: int) -> str:
    return "\t" * level


def serialize_footprint(fp: Footprint) -> str:
    """Serialize a Footprint to KiCad .kicad_mod format (version 20260206)."""
    lines: list[str] = []
    w = lines.append

    attr = "smd" if fp.smd else "through_hole"

    w(f'(footprint "{fp.name}"')
    w(f"\t(version 20260206)")
    w(f'\t(generator "landforge")')
    w(f'\t(layer "F.Cu")')

    if fp.description:
        # Escape quotes in description
        desc = fp.description.replace('"', "'")
        w(f'\t(descr "{desc}")')

    if fp.tags:
        w(f'\t(tags "{fp.tags}")')

    # Properties
    w(f'\t(property "Reference" "REF**"')
    w(f"\t\t(at 0 -1.5 0)")
    w(f'\t\t(layer "F.SilkS")')
    w(f"\t\t(effects")
    w(f"\t\t\t(font")
    w(f"\t\t\t\t(size 1 1)")
    w(f"\t\t\t\t(thickness 0.15)")
    w(f"\t\t\t)")
    w(f"\t\t)")
    w(f"\t)")

    w(f'\t(property "Value" "{fp.name}"')
    w(f"\t\t(at 0 1.5 0)")
    w(f'\t\t(layer "F.Fab")')
    w(f"\t\t(effects")
    w(f"\t\t\t(font")
    w(f"\t\t\t\t(size 1 1)")
    w(f"\t\t\t\t(thickness 0.15)")
    w(f"\t\t\t)")
    w(f"\t\t)")
    w(f"\t)")

    for key, value in fp.properties.items():
        w(f'\t(property "{key}" "{value}"')
        w(f"\t\t(at 0 0 0)")
        w(f'\t\t(layer "F.SilkS")')
        w(f"\t\t(hide yes)")
        w(f"\t\t(effects")
        w(f"\t\t\t(font")
        w(f"\t\t\t\t(size 1 1)")
        w(f"\t\t\t\t(thickness 0.15)")
        w(f"\t\t\t)")
        w(f"\t\t)")
        w(f"\t)")

    w(f"\t(attr {attr})")
    w(f"\t(duplicate_pad_numbers_are_jumpers no)")

    # Lines
    for line in fp.lines:
        w(f"\t(fp_line")
        w(f"\t\t(start {_fmt(line.x1)} {_fmt(line.y1)})")
        w(f"\t\t(end {_fmt(line.x2)} {_fmt(line.y2)})")
        w(f"\t\t(stroke")
        w(f"\t\t\t(width {_fmt(line.width)})")
        w(f"\t\t\t(type solid)")
        w(f"\t\t)")
        w(f'\t\t(layer "{line.layer}")')
        w(f"\t)")

    # Rectangles
    for rect in fp.rects:
        w(f"\t(fp_rect")
        w(f"\t\t(start {_fmt(rect.x1)} {_fmt(rect.y1)})")
        w(f"\t\t(end {_fmt(rect.x2)} {_fmt(rect.y2)})")
        w(f"\t\t(stroke")
        w(f"\t\t\t(width {_fmt(rect.width)})")
        w(f"\t\t\t(type solid)")
        w(f"\t\t)")
        fill = "yes" if rect.fill else "no"
        w(f"\t\t(fill {fill})")
        w(f'\t\t(layer "{rect.layer}")')
        w(f"\t)")

    # Circles
    for circle in fp.circles:
        end_x = circle.cx + circle.radius
        w(f"\t(fp_circle")
        w(f"\t\t(center {_fmt(circle.cx)} {_fmt(circle.cy)})")
        w(f"\t\t(end {_fmt(end_x)} {_fmt(circle.cy)})")
        w(f"\t\t(stroke")
        w(f"\t\t\t(width {_fmt(circle.width)})")
        w(f"\t\t\t(type solid)")
        w(f"\t\t)")
        fill = "yes" if circle.fill else "no"
        w(f"\t\t(fill {fill})")
        w(f'\t\t(layer "{circle.layer}")')
        w(f"\t)")

    # Texts (user text, e.g., ${REFERENCE} on fab layer)
    for text in fp.texts:
        w(f'\t(fp_text user "{text.text}"')
        w(f"\t\t(at {_fmt(text.x)} {_fmt(text.y)} 0)")
        w(f'\t\t(layer "{text.layer}")')
        w(f"\t\t(effects")
        w(f"\t\t\t(font")
        w(f"\t\t\t\t(size {_fmt(text.font_size)} {_fmt(text.font_size)})")
        w(f"\t\t\t\t(thickness {_fmt(text.font_thickness)})")
        w(f"\t\t\t)")
        w(f"\t\t)")
        w(f"\t)")

    # Pads
    for pad in fp.pads:
        shape = pad.shape.value
        ptype = pad.pad_type.value
        layers_str = " ".join(f'"{l}"' for l in pad.layers)

        w(f'\t(pad "{pad.number}" {ptype} {shape}')
        w(f"\t\t(at {_fmt(pad.x)} {_fmt(pad.y)})")
        w(f"\t\t(size {_fmt(pad.width)} {_fmt(pad.height)})")
        w(f"\t\t(layers {layers_str})")

        if pad.shape == PadShape.ROUNDRECT and pad.roundrect_ratio is not None:
            w(f"\t\t(roundrect_rratio {_fmt(pad.roundrect_ratio)})")

        if pad.drill is not None:
            w(f"\t\t(drill {_fmt(pad.drill)})")

        if pad.property != PadProperty.NONE:
            w(f"\t\t({pad.property.value})")

        w(f"\t)")

    # Embedded fonts
    w(f"\t(embedded_fonts no)")

    # 3D model
    if fp.model:
        m = fp.model
        w(f'\t(model "{m.path}"')
        w(f"\t\t(offset")
        w(f"\t\t\t(xyz {_fmt(m.offset[0])} {_fmt(m.offset[1])} {_fmt(m.offset[2])})")
        w(f"\t\t)")
        w(f"\t\t(scale")
        w(f"\t\t\t(xyz {_fmt(m.scale[0])} {_fmt(m.scale[1])} {_fmt(m.scale[2])})")
        w(f"\t\t)")
        w(f"\t\t(rotate")
        w(f"\t\t\t(xyz {_fmt(m.rotate[0])} {_fmt(m.rotate[1])} {_fmt(m.rotate[2])})")
        w(f"\t\t)")
        w(f"\t)")

    w(f")")

    return "\n".join(lines) + "\n"


def write_footprint(fp: Footprint, path: str) -> None:
    """Write a footprint to a .kicad_mod file."""
    with open(path, "w") as f:
        f.write(serialize_footprint(fp))
