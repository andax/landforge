"""
KiCad .kicad_mod footprint file reader.

A minimal s-expression parser plus extraction of the geometry needed for
validation: pads, courtyard extents, and metadata. Used by the stock
comparison tool (generator/stock_compare.py) and regression tests.

This reader is deliberately tolerant: it extracts what it understands and
ignores unknown nodes, so it can read both LandForge output and the stock
KiCad libraries (which contain arcs, polygons, custom pads, etc.).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path


# --- S-expression parsing ---

def _tokenize(text: str) -> list[str]:
    """Tokenize an s-expression: parens, quoted strings, bare atoms."""
    tokens: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in "()":
            tokens.append(c)
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n:
                if text[j] == "\\" and j + 1 < n:
                    buf.append(text[j + 1])
                    j += 2
                elif text[j] == '"':
                    break
                else:
                    buf.append(text[j])
                    j += 1
            # Mark quoted strings so atoms and strings are distinguishable
            tokens.append('"' + "".join(buf))
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()"':
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


def parse_sexpr(text: str) -> list:
    """Parse an s-expression string into nested Python lists.

    Quoted strings lose their quotes; all atoms are plain strings.
    Returns the outermost expression.
    """
    tokens = _tokenize(text)
    pos = 0

    def parse_node():
        nonlocal pos
        token = tokens[pos]
        if token == "(":
            pos += 1
            node = []
            while pos < len(tokens) and tokens[pos] != ")":
                node.append(parse_node())
            pos += 1  # consume ")"
            return node
        pos += 1
        return token[1:] if token.startswith('"') else token

    return parse_node()


def _children(node: list, key: str):
    """Yield child lists of `node` whose first element is `key`."""
    for child in node:
        if isinstance(child, list) and child and child[0] == key:
            yield child


def _child(node: list, key: str) -> list | None:
    """First child list of `node` whose first element is `key`, or None."""
    return next(_children(node, key), None)


def _floats(node: list) -> list[float]:
    """All elements of `node` (after the key) that parse as floats."""
    result = []
    for item in node[1:]:
        if isinstance(item, str):
            try:
                result.append(float(item))
            except ValueError:
                pass
    return result


# --- Extracted footprint data ---

@dataclass
class ReadPad:
    number: str
    pad_type: str          # "smd", "thru_hole", "np_thru_hole"
    shape: str             # "roundrect", "rect", "circle", "oval", "custom"
    x: float
    y: float
    rotation: float
    width: float
    height: float
    layers: list[str]
    drill: float | None = None

    @property
    def on_copper(self) -> bool:
        return any(l in ("F.Cu", "B.Cu", "*.Cu") for l in self.layers)

    @property
    def size_normalized(self) -> tuple[float, float]:
        """(width, height) with pad rotation folded in.

        A pad rotated 90/270 degrees occupies width x height swapped in
        footprint coordinates; normalizing lets rotated stock pads be
        compared against unrotated LandForge pads.
        """
        if round(self.rotation) % 180 == 90:
            return (self.height, self.width)
        return (self.width, self.height)


@dataclass
class ReadFootprint:
    name: str
    description: str = ""
    tags: str = ""
    smd: bool = True
    pads: list[ReadPad] = field(default_factory=list)
    courtyard_bbox: tuple[float, float, float, float] | None = None

    def copper_pads(self) -> dict[str, ReadPad]:
        """Numbered copper pads, keyed by pad number.

        Excludes paste-aperture helper pads (no copper layer), unnumbered
        pads, and NPTH holes. If several pads share a number (e.g. a
        thermal tab split into segments), the largest by area is kept as
        the representative.
        """
        result: dict[str, ReadPad] = {}
        for pad in self.pads:
            if not pad.number or not pad.on_copper:
                continue
            if pad.pad_type == "np_thru_hole":
                continue
            prev = result.get(pad.number)
            if prev is None or pad.width * pad.height > prev.width * prev.height:
                result[pad.number] = pad
        return result


def _parse_pad(node: list) -> ReadPad | None:
    """Parse a (pad ...) node. Returns None for structurally odd pads."""
    # Layout: (pad "NUM" TYPE SHAPE (at ..) (size ..) ...)
    if len(node) < 4:
        return None
    number = node[1] if isinstance(node[1], str) else ""
    pad_type = node[2] if isinstance(node[2], str) else ""
    shape = node[3] if isinstance(node[3], str) else ""

    at = _child(node, "at")
    size = _child(node, "size")
    if at is None or size is None:
        return None
    at_vals = _floats(at)
    size_vals = _floats(size)
    if len(at_vals) < 2 or len(size_vals) < 2:
        return None

    layers_node = _child(node, "layers")
    layers = [l for l in (layers_node[1:] if layers_node else [])
              if isinstance(l, str)]

    drill = None
    drill_node = _child(node, "drill")
    if drill_node is not None:
        drill_vals = _floats(drill_node)
        if drill_vals:
            drill = drill_vals[0]

    return ReadPad(
        number=number,
        pad_type=pad_type,
        shape=shape,
        x=at_vals[0],
        y=at_vals[1],
        rotation=at_vals[2] if len(at_vals) > 2 else 0.0,
        width=size_vals[0],
        height=size_vals[1],
        layers=layers,
        drill=drill,
    )


def _graphic_points(node: list) -> list[tuple[float, float]]:
    """Points that bound a graphic node (line/rect/circle/arc/poly).

    Arcs contribute their start/mid/end points only -- an approximation
    of the true extent, adequate for courtyard bounding boxes.
    """
    kind = node[0]
    points: list[tuple[float, float]] = []
    if kind in ("fp_line", "fp_rect", "fp_arc"):
        for key in ("start", "mid", "end"):
            child = _child(node, key)
            if child is not None:
                vals = _floats(child)
                if len(vals) >= 2:
                    points.append((vals[0], vals[1]))
    elif kind == "fp_circle":
        center = _child(node, "center")
        end = _child(node, "end")
        if center is not None and end is not None:
            c = _floats(center)
            e = _floats(end)
            if len(c) >= 2 and len(e) >= 2:
                radius = math.dist(c[:2], e[:2])
                points.append((c[0] - radius, c[1] - radius))
                points.append((c[0] + radius, c[1] + radius))
    elif kind == "fp_poly":
        pts = _child(node, "pts")
        if pts is not None:
            for xy in _children(pts, "xy"):
                vals = _floats(xy)
                if len(vals) >= 2:
                    points.append((vals[0], vals[1]))
    return points


def _graphic_layer(node: list) -> str | None:
    layer_node = _child(node, "layer")
    if layer_node is not None and len(layer_node) > 1:
        return layer_node[1]
    return None


def parse_footprint(text: str) -> ReadFootprint:
    """Parse .kicad_mod file content into a ReadFootprint."""
    root = parse_sexpr(text)
    if not isinstance(root, list) or not root or root[0] != "footprint":
        raise ValueError("not a footprint s-expression")

    name = root[1] if len(root) > 1 and isinstance(root[1], str) else ""

    descr_node = _child(root, "descr")
    tags_node = _child(root, "tags")
    attr_node = _child(root, "attr")

    fp = ReadFootprint(
        name=name,
        description=descr_node[1] if descr_node and len(descr_node) > 1 else "",
        tags=tags_node[1] if tags_node and len(tags_node) > 1 else "",
        smd=bool(attr_node and "smd" in attr_node[1:]),
    )

    for pad_node in _children(root, "pad"):
        pad = _parse_pad(pad_node)
        if pad is not None:
            fp.pads.append(pad)

    courtyard_points: list[tuple[float, float]] = []
    for kind in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly"):
        for node in _children(root, kind):
            if _graphic_layer(node) == "F.CrtYd":
                courtyard_points.extend(_graphic_points(node))
    if courtyard_points:
        xs = [p[0] for p in courtyard_points]
        ys = [p[1] for p in courtyard_points]
        fp.courtyard_bbox = (min(xs), min(ys), max(xs), max(ys))

    return fp


def read_footprint(path: str | Path) -> ReadFootprint:
    """Read and parse a .kicad_mod file."""
    return parse_footprint(Path(path).read_text())
