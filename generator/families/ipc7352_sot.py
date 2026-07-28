"""
IPC-7352 SOT/SOD/DPAK Family Generator.

Generates footprints for small-outline transistors, diodes, and power packages:
  SOT23 (3/5/6 pin), SOT89, SOT143, SOT223, SOD123/323/523,
  DPAK (TO-252), D2PAK (TO-263)

SOT/SOD use Table 3-2 (gull-wing, pitch > 0.625mm).
DPAK uses Table 3-14 (flat lug leads) for signal leads and thermal tab.

Thermal tabs (SOT-89, SOT-223, DPAK, D2PAK) are flat leads on the side
opposite the signal leads (IPC-7351B 8.11: "gull-wing type leads on one
side and a flat lead on the other side"). The tab land is computed with
the same Z/G/X machinery as the signal leads -- same lead span L and
family fillet goals, but the tab's own contact length (tab_T) and width
(tab_W) -- and placed at +X so its outer edge lands on the pattern
extent Z/2, mirroring the signal lead treatment.

These are the first multi-pin packages. Each package has a fixed pin arrangement
defined in the database, not just a 2-terminal mirror like chip components.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field

from generator.core.ipc_equations import (
    DensityLevel,
    ComponentDimensionsFromSpec,
    calculate_land_pattern,
)
from generator.core.tables import TABLE_3_2, TABLE_3_14, TABLE_3_22
from generator.core.naming import name_sot, name_sod, density_suffix
from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType, PadProperty,
    write_footprint,
)
from generator.core.layers import (
    add_courtyard, add_fab_body, add_silk_ic, add_polarity_mark,
    SILK_WIDTH, SILK_CLEARANCE,
)
from generator.core.paste import add_thermal_paste


@dataclass
class PinPosition:
    """A pin's position relative to component center."""
    number: str
    x: float  # Relative X from center
    y: float  # Relative Y from center


@dataclass
class SotSpec:
    """SOT/SOD/DPAK package specification."""
    name: str           # Human name: SOT-23, SOD-123, DPAK
    body_width: float   # Body width (X, between lead rows)
    body_length: float  # Body length (Y, along lead row)
    body_height: float  # Body height
    pitch: float        # Lead pitch
    lead_span: float    # Lead tip-to-tip span (across body)
    pin_count: int
    # Lead dimensions for IPC calculation
    L_min: float        # Overall lead span, min
    L_max: float        # Overall lead span, max
    T_min: float        # Lead length (terminal), min
    T_max: float        # Lead length (terminal), max
    W_min: float        # Lead width, min
    W_max: float        # Lead width, max
    # Pin layout: list of (pin_number, x_side, y_offset) where
    # x_side is -1 (left) or +1 (right), y_offset is from center
    pins: list[tuple[str, int, float]] = field(default_factory=list)
    table: str = "3-2"  # Which IPC table to use
    has_thermal_tab: bool = False
    tab_T_min: float = 0.0  # Tab contact length along X, min
    tab_T_max: float = 0.0
    tab_W_min: float = 0.0  # Tab width along Y, min
    tab_W_max: float = 0.0
    is_diode: bool = False

    def get_table(self):
        from generator.core.tables import TABLES
        return TABLES[self.table]

    def to_ipc_dims(self) -> ComponentDimensionsFromSpec:
        return ComponentDimensionsFromSpec(
            L_min=self.L_min, L_max=self.L_max,
            T_min=self.T_min, T_max=self.T_max,
            W_min=self.W_min, W_max=self.W_max,
        )

    def to_tab_ipc_dims(self) -> ComponentDimensionsFromSpec:
        """Tab treated as a flat lead: same span L, tab contact dims."""
        return ComponentDimensionsFromSpec(
            L_min=self.L_min, L_max=self.L_max,
            T_min=self.tab_T_min, T_max=self.tab_T_max,
            W_min=self.tab_W_min, W_max=self.tab_W_max,
        )


def _sot_ipc_name(spec: SotSpec, level: DensityLevel) -> str:
    """Generate IPC name for SOT/SOD packages."""
    if spec.is_diode:
        return name_sod(spec.lead_span, spec.body_length, spec.body_height, level)
    return name_sot(spec.pitch, spec.lead_span, spec.body_height, spec.pin_count, level)


