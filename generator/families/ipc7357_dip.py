"""
IPC-7357 DIP (Dual In-line Package) Through-Hole Generator.

Generates footprints for through-hole DIP packages.
Uses Table 3-12: Butt Joints.

Pin layout: two parallel rows along Y axis, pins along X.
Pin 1 at top-left, numbered counter-clockwise.
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
from generator.core.tables import TABLE_3_12
from generator.core.naming import density_suffix
from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType,
    write_footprint,
)
from generator.core.layers import add_courtyard, add_fab_body


@dataclass
class DipSpec:
    pin_count: int
    pitch: float        # 2.54mm standard
    row_spacing: float  # 7.62mm (300mil) or 15.24mm (600mil)
    body_width: float
    body_length: float
    body_height: float
    # Lead dimensions
    L_min: float        # Row spacing (min)
    L_max: float        # Row spacing (max)
    T_min: float        # Lead width at board entry (min)
    T_max: float
    W_min: float        # Lead thickness (min)
    W_max: float
    drill: float        # Drill diameter

    def to_ipc_dims(self) -> ComponentDimensionsFromSpec:
        return ComponentDimensionsFromSpec(
            L_min=self.L_min, L_max=self.L_max,
            T_min=self.T_min, T_max=self.T_max,
            W_min=self.W_min, W_max=self.W_max,
        )


def _dip_ipc_name(spec: DipSpec, level: DensityLevel) -> str:
    rs = f"{round(spec.row_spacing * 100):03d}"
    h = f"{round(spec.body_height * 100):03d}"
    return f"DIP{rs}W{h}P{round(spec.pitch * 100):03d}-{spec.pin_count}{density_suffix(level)}"


def generate_dip_footprint(spec: DipSpec, level: DensityLevel) -> Footprint:
    table = TABLE_3_12
    comp = spec.to_ipc_dims().to_component_dimensions()
    lp = calculate_land_pattern(comp, table, level)

    ipc_name = _dip_ipc_name(spec, level)
    excess = table.courtyard_excess(level)

    fp = Footprint(
        name=ipc_name,
        smd=False,
        description=(
            f"IPC-7351B Level {level.name} DIP-{spec.pin_count}, "
            f"{spec.row_spacing}mm row spacing. Table 3-12. "
            f"Courtyard excess={excess:.2f}mm."
        ),
        tags=f"{ipc_name} dip {spec.pin_count}pin through_hole IPC7351B density_{level.name}",
        properties={"IPC_Table": "3-12", "DensityLevel": level.name, "LandForge": "true"},
    )

    pins_per_side = spec.pin_count // 2
    row_cx = spec.row_spacing / 2
    y_start = -spec.pitch * (pins_per_side - 1) / 2

    pad_dia = lp.pad_width  # Through-hole pad diameter

    # Left side (pins 1..N/2, top to bottom)
    for i in range(pins_per_side):
        fp.pads.append(Pad(
            number=str(i + 1),
            pad_type=PadType.THT,
            shape=PadShape.OVAL if i > 0 else PadShape.RECT,  # Pin 1 is rectangular
            x=-row_cx, y=y_start + i * spec.pitch,
            width=pad_dia, height=pad_dia,
            layers=["*.Cu", "*.Mask"],
            drill=spec.drill,
            roundrect_ratio=None,
        ))

    # Right side (pins N/2+1..N, bottom to top)
    for i in range(pins_per_side):
        fp.pads.append(Pad(
            number=str(pins_per_side + i + 1),
            pad_type=PadType.THT,
            shape=PadShape.OVAL,
            x=row_cx, y=y_start + (pins_per_side - 1 - i) * spec.pitch,
            width=pad_dia, height=pad_dia,
            layers=["*.Cu", "*.Mask"],
            drill=spec.drill,
            roundrect_ratio=None,
        ))

    # Courtyard and body
    pad_y_extent = spec.pitch * (pins_per_side - 1) / 2 + pad_dia / 2
    cy_x = max(spec.body_width, row_cx * 2 + pad_dia) + 2 * excess
    cy_y = max(spec.body_length, pad_y_extent * 2) + 2 * excess
    add_courtyard(fp, cy_x, cy_y)
    add_fab_body(fp, spec.body_width, spec.body_length, pin1_chamfer=1.0)

    return fp


def load_dip_database(csv_path: str) -> list[DipSpec]:
    specs = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            specs.append(DipSpec(
                pin_count=int(row["pin_count"]),
                pitch=float(row["pitch"]),
                row_spacing=float(row["row_spacing"]),
                body_width=float(row["body_width"]),
                body_length=float(row["body_length"]),
                body_height=float(row["body_height"]),
                L_min=float(row["L_min"]),
                L_max=float(row["L_max"]),
                T_min=float(row["T_min"]),
                T_max=float(row["T_max"]),
                W_min=float(row["W_min"]),
                W_max=float(row["W_max"]),
                drill=float(row["drill"]),
            ))
    return specs


def generate_dip_library(csv_path: str, output_dir: str) -> int:
    os.makedirs(output_dir, exist_ok=True)
    specs = load_dip_database(csv_path)
    count = 0
    for spec in specs:
        for level in DensityLevel:
            fp = generate_dip_footprint(spec, level)
            write_footprint(fp, os.path.join(output_dir, f"{fp.name}.kicad_mod"))
            count += 1
    return count
