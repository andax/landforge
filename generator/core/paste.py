"""
Thermal pad paste segmentation per IPC-7351B section 3.1.5.7.

The standard: "The IPC-7351 default paste mask for these thermal pads is
40% of the overall land area. This allows the component body to settle
as opposed to floating on top of solder. The paste mask on thermal pads
is a single square for thermal pads 4.0 mm or less. Above that size the
thermal pads are typically segmented into multiple patterns."

Implementation: the land is divided per axis into ceil(dim / 4.0) equal
cells; each cell gets a centered aperture scaled by sqrt(0.40) per axis,
so total paste area is 40% of the land area. A land 4.0 mm or smaller in
both axes therefore gets exactly one centered aperture.

Apertures are emitted as unnumbered F.Paste-only pads; the copper/mask
thermal pad itself carries no paste layer.
"""

from __future__ import annotations

import math

from generator.core.kicad_writer import Footprint, Pad, PadShape, PadType

PASTE_COVERAGE = 0.40      # fraction of land area (IPC-7351B 3.1.5.7)
MAX_SINGLE_APERTURE = 4.0  # mm; larger lands are segmented


def thermal_paste_segments(
    width: float,
    height: float,
    coverage: float = PASTE_COVERAGE,
    max_single: float = MAX_SINGLE_APERTURE,
) -> list[tuple[float, float, float, float]]:
    """Paste aperture rectangles for a thermal land centered at origin.

    Returns (cx, cy, w, h) tuples relative to the land center.
    """
    scale = math.sqrt(coverage)
    nx = max(1, math.ceil(width / max_single))
    ny = max(1, math.ceil(height / max_single))
    cell_w = width / nx
    cell_h = height / ny
    seg_w = round(cell_w * scale, 3)
    seg_h = round(cell_h * scale, 3)

    segments = []
    for i in range(nx):
        cx = -width / 2 + (i + 0.5) * cell_w
        for j in range(ny):
            cy = -height / 2 + (j + 0.5) * cell_h
            segments.append((round(cx, 3), round(cy, 3), seg_w, seg_h))
    return segments


def add_thermal_paste(fp: Footprint, pad_x: float, pad_y: float,
                      width: float, height: float) -> None:
    """Append 3.1.5.7 paste apertures for a thermal land at (pad_x, pad_y)."""
    for cx, cy, w, h in thermal_paste_segments(width, height):
        fp.pads.append(Pad(
            number="",
            pad_type=PadType.SMD,
            shape=PadShape.RECT,
            x=pad_x + cx, y=pad_y + cy,
            width=w, height=h,
            layers=["F.Paste"],
            roundrect_ratio=None,
        ))
