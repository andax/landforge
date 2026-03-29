"""
IPC-7359 No-Lead Package Family Generator (QFN, SON, DFN).

Generates footprints for:
  QFN: Quad Flat No-Lead (4-side pads + center exposed/thermal pad)
  SON: Small Outline No-Lead (2-side pads + center exposed pad)
  DFN: Dual Flat No-Lead (2-side pads + optional exposed pad)

Uses Table 3-15 for QFN, Table 3-16 for SON, Table 3-18 for DFN/PQFN/PSON.

Pin layout is generated programmatically from pitch and pin count:
  - QFN: pins distributed on all 4 sides, counter-clockwise from top-left
  - SON/DFN: pins on 2 sides (left/right), counter-clockwise

KiCad orientation:
  - QFN: square body centered at origin, pads on all 4 edges
  - SON/DFN: pads along X axis (left/right rows), body centered at origin
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass

from generator.core.ipc_equations import (
    DensityLevel,
    ComponentDimensionsFromSpec,
    calculate_land_pattern,
)
from generator.core.tables import TABLE_3_15, TABLE_3_16, TABLE_3_18
from generator.core.naming import name_nolead, density_suffix
from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType, PadProperty,
    write_footprint,
)
from generator.core.layers import (
    add_courtyard, add_fab_body, add_silk_ic,
)


# Table selection by package type
_TABLE_MAP = {
    "QFN": TABLE_3_15,
    "SON": TABLE_3_16,
    "DFN": TABLE_3_18,
}

# QFN is 4-side, SON and DFN are 2-side
_SIDES_MAP = {
    "QFN": 4,
    "SON": 2,
    "DFN": 2,
}


@dataclass
class NoleadSpec:
    """Specification for a no-lead package (QFN, SON, DFN)."""
    pkg_type: str        # QFN, SON, or DFN
    pin_count: int
    pitch: float         # Lead pitch (mm)
    body_width: float    # Body width (X)
    body_length: float   # Body length (Y)
    body_height: float
    lead_span_x: float   # Lead span across X (= body_width for no-lead)
    lead_span_y: float   # Lead span across Y (= body_length for QFN)
    # Lead dimensions for IPC calculation
    L_min: float         # Overall span, min
    L_max: float         # Overall span, max
    T_min: float         # Terminal extension, min
    T_max: float         # Terminal extension, max
    W_min: float         # Lead width, min
    W_max: float         # Lead width, max
    # Exposed pad
    has_ep: bool = True
    ep_width: float = 0.0   # Exposed pad X size
    ep_length: float = 0.0  # Exposed pad Y size

    @property
    def sides(self) -> int:
        return _SIDES_MAP[self.pkg_type]

    @property
    def table(self):
        return _TABLE_MAP[self.pkg_type]

    def to_ipc_dims(self) -> ComponentDimensionsFromSpec:
        return ComponentDimensionsFromSpec(
            L_min=self.L_min, L_max=self.L_max,
            T_min=self.T_min, T_max=self.T_max,
            W_min=self.W_min, W_max=self.W_max,
        )


def _generate_2side_pads(
    pin_count: int,
    pitch: float,
    pad_cx: float,
    pad_length: float,
    pad_width: float,
) -> list[Pad]:
    """Generate pads for a 2-side no-lead package (SON, DFN).

    Pin numbering: 1..N/2 on left side (top to bottom),
    N/2+1..N on right side (bottom to top).
    Pads are along X axis (left row at -X, right row at +X).
    """
    pads = []
    pins_per_side = pin_count // 2
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


def _generate_4side_pads(
    pin_count: int,
    pitch: float,
    pad_cx: float,
    pad_cy: float,
    pad_length: float,
    pad_width: float,
) -> list[Pad]:
    """Generate pads for a 4-side no-lead package (QFN).

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


def _ipc_name(spec: NoleadSpec, level: DensityLevel) -> str:
    """Generate IPC name for a no-lead package."""
    tp = max(spec.ep_width, spec.ep_length) if spec.has_ep else None
    return name_nolead(
        prefix=spec.pkg_type,
        pitch=spec.pitch,
        body_width=spec.body_width,
        body_length=spec.body_length,
        height=spec.body_height,
        pin_count=spec.pin_count,
        level=level,
        thermal_pad=tp,
    )


