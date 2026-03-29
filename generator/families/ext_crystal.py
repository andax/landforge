"""
Extended: SMD Crystal and Oscillator Generator.

2-pin SMD crystals use chip-style pads (Table 3-5).
4-pin SMD crystals/oscillators use a rectangular 4-pad pattern.

Reuses the chip component generator for 2-pin, and a custom layout for 4-pin.
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
from generator.core.tables import TABLE_3_5
from generator.core.naming import density_suffix
from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType,
    write_footprint,
)
from generator.core.layers import add_courtyard, add_fab_body, add_silk_chip


@dataclass
class CrystalSpec:
    size_code: str      # e.g., "3225", "5032"
    pins: int           # 2 or 4
    body_width: float   # X dimension
    body_length: float  # Y dimension
    body_height: float
    L_min: float        # Overall terminal span (X), min
    L_max: float
    T_min: float        # Terminal length, min
    T_max: float
    W_min: float        # Terminal width (Y), min
    W_max: float
    # For 4-pin: pin spacing in Y
    pin_pitch_y: float = 0.0  # Distance between pad rows in Y (for 4-pin)

    def to_ipc_dims(self) -> ComponentDimensionsFromSpec:
        return ComponentDimensionsFromSpec(
            L_min=self.L_min, L_max=self.L_max,
            T_min=self.T_min, T_max=self.T_max,
            W_min=self.W_min, W_max=self.W_max,
        )


def _crystal_name(spec: CrystalSpec, level: DensityLevel) -> str:
    prefix = "XTAL" if spec.pins == 2 else "OSCL"
    bw = f"{round(spec.body_width * 100):03d}"
    bl = f"{round(spec.body_length * 100):03d}"
    h = f"{round(spec.body_height * 100):03d}"
    return f"{prefix}{bw}X{bl}X{h}-{spec.pins}{density_suffix(level)}"


def generate_crystal_footprint(spec: CrystalSpec, level: DensityLevel) -> Footprint:
    table = TABLE_3_5
    comp = spec.to_ipc_dims().to_component_dimensions()
    lp = calculate_land_pattern(comp, table, level)
    excess = table.courtyard_excess(level)

    ipc_name = _crystal_name(spec, level)
    desc_type = "SMD Crystal" if spec.pins == 2 else "SMD Crystal Oscillator"

    fp = Footprint(
        name=ipc_name,
        description=(
            f"IPC-7351B Level {level.name} {desc_type} {spec.size_code}, "
            f"{spec.pins}-pin. Table 3-5. "
            f"Z={lp.Z:.2f} G={lp.G:.2f} X={lp.X:.2f}. "
            f"Courtyard excess={excess:.2f}mm."
        ),
        tags=(
            f"{ipc_name} crystal oscillator {spec.size_code} "
            f"{spec.pins}pin smd IPC7351B density_{level.name}"
        ),
        properties={"IPC_Table": "3-5", "DensityLevel": level.name, "LandForge": "true"},
    )

    pad_cx = lp.pad_center_to_center / 2

    if spec.pins == 2:
        # Same as chip component: two pads along X
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
        cy_x = max(spec.body_width, lp.Z) + 2 * excess
        cy_y = max(spec.body_length, lp.X) + 2 * excess

    else:  # 4-pin
        # 4 pads in rectangular pattern
        # Pins: 1=bottom-left, 2=bottom-right, 3=top-right, 4=top-left (CCW from BL)
        # Or more standard: 1=top-left, 2=bottom-left, 3=bottom-right, 4=top-right
        py = spec.pin_pitch_y / 2

        fp.pads.append(Pad(
            number="1", pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=-pad_cx, y=-py,
            width=lp.pad_length, height=lp.pad_width,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))
        fp.pads.append(Pad(
            number="2", pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=-pad_cx, y=py,
            width=lp.pad_length, height=lp.pad_width,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))
        fp.pads.append(Pad(
            number="3", pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=pad_cx, y=py,
            width=lp.pad_length, height=lp.pad_width,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))
        fp.pads.append(Pad(
            number="4", pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=pad_cx, y=-py,
            width=lp.pad_length, height=lp.pad_width,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))
        cy_x = max(spec.body_width, lp.Z) + 2 * excess
        cy_y = max(spec.body_length, spec.pin_pitch_y + lp.pad_width) + 2 * excess

    add_courtyard(fp, cy_x, cy_y)
    add_fab_body(fp, spec.body_width, spec.body_length, pin1_chamfer=0.3)

    if spec.pins == 2:
        pad_x_extent = pad_cx + lp.pad_length / 2
        pad_y_extent = lp.pad_width / 2
        add_silk_chip(fp, spec.body_width, pad_x_extent, pad_y_extent)

    return fp


def load_crystal_database(csv_path: str) -> list[CrystalSpec]:
    specs = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            specs.append(CrystalSpec(
                size_code=row["size_code"],
                pins=int(row["pins"]),
                body_width=float(row["body_width"]),
                body_length=float(row["body_length"]),
                body_height=float(row["body_height"]),
                L_min=float(row["L_min"]),
                L_max=float(row["L_max"]),
                T_min=float(row["T_min"]),
                T_max=float(row["T_max"]),
                W_min=float(row["W_min"]),
                W_max=float(row["W_max"]),
                pin_pitch_y=float(row.get("pin_pitch_y", "0")),
            ))
    return specs


def generate_crystal_library(csv_path: str, output_dir: str) -> int:
    os.makedirs(output_dir, exist_ok=True)
    specs = load_crystal_database(csv_path)
    count = 0
    for spec in specs:
        for level in DensityLevel:
            fp = generate_crystal_footprint(spec, level)
            write_footprint(fp, os.path.join(output_dir, f"{fp.name}.kicad_mod"))
            count += 1
    return count