def generate_sot_footprint(spec: SotSpec, level: DensityLevel) -> Footprint:
    """Generate a multi-pin SOT/SOD/DPAK footprint."""
    table = spec.get_table()
    comp = spec.to_ipc_dims().to_component_dimensions()
    lp = calculate_land_pattern(comp, table, level)

    # Tab land: same span and fillet goals, tab contact dimensions
    lp_tab = None
    if spec.has_thermal_tab:
        tab_comp = spec.to_tab_ipc_dims().to_component_dimensions()
        lp_tab = calculate_land_pattern(tab_comp, table, level)

    ipc_name = _sot_ipc_name(spec, level)

    # Calculate courtyard
    cy_x = max(spec.body_width, lp.Z) + 2 * table.courtyard_excess(level)
    # Y extent: body length, outermost pin edge, or tab width
    max_pin_y = max(abs(y) for _, _, y in spec.pins) if spec.pins else 0
    cy_y = max(spec.body_length, max_pin_y * 2 + lp.X) + 2 * table.courtyard_excess(level)

    if lp_tab is not None:
        cy_y = max(cy_y, lp_tab.X + 2 * table.courtyard_excess(level))

    fp = Footprint(
        name=ipc_name,
        description=(
            f"IPC-7351B Level {level.name} {spec.name}. "
            f"Table {table.name}. Z={lp.Z:.2f} G={lp.G:.2f} X={lp.X:.2f}. "
            f"Courtyard excess={table.courtyard_excess(level):.2f}mm."
        ),
        tags=(
            f"{ipc_name} {spec.name.lower()} "
            f"IPC7351B density_{level.name}"
        ),
        properties={
            "IPC_Table": table.name, "DensityLevel": level.name, "LandForge": "true",
        },
    )

    # Place signal pads according to pin layout
    pad_cx = lp.pad_center_to_center / 2

    for pin_num, x_side, y_offset in spec.pins:
        fp.pads.append(Pad(
            number=pin_num,
            pad_type=PadType.SMD,
            shape=PadShape.ROUNDRECT,
            x=x_side * pad_cx,
            y=y_offset,
            width=lp.pad_length,
            height=lp.pad_width,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))

    # Thermal tab (DPAK, D2PAK, SOT-89, SOT-223): flat lead on the +X
    # side. Outer edge lands on Z/2 like any lead; length and width come
    # from the tab's own contact dimensions through the same equations.
    if lp_tab is not None:
        tab_cx = lp_tab.pad_center_to_center / 2
        fp.pads.append(Pad(
            number=str(len(spec.pins) + 1),
            pad_type=PadType.SMD,
            shape=PadShape.ROUNDRECT,
            x=tab_cx, y=0,
            width=lp_tab.pad_length,
            height=lp_tab.pad_width,
            layers=["F.Cu", "F.Mask"],  # Paste segmented per 3.1.5.7
            roundrect_ratio=0.1,
            property=PadProperty.HEATSINK,
        ))
        add_thermal_paste(fp, tab_cx, 0, lp_tab.pad_length, lp_tab.pad_width)

    # Layers
    add_courtyard(fp, cy_x, cy_y)

    chamfer = 0.3 if not spec.is_diode else 0
    add_fab_body(fp, spec.body_width, spec.body_length, pin1_chamfer=chamfer)

    if spec.is_diode:
        add_polarity_mark(fp, -spec.body_width / 2 + 0.2, 0)

    # Silkscreen
    pad_x_extent = pad_cx + lp.pad_length / 2
    pad_y_extent = max(abs(y) + lp.pad_width / 2 for _, _, y in spec.pins) if spec.pins else lp.pad_width / 2
    if lp_tab is not None:
        pad_x_extent = max(pad_x_extent,
                           lp_tab.pad_center_to_center / 2 + lp_tab.pad_length / 2)
        pad_y_extent = max(pad_y_extent, lp_tab.pad_width / 2)
    add_silk_ic(fp, spec.body_width, spec.body_length, pad_x_extent, pad_y_extent)

    return fp


def load_sot_database(csv_path: str) -> list[SotSpec]:
    """Load SOT/SOD/DPAK specs from CSV.

    The CSV has a 'pins' column with the pin layout encoded as:
      pin_num:x_side:y_offset;pin_num:x_side:y_offset;...
    Example for SOT-23: "1:-1:-0.95;2:-1:0.95;3:1:0"
    """
    specs = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            pins = []
            for pin_str in row["pins"].split(";"):
                parts = pin_str.strip().split(":")
                pins.append((parts[0], int(parts[1]), float(parts[2])))

            specs.append(SotSpec(
                name=row["name"],
                body_width=float(row["body_width"]),
                body_length=float(row["body_length"]),
                body_height=float(row["body_height"]),
                pitch=float(row["pitch"]),
                lead_span=float(row["lead_span"]),
                pin_count=int(row["pin_count"]),
                L_min=float(row["L_min"]),
                L_max=float(row["L_max"]),
                T_min=float(row["T_min"]),
                T_max=float(row["T_max"]),
                W_min=float(row["W_min"]),
                W_max=float(row["W_max"]),
                pins=pins,
                table=row.get("table", "3-2"),
                has_thermal_tab=row.get("has_thermal_tab", "false").lower() == "true",
                tab_T_min=float(row.get("tab_T_min", "0")),
                tab_T_max=float(row.get("tab_T_max", "0")),
                tab_W_min=float(row.get("tab_W_min", "0")),
                tab_W_max=float(row.get("tab_W_max", "0")),
                is_diode=row.get("is_diode", "false").lower() == "true",
            ))
    return specs


def generate_sot_library(csv_path: str, output_dir: str) -> int:
    os.makedirs(output_dir, exist_ok=True)
    specs = load_sot_database(csv_path)
    count = 0
    for spec in specs:
        for level in DensityLevel:
            fp = generate_sot_footprint(spec, level)
            write_footprint(fp, os.path.join(output_dir, f"{fp.name}.kicad_mod"))
            count += 1
    return count