def generate_nolead_footprint(spec: NoleadSpec, level: DensityLevel) -> Footprint:
    """Generate a no-lead package footprint (QFN, SON, DFN)."""
    table = spec.table
    comp = spec.to_ipc_dims().to_component_dimensions()
    lp = calculate_land_pattern(comp, table, level)

    ipc_name = _ipc_name(spec, level)
    excess = table.courtyard_excess(level)

    fp = Footprint(
        name=ipc_name,
        description=(
            f"IPC-7351B Level {level.name} {spec.pkg_type}-{spec.pin_count}, "
            f"{spec.pitch}mm pitch, {spec.body_width}x{spec.body_length}mm body. "
            f"Table {table.name}. Z={lp.Z:.2f} G={lp.G:.2f} X={lp.X:.2f}. "
            f"Courtyard excess={excess:.2f}mm."
        ),
        tags=(
            f"{ipc_name} {spec.pkg_type.lower()} {spec.pin_count}pin "
            f"{spec.pitch}mm IPC7351B density_{level.name}"
        ),
        properties={
            "IPC_Table": table.name, "DensityLevel": level.name, "LandForge": "true",
        },
    )

    pad_cx = lp.pad_center_to_center / 2

    if spec.sides == 2:
        fp.pads = _generate_2side_pads(
            spec.pin_count, spec.pitch, pad_cx, lp.pad_length, lp.pad_width,
        )

        # Courtyard: account for pad extent in both directions
        pad_y_extent = spec.pitch * (spec.pin_count // 2 - 1) / 2 + lp.pad_width / 2
        cy_x = max(spec.body_width, lp.Z) + 2 * excess
        cy_y = max(spec.body_length, pad_y_extent * 2) + 2 * excess
        add_courtyard(fp, cy_x, cy_y)
        add_fab_body(fp, spec.body_width, spec.body_length, pin1_chamfer=0.3)

        pad_x_extent = pad_cx + lp.pad_length / 2
        add_silk_ic(fp, spec.body_width, spec.body_length, pad_x_extent, pad_y_extent)

    else:  # 4-side (QFN)
        pad_cy = pad_cx  # Symmetric for square QFN
        fp.pads = _generate_4side_pads(
            spec.pin_count, spec.pitch, pad_cx, pad_cy, lp.pad_length, lp.pad_width,
        )

        # Courtyard: account for pad extent on all sides
        pps = spec.pin_count // 4
        pin_y_extent = spec.pitch * (pps - 1) / 2 + lp.pad_width / 2
        cy_x = max(spec.body_width, lp.Z, pin_y_extent * 2) + 2 * excess
        cy_y = max(spec.body_length, lp.Z, pin_y_extent * 2) + 2 * excess
        add_courtyard(fp, cy_x, cy_y)
        add_fab_body(fp, spec.body_width, spec.body_length, pin1_chamfer=0.5)

        pad_x_extent = pad_cx + lp.pad_length / 2
        pad_y_extent = pad_cy + lp.pad_length / 2
        add_silk_ic(fp, spec.body_width, spec.body_length, pad_x_extent, pad_y_extent)

    # Exposed / thermal pad
    if spec.has_ep:
        ep_num = str(spec.pin_count + 1)
        fp.pads.append(Pad(
            number=ep_num,
            pad_type=PadType.SMD,
            shape=PadShape.ROUNDRECT,
            x=0, y=0,
            width=spec.ep_width,
            height=spec.ep_length,
            layers=["F.Cu", "F.Mask"],  # No paste - handled separately
            roundrect_ratio=0.1,
            property=PadProperty.HEATSINK,
        ))

    return fp


def load_nolead_database(csv_path: str) -> list[NoleadSpec]:
    """Load QFN/SON/DFN specs from CSV."""
    specs = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            specs.append(NoleadSpec(
                pkg_type=row["type"],
                pin_count=int(row["pin_count"]),
                pitch=float(row["pitch"]),
                body_width=float(row["body_width"]),
                body_length=float(row["body_length"]),
                body_height=float(row["body_height"]),
                lead_span_x=float(row["lead_span_x"]),
                lead_span_y=float(row["lead_span_y"]),
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


def generate_nolead_library(csv_path: str, output_dir: str) -> int:
    """Generate all no-lead footprints from CSV database.

    Creates footprints for all 3 density levels (A/B/C) for each component.

    Args:
        csv_path: Path to the QFN/SON/DFN CSV database.
        output_dir: Output directory (.pretty folder).

    Returns:
        Number of footprints generated.
    """
    os.makedirs(output_dir, exist_ok=True)
    specs = load_nolead_database(csv_path)
    count = 0
    for spec in specs:
        for level in DensityLevel:
            fp = generate_nolead_footprint(spec, level)
            write_footprint(fp, os.path.join(output_dir, f"{fp.name}.kicad_mod"))
            count += 1
    return count
