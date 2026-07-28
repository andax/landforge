"""
IPC-7357 DIP (Dual In-line Package) Through-Hole Generator.

Generates footprints for through-hole DIP packages.

Land calculation: IPC-7351B covers surface mount only (its Table 3-12
"Butt Joints" is for butt-MOUNTED DIPB, not through-hole). Through-hole
holes and lands follow IPC-2221 / IPC-7251 practice:

  lead diagonal = sqrt(lead_width_max^2 + lead_thickness_max^2)
  hole  = diagonal + hole allowance  (A: 0.25, B: 0.20, C: 0.15 mm)
  land  = hole + 2 x min annular ring (0.05) + fabrication allowance
          (A: 0.60, B: 0.50, C: 0.40 mm)

both rounded up to the 0.05 mm grid; the hole never goes below the
datasheet-recommended drill from the CSV.

Pin layout: two parallel rows along Y axis, pins along X.
Pin 1 at top-left, numbered counter-clockwise.
"""

from __future__ import annotations

import csv
import math
import os
from dataclasses import dataclass

from generator.core.ipc_equations import DensityLevel, round_to
from generator.core.naming import density_suffix
from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType,
    write_footprint,
)
from generator.core.layers import add_courtyard, add_fab_body

# IPC-2221/7251 allowances per density level (mm)
_HOLE_ALLOWANCE = {DensityLevel.A: 0.25, DensityLevel.B: 0.20, DensityLevel.C: 0.15}
_FAB_ALLOWANCE = {DensityLevel.A: 0.60, DensityLevel.B: 0.50, DensityLevel.C: 0.40}
_MIN_ANNULAR_RING = 0.05  # per side
_COURTYARD_EXCESS = {DensityLevel.A: 0.50, DensityLevel.B: 0.25, DensityLevel.C: 0.10}


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
    drill: float        # Datasheet-recommended minimum drill diameter

    @property
    def lead_diagonal(self) -> float:
        """Worst-case diagonal of the rectangular lead cross-section."""
        return math.hypot(self.T_max, self.W_max)

    def hole_diameter(self, level: DensityLevel) -> float:
        """Finished hole size per IPC-2221/7251, floored at CSV drill."""
        hole = round_to(self.lead_diagonal + _HOLE_ALLOWANCE[level], 0.05)
        return max(hole, self.drill)

    def pad_diameter(self, level: DensityLevel) -> float:
        """Land diameter: hole + 2x min annular ring + fab allowance."""
        pad = (self.hole_diameter(level) + 2 * _MIN_ANNULAR_RING
               + _FAB_ALLOWANCE[level])
        return round_to(pad, 0.05)


def _dip_ipc_name(spec: DipSpec, level: DensityLevel) -> str:
    rs = f"{round(spec.row_spacing * 100):03d}"
    h = f"{round(spec.body_height * 100):03d}"
    return f"DIP{rs}W{h}P{round(spec.pitch * 100):03d}-{spec.pin_count}{density_suffix(level)}"


def generate_dip_footprint(spec: DipSpec, level: DensityLevel) -> Footprint:
    ipc_name = _dip_ipc_name(spec, level)
    excess = _COURTYARD_EXCESS[level]
    drill = spec.hole_diameter(level)
    pad_dia = spec.pad_diameter(level)

    fp = Footprint(
        name=ipc_name,
        smd=False,
        description=(
            f"Level {level.name} DIP-{spec.pin_count}, "
            f"{spec.row_spacing}mm row spacing. IPC-2221/7251 THT lands: "
            f"hole={drill:.2f} pad={pad_dia:.2f}. "
            f"Courtyard excess={excess:.2f}mm."
        ),
        tags=f"{ipc_name} dip {spec.pin_count}pin through_hole IPC7351B density_{level.name}",
        properties={"IPC_Table": "IPC-2221", "DensityLevel": level.name, "LandForge": "true"},
    )

    pins_per_side = spec.pin_count // 2
    row_cx = spec.row_spacing / 2
    y_start = -spec.pitch * (pins_per_side - 1) / 2

    # Left side (pins 1..N/2, top to bottom)
    for i in range(pins_per_side):
        fp.pads.append(Pad(
            number=str(i + 1),
            pad_type=PadType.THT,
            shape=PadShape.OVAL if i > 0 else PadShape.RECT,  # Pin 1 is rectangular
            x=-row_cx, y=y_start + i * spec.pitch,
            width=pad_dia, height=pad_dia,
            layers=["*.Cu", "*.Mask"],
            drill=drill,
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
            drill=drill,
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
