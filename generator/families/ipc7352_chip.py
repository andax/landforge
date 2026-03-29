"""
IPC-7352 Chip Component Family Generator.

Generates footprints for 2-terminal rectangular/square-end chip components:
  RESC (resistor), CAPC (capacitor non-polar), CAPCP (capacitor polar),
  INDC (inductor), DIOC (diode)

Uses Table 3-5 for components >= 1608 (0603) and Table 3-6 for smaller.

KiCad orientation convention:
  - Component body long axis along X
  - Pads at left (-X) and right (+X)
  - Pin 1 at left (negative X)
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path

from generator.core.ipc_equations import (
    DensityLevel,
    ComponentDimensionsFromSpec,
    calculate_land_pattern,
    calculate_courtyard,
)
from generator.core.tables import TABLE_3_5, TABLE_3_6
from generator.core.naming import name_chip, density_suffix
from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType, Model3D,
    write_footprint,
)
from generator.core.layers import (
    add_courtyard, add_fab_body, add_silk_chip, add_polarity_mark,
)


@dataclass
class ChipComponentSpec:
    """Specification for a chip component from the database."""
    prefix: str         # IPC prefix: RESC, CAPC, CAPCP, INDC, DIOC
    eia_code: str       # EIA size code: 0402, 0603, 0805, etc.
    metric_code: str    # Metric size code: 1005, 1608, 2012, etc.
    body_length: float  # Body length (mm), along X axis
    body_width: float   # Body width (mm), along Y axis
    body_height: float  # Body height (mm)
    L_min: float        # Overall length with terminals, minimum
    L_max: float        # Overall length with terminals, maximum
    T_min: float        # Terminal length, minimum
    T_max: float        # Terminal length, maximum
    W_min: float        # Terminal width, minimum
    W_max: float        # Terminal width, maximum
    polarized: bool = False  # True for CAPCP, DIOC

    @property
    def is_small(self) -> bool:
        """True if this component uses Table 3-6 (< 1608/0603)."""
        return self.body_length < 1.6 or (self.body_length == 1.6 and self.body_width < 0.8)

    @property
    def table(self):
        """Get the appropriate tolerance table."""
        return TABLE_3_6 if self.is_small else TABLE_3_5

    def to_ipc_dims(self) -> ComponentDimensionsFromSpec:
        return ComponentDimensionsFromSpec(
            L_min=self.L_min, L_max=self.L_max,
            T_min=self.T_min, T_max=self.T_max,
            W_min=self.W_min, W_max=self.W_max,
        )


def generate_chip_footprint(spec: ChipComponentSpec, level: DensityLevel) -> Footprint:
    """Generate a complete chip component footprint.

    Args:
        spec: Component specification from database.
        level: Density level (A, B, or C).

    Returns:
        Complete Footprint ready for serialization.
    """
    table = spec.table
    comp = spec.to_ipc_dims().to_component_dimensions()
    lp = calculate_land_pattern(comp, table, level)

    # Courtyard: X direction = land span (Z), Y direction = land width (X_max)
    cy_x = max(spec.body_length, lp.Z) + 2 * table.courtyard_excess(level)
    cy_y = max(spec.body_width, lp.X) + 2 * table.courtyard_excess(level)

    ipc_name = name_chip(spec.prefix, spec.body_length, spec.body_width,
                         spec.body_height, level)

    table_name = table.name
    fp = Footprint(
        name=ipc_name,
        description=(
            f"IPC-7351B Level {level.name} {_prefix_description(spec.prefix)} "
            f"{spec.eia_code} ({spec.metric_code} Metric). "
            f"Table {table_name}. "
            f"Z={lp.Z:.2f} G={lp.G:.2f} X={lp.X:.2f}. "
            f"Courtyard excess={table.courtyard_excess(level):.2f}mm."
        ),
        tags=(
            f"{ipc_name} {_prefix_description(spec.prefix).lower()} chip "
            f"{spec.eia_code} {spec.metric_code} IPC7351B density_{level.name}"
        ),
        properties={
            "IPC_Table": table_name,
            "DensityLevel": level.name,
            "LandForge": "true",
        },
    )

    # Pads: along X axis, symmetric about origin
    # pad_length is along X (component length axis)
    # pad_width is along Y (component width axis = IPC "X" dimension)
    pad_cx = lp.pad_center_to_center / 2

    fp.pads.append(Pad(
        number="1", pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
        x=-pad_cx, y=0,
        width=lp.pad_length, height=lp.pad_width,
        layers=["F.Cu", "F.Mask", "F.Paste"],
    ))
    fp.pads.append(Pad(
        number="2", pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
        x=pad_cx, y=0,
        width=lp.pad_length, height=lp.pad_width,
        layers=["F.Cu", "F.Mask", "F.Paste"],
    ))

    # Courtyard (X=length direction, Y=width direction)
    add_courtyard(fp, cy_x, cy_y)

    # Fabrication layer body outline
    add_fab_body(fp, spec.body_length, spec.body_width)

    # Polarity mark for polarized components
    if spec.polarized:
        add_polarity_mark(fp, -spec.body_length / 2 + 0.15, 0)

    # Silkscreen
    pad_x_extent = pad_cx + lp.pad_length / 2  # outermost pad edge in X
    pad_y_extent = lp.pad_width / 2             # outermost pad edge in Y
    add_silk_chip(fp, spec.body_length, pad_x_extent, pad_y_extent)

    # 3D model reference (to be resolved in Stage C)
    _add_stock_model_ref(fp, spec)

    return fp


def _prefix_description(prefix: str) -> str:
    """Human-readable description for an IPC prefix."""
    return {
        "RESC": "Chip Resistor",
        "CAPC": "Chip Capacitor",
        "CAPCP": "Chip Capacitor (Polar)",
        "INDC": "Chip Inductor",
        "DIOC": "Chip Diode",
    }.get(prefix, prefix)


def _add_stock_model_ref(fp: Footprint, spec: ChipComponentSpec) -> None:
    """Add a KiCad stock 3D model reference if a likely match exists."""
    # Map prefix to KiCad stock model category
    category_map = {
        "RESC": ("Resistor_SMD", "R"),
        "CAPC": ("Capacitor_SMD", "C"),
        "CAPCP": ("Capacitor_SMD", "C"),
        "INDC": ("Inductor_SMD", "L"),
        "DIOC": ("Diode_SMD", "D"),
    }
    if spec.prefix not in category_map:
        return

    category, letter = category_map[spec.prefix]
    model_name = f"{letter}_{spec.eia_code}_{spec.metric_code}Metric"
    fp.model = Model3D(
        path=f"${{KICAD10_3DMODEL_DIR}}/{category}.3dshapes/{model_name}.step"
    )


def load_chip_database(csv_path: str) -> list[ChipComponentSpec]:
    """Load chip component specifications from CSV database."""
    specs = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            specs.append(ChipComponentSpec(
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
                polarized=row.get("polarized", "").lower() == "true",
            ))
    return specs


def generate_chip_library(csv_path: str, output_dir: str) -> int:
    """Generate all chip component footprints from database.

    Args:
        csv_path: Path to chip_components.csv.
        output_dir: Path to output .pretty directory.

    Returns:
        Number of footprints generated.
    """
    os.makedirs(output_dir, exist_ok=True)
    specs = load_chip_database(csv_path)
    count = 0

    for spec in specs:
        for level in DensityLevel:
            fp = generate_chip_footprint(spec, level)
            path = os.path.join(output_dir, f"{fp.name}.kicad_mod")
            write_footprint(fp, path)
            count += 1

    return count
