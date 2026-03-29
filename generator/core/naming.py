"""
IPC-7351B Land Pattern Naming Convention (Table 3-23).

Encodes component dimensions into standardized IPC names like:
  RESC1608X55N    (chip resistor, 1.6x0.8mm body, 0.55mm height, nominal)
  SOIC127P600X175-8N  (SOIC, 1.27mm pitch, 6.00mm span, 1.75mm height, 8 pins, nominal)
  BGA100C100P10X10_1200X1200X185N  (BGA, 100 pins, collapsible, 1.0mm pitch, ...)

Formatting rules from IPC-7351B Table 3-23:
  - Chip body sizes: 1 digit.1 digit (e.g., 1.6 -> "1.6", 0.8 -> "0.8")
  - Lead span/height: 2 digits before decimal, 2 after, no decimal point
    (e.g., 6.00 -> "600", 1.75 -> "175", 0.55 -> "055")
  - Pitch: same as lead span/height format
  - Pin count: plain integer
  - Density suffix: M (most), N (nominal), L (least)
"""

from __future__ import annotations

from .ipc_equations import DensityLevel


def _chip_dim(value: float) -> str:
    """Format a chip component body dimension.

    IPC convention: dimensions in tenths of mm, two digits, no decimal point.
    Examples: 1.6 -> "16", 0.8 -> "08", 3.2 -> "32", 0.4 -> "04"
    """
    tenths = round(value * 10)
    return f"{tenths:02d}"


def _span_dim(value: float) -> str:
    """Format a lead span, height, or pitch dimension.

    Two digits before decimal, two after, concatenated without decimal point.
    Leading zeros preserved, trailing zeros preserved.

    Examples: 6.00 -> "600", 1.75 -> "175", 0.55 -> "055", 1.27 -> "127"
    """
    # Multiply by 100 to get integer representation
    val_int = round(value * 100)
    return f"{val_int:03d}"


def _pitch_dim(value: float) -> str:
    """Format a pitch dimension. Same rules as span."""
    return _span_dim(value)


def density_suffix(level: DensityLevel) -> str:
    """Get the IPC naming suffix for a density level."""
    return level.value  # M, N, or L


def name_chip(
    prefix: str,
    body_length: float,
    body_width: float,
    height: float,
    level: DensityLevel,
) -> str:
    """Generate IPC name for a 2-terminal chip component.

    Format: {PREFIX}{BodyL}{BodyW}X{Height}{Density}
    Example: RESC1608X55N
    """
    bl = _chip_dim(body_length)
    bw = _chip_dim(body_width)
    h = _span_dim(height)
    return f"{prefix}{bl}{bw}X{h}{density_suffix(level)}"


def name_leaded_2side(
    prefix: str,
    pitch: float,
    lead_span: float,
    height: float,
    pin_count: int,
    level: DensityLevel,
) -> str:
    """Generate IPC name for a 2-side leaded component.

    Format: {PREFIX}{Pitch}P{LeadSpan}X{Height}-{PinQty}{Density}
    Example: SOIC127P600X175-8N
    """
    p = _pitch_dim(pitch)
    ls = _span_dim(lead_span)
    h = _span_dim(height)
    return f"{prefix}{p}P{ls}X{h}-{pin_count}{density_suffix(level)}"


def name_qfp(
    pitch: float,
    lead_span_x: float,
    lead_span_y: float,
    height: float,
    pin_count: int,
    level: DensityLevel,
    prefix: str = "QFP",
) -> str:
    """Generate IPC name for a 4-side leaded component (QFP).

    Format: QFP{Pitch}P{SpanX}X{SpanY}X{Height}-{PinQty}{Density}
    Example: QFP50P700X700X120-48N
    """
    p = _pitch_dim(pitch)
    sx = _span_dim(lead_span_x)
    sy = _span_dim(lead_span_y)
    h = _span_dim(height)
    return f"{prefix}{p}P{sx}X{sy}X{h}-{pin_count}{density_suffix(level)}"


def name_bga(
    pin_count: int,
    pitch: float,
    columns: int,
    rows: int,
    body_length: float,
    body_width: float,
    height: float,
    level: DensityLevel,
    collapsible: bool = True,
) -> str:
    """Generate IPC name for a BGA component.

    Format: BGA{PinQty}{C/N}{Pitch}P{Cols}X{Rows}_{BodyL}X{BodyW}X{Height}{Density}
    Example: BGA100C100P10X10_1200X1200X185N
    """
    ball_type = "C" if collapsible else "N"
    p = _pitch_dim(pitch)
    bl = _span_dim(body_length)
    bw = _span_dim(body_width)
    h = _span_dim(height)
    return (
        f"BGA{pin_count}{ball_type}{p}P{columns}X{rows}"
        f"_{bl}X{bw}X{h}{density_suffix(level)}"
    )


def name_nolead(
    prefix: str,
    pitch: float,
    body_width: float,
    body_length: float,
    height: float,
    pin_count: int,
    level: DensityLevel,
    thermal_pad: float | None = None,
) -> str:
    """Generate IPC name for a no-lead component (QFN, SON, DFN).

    Format: {PREFIX}{Pitch}P{BodyW}X{BodyL}X{Height}-{PinQty}{+ThermalPad}{Density}
    Example: QFN50P500X500X100-33T340N
    """
    p = _pitch_dim(pitch)
    bw = _span_dim(body_width)
    bl = _span_dim(body_length)
    h = _span_dim(height)
    tp = ""
    if thermal_pad is not None:
        tp = f"T{_span_dim(thermal_pad)}"
    return f"{prefix}{p}P{bw}X{bl}X{h}-{pin_count}{tp}{density_suffix(level)}"


def name_sot(
    pitch: float,
    lead_span: float,
    height: float,
    pin_count: int,
    level: DensityLevel,
) -> str:
    """Generate IPC name for SOT packages.

    Format: SOT{Pitch}P{LeadSpan}X{Height}-{PinQty}{Density}
    Example: SOT95P240X110-3N
    """
    return name_leaded_2side("SOT", pitch, lead_span, height, pin_count, level)


def name_sod(
    lead_span: float,
    body_width: float,
    height: float,
    level: DensityLevel,
) -> str:
    """Generate IPC name for SOD packages.

    Format: SOD{LeadSpan}{BodyW}X{Height}{Density}
    Example: SOD2513X100N
    """
    ls = _span_dim(lead_span)
    bw = _chip_dim(body_width)
    h = _span_dim(height)
    return f"SOD{ls}{bw}X{h}{density_suffix(level)}"
