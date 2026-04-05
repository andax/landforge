"""
IPC-7351B Land Pattern Tolerance Equations.

Implements the core dimensioning system from IPC-7351B Section 3.1.5:
  Z_max = L_min + 2*J_T + sqrt(CL^2 + F^2 + P^2)   (overall land pattern span)
  G_min = S_max - 2*J_H - sqrt(CS^2 + F^2 + P^2)    (gap between lands)
  X_max = W_min + 2*J_S + sqrt(CW^2 + F^2 + P^2)    (land width)

Where:
  L = overall component length, S = distance between terminations, W = lead width
  J_T/J_H/J_S = solder fillet goals (toe/heel/side) from density level tables
  CL/CS/CW = component tolerances
  F = fabrication tolerance (default 0.05 mm)
  P = placement tolerance (default 0.05 mm)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple


class DensityLevel(Enum):
    """IPC-7351B density levels (Section 1.3.1)."""
    A = "M"  # Most (Maximum) land protrusion
    B = "N"  # Nominal (Median) land protrusion
    C = "L"  # Least (Minimum) land protrusion


class FilletGoals(NamedTuple):
    """Solder fillet goals (J_T, J_H, J_S) for a given density level."""
    toe: float   # J_T - land protrusion beyond lead at toe
    heel: float  # J_H - land protrusion beyond lead at heel
    side: float  # J_S - land protrusion beyond lead at side


class CourtyardExcess(NamedTuple):
    """Courtyard excess per density level."""
    A: float
    B: float
    C: float


@dataclass
class ToleranceTable:
    """An IPC-7351B tolerance table (Tables 3-2 through 3-22).

    Each table provides fillet goals and courtyard excess for all three
    density levels, plus a round-off factor.
    """
    name: str
    description: str
    fillet_A: FilletGoals
    fillet_B: FilletGoals
    fillet_C: FilletGoals
    courtyard: CourtyardExcess
    roundoff: float = 0.05  # mm, default rounding increment

    def fillet(self, level: DensityLevel) -> FilletGoals:
        """Get fillet goals for a density level."""
        return {
            DensityLevel.A: self.fillet_A,
            DensityLevel.B: self.fillet_B,
            DensityLevel.C: self.fillet_C,
        }[level]

    def courtyard_excess(self, level: DensityLevel) -> float:
        """Get courtyard excess for a density level."""
        return {
            DensityLevel.A: self.courtyard.A,
            DensityLevel.B: self.courtyard.B,
            DensityLevel.C: self.courtyard.C,
        }[level]


@dataclass
class ComponentDimensions:
    """Component dimensions extracted from datasheet/JEDEC outline.

    All dimensions in mm. Min/max values define the tolerance range.
    """
    L_min: float  # Overall length (outer extremity), minimum
    L_max: float  # Overall length (outer extremity), maximum
    S_min: float  # Distance between terminations (inner), minimum
    S_max: float  # Distance between terminations (inner), maximum
    W_min: float  # Lead/termination width, minimum
    W_max: float  # Lead/termination width, maximum

    @property
    def CL(self) -> float:
        """Component tolerance on overall length."""
        return self.L_max - self.L_min

    @property
    def CS(self) -> float:
        """Component tolerance on termination distance."""
        return self.S_max - self.S_min

    @property
    def CW(self) -> float:
        """Component tolerance on lead width."""
        return self.W_max - self.W_min


@dataclass
class ComponentDimensionsFromSpec:
    """Build ComponentDimensions from typical datasheet specifications.

    Datasheets often give L, T (terminal length), W with tolerances, rather
    than S directly. This class derives S using RMS tolerance accumulation
    (IPC-7351B Section 3.1.1, page 11).
    """
    L_min: float
    L_max: float
    T_min: float  # Terminal/lead length, minimum
    T_max: float  # Terminal/lead length, maximum
    W_min: float
    W_max: float

    def to_component_dimensions(self) -> ComponentDimensions:
        """Convert to ComponentDimensions with RMS-adjusted S values.

        Uses RMS tolerance accumulation per IPC-7351B page 11:
          S_tol(RMS) = sqrt(L_tol^2 + 2*T_tol^2)

        The difference between worst-case and RMS is split and applied
        to adjust S_max (down) and S_min (up) for realistic tolerances.
        """
        L_tol = self.L_max - self.L_min
        T_tol = self.T_max - self.T_min

        # Worst-case S range
        S_min_worst = self.L_min - 2 * self.T_max
        S_max_worst = self.L_max - 2 * self.T_min

        # RMS tolerance
        S_tol_rms = math.sqrt(L_tol**2 + 2 * T_tol**2)

        # Worst-case tolerance
        S_tol_worst = S_max_worst - S_min_worst

        # Split the difference between worst-case and RMS
        adjustment = (S_tol_worst - S_tol_rms) / 2

        S_min = S_min_worst + adjustment
        S_max = S_max_worst - adjustment

        return ComponentDimensions(
            L_min=self.L_min,
            L_max=self.L_max,
            S_min=S_min,
            S_max=S_max,
            W_min=self.W_min,
            W_max=self.W_max,
        )


@dataclass
class LandPatternResult:
    """Result of land pattern calculation.

    Z, G, X are the three fundamental dimensions; pad_length, pad_width,
    and pad_center_to_center are derived for direct use in footprint generation.

    Note: IPC-7351B rounds Z, G, X to the 0.05mm grid, but the derived pad
    dimensions (pad_length, pad_center_to_center) end up on a 0.025mm grid
    because they are (Z±G)/2. An optional post-rounding step to snap derived
    dimensions to 0.05mm would align with KiCad stock library practice but is
    not required by the standard.
    """
    Z: float  # Overall land pattern span (outer extremity to outer extremity)
    G: float  # Gap between lands (inner edge to inner edge)
    X: float  # Land width

    @property
    def pad_length(self) -> float:
        """Individual pad length (in the direction of component length)."""
        return (self.Z - self.G) / 2

    @property
    def pad_width(self) -> float:
        """Individual pad width."""
        return self.X

    @property
    def pad_center_to_center(self) -> float:
        """Distance between pad centers."""
        return (self.Z + self.G) / 2


def round_to(value: float, increment: float) -> float:
    """Round a value UP to the nearest increment.

    IPC-7351B rounding rules:
      - Standard: round to nearest 0.05 mm
      - Small chip (< 0603): round to nearest 0.02 mm

    For Z (outer) and X (width): round UP.
    Uses integer arithmetic to avoid floating-point precision issues.
    """
    # Work in integer micrometers to avoid float imprecision
    inc_um = round(increment * 1e6)
    val_um = round(value * 1e6)
    remainder = val_um % inc_um
    if remainder == 0:
        return val_um / 1e6
    return (val_um + inc_um - remainder) / 1e6


def round_down_to(value: float, increment: float) -> float:
    """Round a value DOWN to the nearest increment.

    For G (inner/gap): round DOWN.
    """
    inc_um = round(increment * 1e6)
    val_um = round(value * 1e6)
    return (val_um - val_um % inc_um) / 1e6


def calculate_land_pattern(
    comp: ComponentDimensions,
    table: ToleranceTable,
    level: DensityLevel,
    fab_tol: float = 0.05,
    place_tol: float = 0.05,
) -> LandPatternResult:
    """Calculate land pattern dimensions using IPC-7351B equations.

    This is the core calculation from Section 3.1.5:
      Z_max = L_min + 2*J_T + sqrt(CL^2 + F^2 + P^2)
      G_min = S_max - 2*J_H - sqrt(CS^2 + F^2 + P^2)
      X_max = W_min + 2*J_S + sqrt(CW^2 + F^2 + P^2)

    Args:
        comp: Component dimensions with min/max tolerances.
        table: IPC tolerance table for this component family.
        level: Density level (A, B, or C).
        fab_tol: Fabrication tolerance F (default 0.05 mm).
        place_tol: Placement tolerance P (default 0.05 mm).

    Returns:
        LandPatternResult with Z, G, X dimensions rounded per IPC rules.
    """
    fillet = table.fillet(level)
    r = table.roundoff

    # Tolerance RSS (root sum of squares) terms
    rss_L = math.sqrt(comp.CL**2 + fab_tol**2 + place_tol**2)
    rss_S = math.sqrt(comp.CS**2 + fab_tol**2 + place_tol**2)
    rss_W = math.sqrt(comp.CW**2 + fab_tol**2 + place_tol**2)

    # Core equations
    Z_raw = comp.L_min + 2 * fillet.toe + rss_L
    G_raw = comp.S_max - 2 * fillet.heel - rss_S
    X_raw = comp.W_min + 2 * fillet.side + rss_W

    # Round per IPC rules: Z and X round up, G rounds down
    Z = round_to(Z_raw, r)
    G = round_down_to(G_raw, r)
    X = round_to(X_raw, r)

    return LandPatternResult(Z=Z, G=G, X=X)


def calculate_courtyard(
    body_width: float,
    body_length: float,
    land_pattern: LandPatternResult,
    table: ToleranceTable,
    level: DensityLevel,
    grid: float = 0.05,
) -> tuple[float, float]:
    """Calculate courtyard dimensions per IPC-7351B.

    Courtyard = max(component_body, land_pattern_extent) + courtyard_excess
    on each side, snapped to grid.

    Args:
        body_width: Component body width (perpendicular to leads).
        body_length: Component body length (parallel to leads / overall).
        land_pattern: Calculated land pattern result.
        table: Tolerance table (for courtyard excess).
        level: Density level.
        grid: Courtyard grid snap (default 0.05 mm).

    Returns:
        (courtyard_width, courtyard_length) tuple.
    """
    excess = table.courtyard_excess(level)

    # Courtyard spans the larger of body or land pattern, plus excess on each side
    cy_length = max(body_length, land_pattern.Z) + 2 * excess
    cy_width = max(body_width, land_pattern.X) + 2 * excess

    # Snap to grid (round up)
    cy_length = round_to(cy_length, grid)
    cy_width = round_to(cy_width, grid)

    return cy_width, cy_length


# --- BGA/Periphery-based calculations (Tables 3-17, 3-18) ---

def calculate_bga_land_diameter(
    ball_diameter: float,
    level: DensityLevel,
    collapsible: bool = True,
) -> float:
    """Calculate BGA land pad diameter per IPC-7351B Table 3-17.

    For collapsible balls: land = ball_diameter * (1 - reduction%)
    For non-collapsible: land = ball_diameter * (1 + increase%)

    The percentage depends on density level and ball size.
    """
    if collapsible:
        # Table 14-5: reduction percentages for collapsible balls
        if ball_diameter >= 0.65:
            pct = {DensityLevel.A: 0.25, DensityLevel.B: 0.20, DensityLevel.C: 0.15}
        elif ball_diameter >= 0.35:
            pct = {DensityLevel.A: 0.20, DensityLevel.B: 0.15, DensityLevel.C: 0.10}
        else:
            pct = {DensityLevel.A: 0.15, DensityLevel.B: 0.10, DensityLevel.C: 0.05}
        return round_to(ball_diameter * (1 - pct[level]), 0.05)
    else:
        # Table 14-6: increase percentages for non-collapsible balls
        if ball_diameter >= 0.55:
            pct = {DensityLevel.A: 0.15, DensityLevel.B: 0.10, DensityLevel.C: 0.05}
        elif ball_diameter >= 0.30:
            pct = {DensityLevel.A: 0.10, DensityLevel.B: 0.05, DensityLevel.C: 0.00}
        else:
            pct = {DensityLevel.A: 0.05, DensityLevel.B: 0.00, DensityLevel.C: -0.05}
        return round_to(ball_diameter * (1 + pct[level]), 0.05)


def calculate_periphery_land(
    terminal_width: float,
    terminal_length: float,
    table: ToleranceTable,
    level: DensityLevel,
    fab_tol: float = 0.05,
    place_tol: float = 0.05,
) -> tuple[float, float]:
    """Calculate land dimensions for periphery-based packages (PQFN, PSON, DFN).

    These packages use a single 'periphery' tolerance added uniformly.
    Table 3-18 provides the periphery goal per density level in the toe field.

    Returns:
        (pad_width, pad_length) tuple.
    """
    fillet = table.fillet(level)
    periphery = fillet.toe  # For periphery-based, toe holds the periphery value

    rss = math.sqrt(fab_tol**2 + place_tol**2)

    pad_width = round_to(terminal_width + 2 * periphery + rss, table.roundoff)
    pad_length = round_to(terminal_length + 2 * periphery + rss, table.roundoff)

    return pad_width, pad_length
