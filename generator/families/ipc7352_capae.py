"""
IPC-7352 Aluminum Electrolytic Capacitor (CAPAE) Family Generator.

Generates footprints for SMD aluminum electrolytic capacitors.
Uses Table 3-20 (standard) or Table 3-20L (>= 10mm diameter).

These are cylindrical components with flat bottom terminals.
KiCad orientation: terminals along X axis, body centered.
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
from generator.core.tables import TABLE_3_20, TABLE_3_20_LARGE
from generator.core.naming import density_suffix
from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType,
    write_footprint,
)
from generator.core.layers import (
    add_courtyard, add_fab_body, add_silk_chip, add_polarity_mark,
)


@dataclass
class CapaeSpec:
    diameter: float     # Body diameter (mm)
    height: float       # Body height (mm)
    L_min: float        # Overall terminal span, min
    L_max: float        # Overall terminal span, max
    T_min: float        # Terminal length, min
    T_max: float        # Terminal length, max
    W_min: float        # Terminal width, min
    W_max: float        # Terminal width, max

    @property
    def table(self):
        return TABLE_3_20_LARGE if self.diameter >= 10.0 else TABLE_3_20

    def to_ipc_dims(self) -> ComponentDimensionsFromSpec:
        return ComponentDimensionsFromSpec(
            L_min=self.L_min, L_max=self.L_max,
            T_min=self.T_min, T_max=self.T_max,
            W_min=self.W_min, W_max=self.W_max,
        )


def _capae_ipc_name(spec: CapaeSpec, level: DensityLevel) -> str:
    """CAPAE naming: CAPAE{Diameter_2.2}X{Height_2.2}{Density}"""
    d = f"{round(spec.diameter * 100):03d}"
    h = f"{round(spec.height * 100):03d}"
    return f"CAPAE{d}X{h}{density_suffix(level)}"


def generate_capae_footprint(spec: CapaeSpec, level: DensityLevel) -> Footprint:
    table = spec.table
    comp = spec.to_ipc_dims().to_component_dimensions()
    lp = calculate_land_pattern(comp, table, level)

    # Courtyard should encompass the cylindrical body
    cy_x = max(spec.diameter, lp.Z) + 2 * table.courtyard_excess(level)
    cy_y = max(spec.diameter, lp.X) + 2 * table.courtyard_excess(level)

    ipc_name = _capae_ipc_name(spec, level)
    table_name = table.name

    fp = Footprint(
        name=ipc_name,
        description=(
            f"IPC-7351B Level {level.name} Aluminum Electrolytic Capacitor "
            f"{spec.diameter:.1f}x{spec.height:.1f}mm. "
            f"Table {table_name}. Z={lp.Z:.2f} G={lp.G:.2f} X={lp.X:.2f}. "
            f"Courtyard excess={table.courtyard_excess(level):.2f}mm."
        ),
        tags=(
            f"{ipc_name} electrolytic capacitor aluminum capae "
            f"{spec.diameter:.1f}mm IPC7351B density_{level.name}"
        ),
        properties={
            "IPC_Table": table_name, "DensityLevel": level.name, "LandForge": "true",
        },
    )

    pad_cx = lp.pad_center_to_center / 2
    fp.pads.append(Pad(
        number="1", pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
        x=-pad_cx, y=0, width=lp.pad_length, height=lp.pad_width,
        layers=["F.Cu", "F.Mask", "F.Paste"],
    ))
    fp.pads.append(Pad(
        number="2", pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
        x=pad_cx, y=0, width=lp.pad_length, height=lp.pad_width,
        layers=["F.Cu", "F.Mask", "F.Paste"],
    ))

    add_courtyard(fp, cy_x, cy_y)
    # Body outline is diameter x diameter (cylindrical, viewed from top)
    add_fab_body(fp, spec.diameter, spec.diameter)
    # Polarity mark on pin 1 side
    add_polarity_mark(fp, -spec.diameter / 2 + 0.3, 0)

    pad_x_extent = pad_cx + lp.pad_length / 2
    pad_y_extent = lp.pad_width / 2
    add_silk_chip(fp, spec.diameter, pad_x_extent, pad_y_extent)

    return fp


def load_capae_database(csv_path: str) -> list[CapaeSpec]:
    specs = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            specs.append(CapaeSpec(
                diameter=float(row["diameter"]),
                height=float(row["height"]),
                L_min=float(row["L_min"]),
                L_max=float(row["L_max"]),
                T_min=float(row["T_min"]),
                T_max=float(row["T_max"]),
                W_min=float(row["W_min"]),
                W_max=float(row["W_max"]),
            ))
    return specs


def generate_capae_library(csv_path: str, output_dir: str) -> int:
    os.makedirs(output_dir, exist_ok=True)
    specs = load_capae_database(csv_path)
    count = 0
    for spec in specs:
        for level in DensityLevel:
            fp = generate_capae_footprint(spec, level)
            write_footprint(fp, os.path.join(output_dir, f"{fp.name}.kicad_mod"))
            count += 1
    return count
