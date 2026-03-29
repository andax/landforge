"""
Extended: WLCSP (Wafer-Level Chip Scale Package) Generator.

WLCSP is essentially a BGA where the die IS the package -- no substrate,
no mold compound. Key differences from standard BGA:
  - Non-collapsible bumps (copper pillar + solder cap)
  - Ultra-fine pitch (0.35-0.50mm)
  - Land pad is slightly LARGER than bump (Table 14-6)

Adapts the BGA generator with non-collapsible ball sizing.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass

from generator.core.ipc_equations import (
    DensityLevel,
    calculate_bga_land_diameter,
    round_to,
)
from generator.core.tables import TABLE_3_17
from generator.core.naming import density_suffix
from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType, PadProperty,
    write_footprint,
)
from generator.core.layers import add_courtyard, add_fab_body

# Reuse BGA row naming
from generator.families.ipc7358_bga import bga_row_name


@dataclass
class WlcspSpec:
    pin_count: int
    pitch: float
    columns: int
    rows: int
    body_width: float   # Die size X
    body_length: float  # Die size Y
    body_height: float
    ball_diameter: float


def _wlcsp_name(spec: WlcspSpec, level: DensityLevel) -> str:
    p = f"{round(spec.pitch * 100):03d}"
    bw = f"{round(spec.body_width * 100):03d}"
    bl = f"{round(spec.body_length * 100):03d}"
    h = f"{round(spec.body_height * 100):03d}"
    return (
        f"WLCSP{spec.pin_count}N{p}P{spec.columns}X{spec.rows}"
        f"_{bw}X{bl}X{h}{density_suffix(level)}"
    )


def generate_wlcsp_footprint(spec: WlcspSpec, level: DensityLevel) -> Footprint:
    # Non-collapsible: land is slightly larger than bump
    land_dia = calculate_bga_land_diameter(
        spec.ball_diameter, level, collapsible=False,
    )

    excess = TABLE_3_17.courtyard_excess(level)
    cy_x = spec.body_width + 2 * excess
    cy_y = spec.body_length + 2 * excess

    ipc_name = _wlcsp_name(spec, level)

    fp = Footprint(
        name=ipc_name,
        description=(
            f"IPC-7351B Level {level.name} WLCSP-{spec.pin_count}, "
            f"{spec.pitch}mm pitch, {spec.columns}x{spec.rows} grid. "
            f"Non-collapsible bumps. Land dia={land_dia:.3f}mm. "
            f"Courtyard excess={excess:.2f}mm."
        ),
        tags=(
            f"{ipc_name} wlcsp csp wafer-level {spec.pin_count}pin "
            f"{spec.pitch}mm IPC7351B density_{level.name}"
        ),
        properties={"DensityLevel": level.name, "LandForge": "true"},
    )

    # Generate ball grid (same as BGA but non-collapsible)
    x_start = -spec.pitch * (spec.columns - 1) / 2
    y_start = -spec.pitch * (spec.rows - 1) / 2

    for row in range(spec.rows):
        row_letter = bga_row_name(row)
        for col in range(spec.columns):
            fp.pads.append(Pad(
                number=f"{row_letter}{col + 1}",
                pad_type=PadType.SMD,
                shape=PadShape.CIRCLE,
                x=x_start + col * spec.pitch,
                y=y_start + row * spec.pitch,
                width=land_dia,
                height=land_dia,
                layers=["F.Cu", "F.Mask", "F.Paste"],
                roundrect_ratio=None,
                property=PadProperty.BGA,
            ))

    add_courtyard(fp, cy_x, cy_y)
    add_fab_body(fp, spec.body_width, spec.body_length, pin1_chamfer=0.3)

    return fp


def load_wlcsp_database(csv_path: str) -> list[WlcspSpec]:
    specs = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            specs.append(WlcspSpec(
                pin_count=int(row["pin_count"]),
                pitch=float(row["pitch"]),
                columns=int(row["columns"]),
                rows=int(row["rows"]),
                body_width=float(row["body_width"]),
                body_length=float(row["body_length"]),
                body_height=float(row["body_height"]),
                ball_diameter=float(row["ball_diameter"]),
            ))
    return specs


def generate_wlcsp_library(csv_path: str, output_dir: str) -> int:
    os.makedirs(output_dir, exist_ok=True)
    specs = load_wlcsp_database(csv_path)
    count = 0
    for spec in specs:
        for level in DensityLevel:
            fp = generate_wlcsp_footprint(spec, level)
            write_footprint(fp, os.path.join(output_dir, f"{fp.name}.kicad_mod"))
            count += 1
    return count
