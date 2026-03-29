"""
IPC-7352 MELF (Metal Electrode Leadless Face) Component Family Generator.

Generates footprints for cylindrical end-cap termination components:
  RESMELF (resistor), DIOMELF (diode)

Uses Table 3-7: Cylindrical End Cap Terminations.

KiCad orientation: body long axis along X, pads at ±X.
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
from generator.core.tables import TABLE_3_7
from generator.core.naming import density_suffix
from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType,
    write_footprint,
)
from generator.core.layers import (
    add_courtyard, add_fab_body, add_silk_chip, add_polarity_mark,
)


@dataclass
class MelfComponentSpec:
    prefix: str         # RESMELF or DIOMELF
    name_suffix: str    # e.g., "MMB-0207" for standard MELF
    body_length: float  # Cylindrical body length
    body_diameter: float  # Cylindrical body diameter
    L_min: float
    L_max: float
    T_min: float        # End cap length
    T_max: float
    W_min: float        # End cap width (= body diameter for cylindrical)
    W_max: float
    polarized: bool = False

    def to_ipc_dims(self) -> ComponentDimensionsFromSpec:
        return ComponentDimensionsFromSpec(
            L_min=self.L_min, L_max=self.L_max,
            T_min=self.T_min, T_max=self.T_max,
            W_min=self.W_min, W_max=self.W_max,
        )


def _melf_ipc_name(spec: MelfComponentSpec, level: DensityLevel) -> str:
    """MELF naming: {PREFIX}{BodyLength_2.2}{BodyDiameter_2.2}{Density}"""
    bl = f"{round(spec.body_length * 100):03d}"
    bd = f"{round(spec.body_diameter * 100):03d}"
    return f"{spec.prefix}{bl}X{bd}{density_suffix(level)}"


def generate_melf_footprint(spec: MelfComponentSpec, level: DensityLevel) -> Footprint:
    table = TABLE_3_7
    comp = spec.to_ipc_dims().to_component_dimensions()
    lp = calculate_land_pattern(comp, table, level)

    cy_x = max(spec.body_length, lp.Z) + 2 * table.courtyard_excess(level)
    cy_y = max(spec.body_diameter, lp.X) + 2 * table.courtyard_excess(level)

    ipc_name = _melf_ipc_name(spec, level)

    desc_type = "MELF Resistor" if spec.prefix == "RESMELF" else "MELF Diode"

    fp = Footprint(
        name=ipc_name,
        description=(
            f"IPC-7351B Level {level.name} {desc_type} {spec.name_suffix}. "
            f"Table 3-7. Z={lp.Z:.2f} G={lp.G:.2f} X={lp.X:.2f}. "
            f"Courtyard excess={table.courtyard_excess(level):.2f}mm."
        ),
        tags=f"{ipc_name} {desc_type.lower()} melf IPC7351B density_{level.name}",
        properties={"IPC_Table": "3-7", "DensityLevel": level.name, "LandForge": "true"},
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
    add_fab_body(fp, spec.body_length, spec.body_diameter)

    if spec.polarized:
        add_polarity_mark(fp, -spec.body_length / 2 + 0.2, 0)

    pad_x_extent = pad_cx + lp.pad_length / 2
    pad_y_extent = lp.pad_width / 2
    add_silk_chip(fp, spec.body_length, pad_x_extent, pad_y_extent)

    return fp


def load_melf_database(csv_path: str) -> list[MelfComponentSpec]:
    specs = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            specs.append(MelfComponentSpec(
                prefix=row["prefix"],
                name_suffix=row["name_suffix"],
                body_length=float(row["body_length"]),
                body_diameter=float(row["body_diameter"]),
                L_min=float(row["L_min"]),
                L_max=float(row["L_max"]),
                T_min=float(row["T_min"]),
                T_max=float(row["T_max"]),
                W_min=float(row["W_min"]),
                W_max=float(row["W_max"]),
                polarized=row.get("polarized", "false").lower() == "true",
            ))
    return specs


def generate_melf_library(csv_path: str, output_dir: str) -> int:
    os.makedirs(output_dir, exist_ok=True)
    specs = load_melf_database(csv_path)
    count = 0
    for spec in specs:
        for level in DensityLevel:
            fp = generate_melf_footprint(spec, level)
            write_footprint(fp, os.path.join(output_dir, f"{fp.name}.kicad_mod"))
            count += 1
    return count
