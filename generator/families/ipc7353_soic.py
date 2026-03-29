"""
IPC-7353 Gull-Wing Leaded IC Family Generator (2-side and 4-side).

Generates footprints for:
  2-side: SOIC, SOP, SSOP, TSSOP, MSOP, SOP127, CFP127
  4-side: QFP, TQFP, LQFP, BQFP, CQFP

Uses Table 3-2 (pitch > 0.625mm) or Table 3-3 (pitch <= 0.625mm).

Pin layout is generated programmatically from pitch and pin count.
Pins are numbered counter-clockwise starting from pin 1 at top-left:
  - 2-side: pins 1..N/2 on left side (top to bottom), N/2+1..N on right (bottom to top)
  - 4-side: pins distributed equally on all 4 sides, starting top-left going down

KiCad orientation:
  - 2-side: pads along X axis (left/right rows), body long axis along Y
  - 4-side: pads on all 4 sides, body centered at origin
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from typing import Literal

from generator.core.ipc_equations import (
    DensityLevel,
    ComponentDimensionsFromSpec,
    calculate_land_pattern,
)
from generator.core.tables import TABLE_3_2, TABLE_3_3
from generator.core.naming import name_leaded_2side, name_qfp, density_suffix
from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType, PadProperty,
    write_footprint,
)
from generator.core.layers import (
    add_courtyard, add_fab_body, add_silk_ic,
)


@dataclass
class GullwingICSpec:
    """Specification for a gull-wing leaded IC package."""
    prefix: str          # SOIC, SOP, SSOP, TSSOP, MSOP, QFP, etc.
    sides: int           # 2 or 4
    pin_count: int
    pitch: float         # Lead pitch (mm)
    body_width: float    # Body width (X for 2-side, both for 4-side)
    body_length: float   # Body length (Y for 2-side)
    body_height: float
    lead_span_x: float   # Lead tip-to-tip span across X
    lead_span_y: float   # Lead tip-to-tip span across Y (= lead_span_x for 2-side)
    # Lead dimensions for IPC calculation
    L_min: float         # Overall span, min
    L_max: float         # Overall span, max
    T_min: float         # Lead length, min
    T_max: float         # Lead length, max
    W_min: float         # Lead width, min
    W_max: float         # Lead width, max
    # Optional exposed pad
    has_ep: bool = False
    ep_width: float = 0.0   # Exposed pad X size
    ep_length: float = 0.0  # Exposed pad Y size

    @property
    def table(self):
        return TABLE_3_3 if self.pitch <= 0.625 else TABLE_3_2

    def to_ipc_dims(self) -> ComponentDimensionsFromSpec:
        return ComponentDimensionsFromSpec(
            L_min=self.L_min, L_max=self.L_max,
            T_min=self.T_min, T_max=self.T_max,
            W_min=self.W_min, W_max=self.W_max,
        )


def _generate_2side_pins(
    pin_count: int,
    pitch: float,
    pad_cx: float,
    pad_length: float,
    pad_width: float,
) -> list[Pad]:
    """Generate pads for a 2-side IC (SOIC, SOP, etc.).

    Pin numbering: 1..N/2 on left side (top to bottom),
    N/2+1..N on right side (bottom to top).
    Pads are along X axis (left row at -X, right row at +X).
    """
    pads = []
    pins_per_side = pin_count // 2
    # Y positions: centered, spaced by pitch
    y_start = -pitch * (pins_per_side - 1) / 2

    # Left side (pins 1 to N/2, top to bottom)
    for i in range(pins_per_side):
        pads.append(Pad(
            number=str(i + 1),
            pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=-pad_cx, y=y_start + i * pitch,
            width=pad_length, height=pad_width,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))

    # Right side (pins N/2+1 to N, bottom to top)
    for i in range(pins_per_side):
        pads.append(Pad(
            number=str(pins_per_side + i + 1),
            pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=pad_cx, y=y_start + (pins_per_side - 1 - i) * pitch,
            width=pad_length, height=pad_width,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))

    return pads


def _generate_4side_pins(
    pin_count: int,
    pitch: float,
    pad_cx: float,
    pad_cy: float,
    pad_length: float,
    pad_width: float,
) -> list[Pad]:
    """Generate pads for a 4-side IC (QFP).

    Pin numbering starts at pin 1 (top of left side), goes counter-clockwise:
      Left side (top to bottom): pins 1..N/4
      Bottom side (left to right): pins N/4+1..N/2
      Right side (bottom to top): pins N/2+1..3N/4
      Top side (right to left): pins 3N/4+1..N
    """
    pads = []
    pps = pin_count // 4  # pins per side

    y_start = -pitch * (pps - 1) / 2
    x_start = -pitch * (pps - 1) / 2

    pin = 1

    # Left side (top to bottom, pads along X)
    for i in range(pps):
        pads.append(Pad(
            number=str(pin), pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=-pad_cx, y=y_start + i * pitch,
            width=pad_length, height=pad_width,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))
        pin += 1

    # Bottom side (left to right, pads along Y)
    for i in range(pps):
        pads.append(Pad(
            number=str(pin), pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=x_start + i * pitch, y=pad_cy,
            width=pad_width, height=pad_length,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))
        pin += 1

    # Right side (bottom to top, pads along X)
    for i in range(pps):
        pads.append(Pad(
            number=str(pin), pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=pad_cx, y=y_start + (pps - 1 - i) * pitch,
            width=pad_length, height=pad_width,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))
        pin += 1

    # Top side (right to left, pads along Y)
    for i in range(pps):
        pads.append(Pad(
            number=str(pin), pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=x_start + (pps - 1 - i) * pitch, y=-pad_cy,
            width=pad_width, height=pad_length,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))
        pin += 1

    return pads


def _ipc_name(spec: GullwingICSpec, level: DensityLevel) -> str:
    if spec.sides == 4:
        return name_qfp(
            spec.pitch, spec.lead_span_x, spec.lead_span_y,
            spec.body_height, spec.pin_count, level, prefix=spec.prefix,
        )
    return name_leaded_2side(
        spec.prefix, spec.pitch, spec.lead_span_x,
        spec.body_height, spec.pin_count, level,
    )


def generate_gullwing_ic(spec: GullwingICSpec, level: DensityLevel) -> Footprint:
    """Generate a gull-wing IC footprint (2-side or 4-side)."""
    table = spec.table
    comp = spec.to_ipc_dims().to_component_dimensions()
    lp = calculate_land_pattern(comp, table, level)

    ipc_name = _ipc_name(spec, level)
    excess = table.courtyard_excess(level)

    fp = Footprint(
        name=ipc_name,
        description=(
            f"IPC-7351B Level {level.name} {spec.prefix}-{spec.pin_count}, "
            f"{spec.pitch}mm pitch. Table {table.name}. "
            f"Z={lp.Z:.2f} G={lp.G:.2f} X={lp.X:.2f}. "
            f"Courtyard excess={excess:.2f}mm."
        ),
        tags=(
            f"{ipc_name} {spec.prefix.lower()} {spec.pin_count}pin "
            f"{spec.pitch}mm IPC7351B density_{level.name}"
        ),
        properties={
            "IPC_Table": table.name, "DensityLevel": level.name, "LandForge": "true",
        },
    )

    pad_cx = lp.pad_center_to_center / 2

    if spec.sides == 2:
        fp.pads = _generate_2side_pins(
            spec.pin_count, spec.pitch, pad_cx, lp.pad_length, lp.pad_width,
        )
        # Courtyard
        pad_y_extent = spec.pitch * (spec.pin_count // 2 - 1) / 2 + lp.pad_width / 2
        cy_x = max(spec.body_width, lp.Z) + 2 * excess
        cy_y = max(spec.body_length, pad_y_extent * 2) + 2 * excess
        add_courtyard(fp, cy_x, cy_y)
        add_fab_body(fp, spec.body_width, spec.body_length, pin1_chamfer=0.5)

        pad_x_extent = pad_cx + lp.pad_length / 2
        add_silk_ic(fp, spec.body_width, spec.body_length, pad_x_extent, pad_y_extent)

    else:  # 4-side
        pad_cy = lp.pad_center_to_center / 2  # Same calculation for Y span
        fp.pads = _generate_4side_pins(
            spec.pin_count, spec.pitch, pad_cx, pad_cy, lp.pad_length, lp.pad_width,
        )
        # Courtyard
        pps = spec.pin_count // 4
        pin_y_extent = spec.pitch * (pps - 1) / 2 + lp.pad_width / 2
        cy_x = max(spec.body_width, lp.Z, pin_y_extent * 2) + 2 * excess
        cy_y = max(spec.body_length, lp.Z, pin_y_extent * 2) + 2 * excess
        add_courtyard(fp, cy_x, cy_y)
        add_fab_body(fp, spec.body_width, spec.body_length, pin1_chamfer=0.8)

        pad_x_extent = pad_cx + lp.pad_length / 2
        pad_y_extent = pad_cy + lp.pad_length / 2
        add_silk_ic(fp, spec.body_width, spec.body_length, pad_x_extent, pad_y_extent)

    # Exposed pad
    if spec.has_ep:
        ep_num = str(spec.pin_count + 1)
        fp.pads.append(Pad(
            number=ep_num, pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=0, y=0, width=spec.ep_width, height=spec.ep_length,
            layers=["F.Cu", "F.Mask"],
            roundrect_ratio=0.1,
            property=PadProperty.HEATSINK,
        ))

    return fp


def load_gullwing_database(csv_path: str) -> list[GullwingICSpec]:
    specs = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            specs.append(GullwingICSpec(
                prefix=row["prefix"],
                sides=int(row["sides"]),
                pin_count=int(row["pin_count"]),
                pitch=float(row["pitch"]),
                body_width=float(row["body_width"]),
                body_length=float(row["body_length"]),
                body_height=float(row["body_height"]),
                lead_span_x=float(row["lead_span_x"]),
                lead_span_y=float(row.get("lead_span_y", row["lead_span_x"])),
                L_min=float(row["L_min"]),
                L_max=float(row["L_max"]),
                T_min=float(row["T_min"]),
                T_max=float(row["T_max"]),
                W_min=float(row["W_min"]),
                W_max=float(row["W_max"]),
                has_ep=row.get("has_ep", "false").lower() == "true",
                ep_width=float(row.get("ep_width", "0")),
                ep_length=float(row.get("ep_length", "0")),
            ))
    return specs


def generate_gullwing_library(csv_path: str, output_dir: str) -> int:
    os.makedirs(output_dir, exist_ok=True)
    specs = load_gullwing_database(csv_path)
    count = 0
    for spec in specs:
        for level in DensityLevel:
            fp = generate_gullwing_ic(spec, level)
            write_footprint(fp, os.path.join(output_dir, f"{fp.name}.kicad_mod"))
            count += 1
    return count
