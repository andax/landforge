"""
IPC-7358 BGA/Area Array Family Generator.

Generates footprints for Ball Grid Array packages:
  BGA (standard pitch >= 1.0mm)
  FBGA (fine pitch < 1.0mm)

Uses Table 3-17 for courtyard excess (2.0/1.0/0.5mm for A/B/C).
Pad diameter calculated via calculate_bga_land_diameter() which uses
percentage-based reduction/increase per IPC-7351B Section 14.

BGA pin naming: alpha rows (A-Z skipping I and O), numeric columns (1-N).
All pads are circular with PadProperty.BGA and NSMD solder mask.

KiCad orientation convention:
  - Component body centered at origin
  - Pin A1 at top-left (negative X, negative Y)
  - Columns increase in +X, rows increase in +Y
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass

from generator.core.ipc_equations import (
    DensityLevel,
    calculate_bga_land_diameter,
)
from generator.core.tables import TABLE_3_17
from generator.core.naming import name_bga
from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType, PadProperty,
    write_footprint,
)
from generator.core.layers import (
    add_courtyard, add_fab_body,
    SILK_WIDTH, SILK_CLEARANCE,
)


# BGA row letters: A-Z skipping I and O (IPC/JEDEC convention)
_BGA_ROW_LETTERS = [c for c in "ABCDEFGHJKLMNPQRSTUVWXYZ"]


def bga_row_name(row_index: int) -> str:
    """Convert a zero-based row index to BGA row letter(s).

    Single letter for rows 0-23 (A-Y skipping I,O), then doubles:
    AA, AB, ... AY, BA, BB, ... for rows >= 24.
    """
    n = len(_BGA_ROW_LETTERS)
    if row_index < n:
        return _BGA_ROW_LETTERS[row_index]
    # Double-letter rows for large BGAs
    first = (row_index // n) - 1
    second = row_index % n
    return _BGA_ROW_LETTERS[first] + _BGA_ROW_LETTERS[second]


@dataclass
class BgaComponentSpec:
    """Specification for a BGA component from the database."""
    pin_count: int       # Total number of balls
    pitch: float         # Ball pitch (mm)
    columns: int         # Number of columns
    rows: int            # Number of rows
    body_length: float   # Body length X (mm)
    body_width: float    # Body width Y (mm)
    body_height: float   # Body height (mm)
    ball_diameter: float # Ball diameter (mm)
    collapsible: bool    # True for collapsible (solder) balls


def generate_bga_footprint(spec: BgaComponentSpec, level: DensityLevel) -> Footprint:
    """Generate a complete BGA footprint.

    Args:
        spec: BGA component specification from database.
        level: Density level (A, B, or C).

    Returns:
        Complete Footprint ready for serialization.
    """
    table = TABLE_3_17

    # Calculate pad diameter using IPC percentage-based method
    pad_diameter = calculate_bga_land_diameter(
        spec.ball_diameter, level, spec.collapsible,
    )

    # NSMD solder mask: pads include F.Mask layer; KiCad applies its own
    # mask expansion (typically 0.05mm per side) for the NSMD opening

    # IPC name
    ipc_name = name_bga(
        pin_count=spec.pin_count,
        pitch=spec.pitch,
        columns=spec.columns,
        rows=spec.rows,
        body_length=spec.body_length,
        body_width=spec.body_width,
        height=spec.body_height,
        level=level,
        collapsible=spec.collapsible,
    )

    ball_type_str = "Collapsible" if spec.collapsible else "Non-collapsible"
    fp = Footprint(
        name=ipc_name,
        description=(
            f"IPC-7351B Level {level.name} BGA, "
            f"{spec.pin_count} balls, {spec.pitch:.2f}mm pitch, "
            f"{spec.columns}x{spec.rows} array, "
            f"{spec.body_length:.1f}x{spec.body_width:.1f}x{spec.body_height:.1f}mm. "
            f"{ball_type_str} ball {spec.ball_diameter:.2f}mm. "
            f"Table 3-17. "
            f"Pad diameter={pad_diameter:.2f}mm. "
            f"Courtyard excess={table.courtyard_excess(level):.2f}mm."
        ),
        tags=(
            f"{ipc_name} BGA {spec.pin_count} "
            f"{spec.pitch}mm IPC7351B density_{level.name}"
        ),
        properties={
            "IPC_Table": table.name,
            "DensityLevel": level.name,
            "LandForge": "true",
        },
    )

    # Calculate grid origin so that the array is centered at (0, 0)
    # Pin A1 is at top-left (most negative X and Y)
    grid_x_extent = (spec.columns - 1) * spec.pitch
    grid_y_extent = (spec.rows - 1) * spec.pitch
    origin_x = -grid_x_extent / 2
    origin_y = -grid_y_extent / 2

    # Generate pads for the full grid
    for row in range(spec.rows):
        row_letter = bga_row_name(row)
        for col in range(spec.columns):
            pin_name = f"{row_letter}{col + 1}"
            x = origin_x + col * spec.pitch
            y = origin_y + row * spec.pitch

            fp.pads.append(Pad(
                number=pin_name,
                pad_type=PadType.SMD,
                shape=PadShape.CIRCLE,
                x=x,
                y=y,
                width=pad_diameter,
                height=pad_diameter,
                layers=["F.Cu", "F.Mask", "F.Paste"],
                roundrect_ratio=None,
                property=PadProperty.BGA,
            ))

    # Courtyard: max of body or pad array extent, plus courtyard excess
    pad_array_x = grid_x_extent + pad_diameter
    pad_array_y = grid_y_extent + pad_diameter
    excess = table.courtyard_excess(level)
    cy_x = max(spec.body_length, pad_array_x) + 2 * excess
    cy_y = max(spec.body_width, pad_array_y) + 2 * excess
    add_courtyard(fp, cy_x, cy_y)

    # Fabrication layer: body outline with pin 1 chamfer
    add_fab_body(fp, spec.body_length, spec.body_width, pin1_chamfer=1.0)

    # Silkscreen: corner marks and pin 1 indicator
    _add_silk_bga(fp, spec, pad_array_x, pad_array_y)

    return fp


def _add_silk_bga(
    fp: Footprint,
    spec: BgaComponentSpec,
    pad_array_x: float,
    pad_array_y: float,
) -> None:
    """Add silkscreen corner marks and pin 1 indicator for BGA.

    BGA silkscreen uses corner marks rather than a full outline,
    since the body often overlaps the pad array. A pin 1 indicator
    (filled circle or line) is placed at the A1 corner.
    """
    from generator.core.kicad_writer import FpLine, FpCircle

    bx2 = spec.body_length / 2
    by2 = spec.body_width / 2

    # Use body outline or pad extent, whichever is larger, plus clearance
    extent_x = max(bx2, pad_array_x / 2 + SILK_CLEARANCE)
    extent_y = max(by2, pad_array_y / 2 + SILK_CLEARANCE)

    # Silk position just outside the body/pads
    sx = extent_x + SILK_WIDTH / 2
    sy = extent_y + SILK_WIDTH / 2

    # Corner mark length (proportional to body, capped)
    mark_len = min(1.0, spec.body_length * 0.1, spec.body_width * 0.1)
    mark_len = max(mark_len, 0.5)

    # Four corner marks (L-shaped)
    corners = [
        (-sx, -sy, -sx + mark_len, -sx, -sy + mark_len),  # top-left
        (sx, -sy, sx - mark_len, sx, -sy + mark_len),      # top-right
        (-sx, sy, -sx + mark_len, -sx, sy - mark_len),     # bottom-left
        (sx, sy, sx - mark_len, sx, sy - mark_len),        # bottom-right
    ]
    for cx, cy, hx, vx, vy in corners:
        # Horizontal stroke
        fp.lines.append(FpLine(cx, cy, hx, cy, "F.SilkS", SILK_WIDTH))
        # Vertical stroke
        fp.lines.append(FpLine(cx, cy, vx, vy, "F.SilkS", SILK_WIDTH))

    # Pin 1 indicator: filled circle near top-left corner
    pin1_x = -sx - 0.3
    pin1_y = -sy - 0.3
    fp.circles.append(FpCircle(
        cx=pin1_x, cy=pin1_y,
        radius=0.15,
        layer="F.SilkS",
        width=SILK_WIDTH,
        fill=True,
    ))


def load_bga_database(csv_path: str) -> list[BgaComponentSpec]:
    """Load BGA component specifications from CSV database."""
    specs = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            specs.append(BgaComponentSpec(
                pin_count=int(row["pin_count"]),
                pitch=float(row["pitch"]),
                columns=int(row["columns"]),
                rows=int(row["rows"]),
                body_length=float(row["body_length"]),
                body_width=float(row["body_width"]),
                body_height=float(row["body_height"]),
                ball_diameter=float(row["ball_diameter"]),
                collapsible=row["collapsible"].strip().lower() == "true",
            ))
    return specs


def generate_bga_library(csv_path: str, output_dir: str) -> int:
    """Generate all BGA footprints from database.

    Args:
        csv_path: Path to bga_components.csv.
        output_dir: Path to output .pretty directory.

    Returns:
        Number of footprints generated.
    """
    os.makedirs(output_dir, exist_ok=True)
    specs = load_bga_database(csv_path)
    count = 0

    for spec in specs:
        for level in DensityLevel:
            fp = generate_bga_footprint(spec, level)
            path = os.path.join(output_dir, f"{fp.name}.kicad_mod")
            write_footprint(fp, path)
            count += 1

    return count
