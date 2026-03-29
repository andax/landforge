"""
IPC-7352 Molded Body Component Family Generator.

Generates footprints for components with inward-bent L-shaped flat leads:
  CAPMP (molded capacitor polar), CAPM (non-polar), DIOM (molded diode),
  INDM (molded inductor), RESM (molded resistor), FUSM (fuse), LEDM (LED)

Uses Table 3-13: Inward Flat Ribbon L-Leads.

IMPORTANT: Table 3-13 reverses toe/heel vs gull-wing:
  - Heel fillet (J_H) applies to the OUTER (Z) dimension (larger value)
  - Toe fillet (J_T) applies to the INNER (G) dimension (smaller value)
  The standard calculate_land_pattern function handles this correctly because
  Table 3-13 already has the values in the right fields:
    fillet.toe=0.25/0.15/0.07 (small, for inner gap)
    fillet.heel=0.80/0.50/0.20 (large, for outer span)

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
from generator.core.tables import TABLE_3_13
from generator.core.naming import name_chip, density_suffix
from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType, Model3D,
    write_footprint,
)
from generator.core.layers import (
    add_courtyard, add_fab_body, add_silk_chip, add_polarity_mark,
)


@dataclass
class MoldedComponentSpec:
    prefix: str
    eia_code: str
    metric_code: str
    body_length: float
    body_width: float
    body_height: float
    L_min: float
    L_max: float
    T_min: float
    T_max: float
    W_min: float
    W_max: float
    polarized: bool = True  # Most molded components are polarized

    def to_ipc_dims(self) -> ComponentDimensionsFromSpec:
        return ComponentDimensionsFromSpec(
            L_min=self.L_min, L_max=self.L_max,
            T_min=self.T_min, T_max=self.T_max,
            W_min=self.W_min, W_max=self.W_max,
        )


def generate_molded_footprint(spec: MoldedComponentSpec, level: DensityLevel) -> Footprint:
    table = TABLE_3_13
    comp = spec.to_ipc_dims().to_component_dimensions()
    lp = calculate_land_pattern(comp, table, level)

    cy_x = max(spec.body_length, lp.Z) + 2 * table.courtyard_excess(level)
    cy_y = max(spec.body_width, lp.X) + 2 * table.courtyard_excess(level)

    ipc_name = name_chip(spec.prefix, spec.body_length, spec.body_width,
                         spec.body_height, level)

    desc_type = {
        "CAPMP": "Molded Capacitor (Polar)", "CAPM": "Molded Capacitor",
        "DIOM": "Molded Diode", "INDM": "Molded Inductor",
        "RESM": "Molded Resistor", "FUSM": "Molded Fuse", "LEDM": "Molded LED",
    }.get(spec.prefix, spec.prefix)

    fp = Footprint(
        name=ipc_name,
        description=(
            f"IPC-7351B Level {level.name} {desc_type} "
            f"{spec.eia_code} ({spec.metric_code} Metric). "
            f"Table 3-13. Z={lp.Z:.2f} G={lp.G:.2f} X={lp.X:.2f}. "
            f"Courtyard excess={table.courtyard_excess(level):.2f}mm."
        ),
        tags=(
            f"{ipc_name} {desc_type.lower()} "
            f"{spec.eia_code} {spec.metric_code} IPC7351B density_{level.name}"
        ),
        properties={"IPC_Table": "3-13", "DensityLevel": level.name, "LandForge": "true"},
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
    chamfer = 0.3 if spec.polarized else 0
    add_fab_body(fp, spec.body_length, spec.body_width, pin1_chamfer=chamfer)

    if spec.polarized:
        add_polarity_mark(fp, -spec.body_length / 2 + 0.2, 0)

    pad_x_extent = pad_cx + lp.pad_length / 2
    pad_y_extent = lp.pad_width / 2
    add_silk_chip(fp, spec.body_length, pad_x_extent, pad_y_extent)

    return fp


def load_molded_database(csv_path: str) -> list[MoldedComponentSpec]:
    specs = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            specs.append(MoldedComponentSpec(
                prefix=row["prefix"],
                eia_code=row["eia_code"],
                metric_code=row["metric_code"],
                body_length=float(row["body_length"]),
                body_width=float(row["body_width"]),
                body_height=float(row["body_height"]),
                L_min=float(row["L_min"]),
                L_max=float(row["L_max"]),
                T_min=float(row["T_min"]),
                T_max=float(row["T_max"]),
                W_min=float(row["W_min"]),
                W_max=float(row["W_max"]),
                polarized=row.get("polarized", "true").lower() == "true",
            ))
    return specs


def generate_molded_library(csv_path: str, output_dir: str) -> int:
    os.makedirs(output_dir, exist_ok=True)
    specs = load_molded_database(csv_path)
    count = 0
    for spec in specs:
        for level in DensityLevel:
            fp = generate_molded_footprint(spec, level)
            write_footprint(fp, os.path.join(output_dir, f"{fp.name}.kicad_mod"))
            count += 1
    return count
