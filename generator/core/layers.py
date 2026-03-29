"""
Layer geometry generators for KiCad footprints.

Generates silkscreen, courtyard, and fabrication layer elements
following IPC-7351B and KiCad conventions.
"""

from __future__ import annotations

from .kicad_writer import (
    Footprint, FpLine, FpRect, FpCircle, FpText, Pad,
)
from .ipc_equations import LandPatternResult, round_to


# --- Constants ---

SILK_WIDTH = 0.12       # mm, silkscreen line width
SILK_CLEARANCE = 0.10   # mm, minimum clearance from silkscreen to pad edge
CRTYD_WIDTH = 0.05      # mm, courtyard line width
CRTYD_GRID = 0.05       # mm, courtyard grid snap
FAB_WIDTH = 0.10        # mm, fabrication layer line width


def add_courtyard(
    fp: Footprint,
    x_span: float,
    y_span: float,
) -> None:
    """Add courtyard rectangle to footprint.

    Args:
        fp: Footprint to modify.
        x_span: Total courtyard extent in X direction.
        y_span: Total courtyard extent in Y direction.
    """
    # Snap half-extents to grid
    x2 = round_to(x_span / 2, CRTYD_GRID)
    y2 = round_to(y_span / 2, CRTYD_GRID)

    fp.rects.append(FpRect(
        x1=-x2, y1=-y2,
        x2=x2, y2=y2,
        layer="F.CrtYd",
        width=CRTYD_WIDTH,
    ))


def add_fab_body(
    fp: Footprint,
    x_size: float,
    y_size: float,
    pin1_chamfer: float = 0,
) -> None:
    """Add fabrication layer body outline and reference text.

    Args:
        fp: Footprint to modify.
        x_size: Component body size in X direction.
        y_size: Component body size in Y direction.
        pin1_chamfer: If > 0, add a corner chamfer at pin 1 (top-left).
    """
    x2 = x_size / 2
    y2 = y_size / 2

    if pin1_chamfer > 0:
        c = min(pin1_chamfer, x2 * 0.3, y2 * 0.3)
        # Draw body with chamfered top-left corner (pin 1 side)
        fp.lines.append(FpLine(-x2 + c, -y2, x2, -y2, "F.Fab", FAB_WIDTH))
        fp.lines.append(FpLine(x2, -y2, x2, y2, "F.Fab", FAB_WIDTH))
        fp.lines.append(FpLine(x2, y2, -x2, y2, "F.Fab", FAB_WIDTH))
        fp.lines.append(FpLine(-x2, y2, -x2, -y2 + c, "F.Fab", FAB_WIDTH))
        fp.lines.append(FpLine(-x2, -y2 + c, -x2 + c, -y2, "F.Fab", FAB_WIDTH))
    else:
        fp.rects.append(FpRect(
            x1=-x2, y1=-y2,
            x2=x2, y2=y2,
            layer="F.Fab",
            width=FAB_WIDTH,
        ))

    # Reference text centered on body, sized to fit
    font_size = min(0.8, x_size * 0.6, y_size * 0.6)
    font_size = max(font_size, 0.3)  # minimum readable size
    fp.texts.append(FpText(
        text="${REFERENCE}",
        x=0, y=0,
        layer="F.Fab",
        font_size=font_size,
        font_thickness=font_size * 0.15,
    ))


def add_silk_chip(
    fp: Footprint,
    body_x: float,
    pad_x_extent: float,
    pad_y_extent: float,
) -> None:
    """Add silkscreen for 2-terminal chip components (R, C, L, D).

    Draws two short horizontal lines above and below the body (matching KiCad
    convention). The lines are placed between the pads, avoiding overlap.

    Pads are assumed to be along X axis.

    Args:
        fp: Footprint to modify.
        body_x: Component body size in X (along pad axis).
        pad_x_extent: Outermost pad edge in X (pad_center_x + pad_width/2).
        pad_y_extent: Outermost pad edge in Y (pad_height/2).
    """
    bx2 = body_x / 2

    # X range: the silk lines span between the inner edges of the pads
    # but are capped to the body edge
    silk_x_max = pad_x_extent - SILK_CLEARANCE
    silk_x = min(bx2, silk_x_max)

    # Y position: just outside the pads
    silk_y = pad_y_extent + SILK_CLEARANCE + SILK_WIDTH / 2

    if silk_x > SILK_WIDTH:  # Only draw if there's space
        fp.lines.append(FpLine(-silk_x, -silk_y, silk_x, -silk_y, "F.SilkS", SILK_WIDTH))
        fp.lines.append(FpLine(-silk_x, silk_y, silk_x, silk_y, "F.SilkS", SILK_WIDTH))


def add_silk_ic(
    fp: Footprint,
    body_width: float,
    body_height: float,
    pad_x_extent: float,
    pad_y_extent: float,
    pin1_mark: bool = True,
) -> None:
    """Add silkscreen for multi-pin IC packages (SOIC, QFP, QFN, etc.).

    Draws body outline with clearance from pads and pin 1 indicator.

    Args:
        fp: Footprint to modify.
        body_width: Component body width.
        body_height: Component body height.
        pad_x_extent: Outermost pad edge in X.
        pad_y_extent: Outermost pad edge in Y.
        pin1_mark: If True, add a pin 1 indicator dot.
    """
    bw2 = body_width / 2
    bh2 = body_height / 2

    # Silkscreen lines along sides where there are no pads
    # For 2-side packages (SOIC): lines at top and bottom
    # For 4-side packages (QFP): corner marks only

    # Top line
    silk_top_y = -max(bh2, pad_y_extent + SILK_CLEARANCE + SILK_WIDTH / 2)
    silk_bot_y = max(bh2, pad_y_extent + SILK_CLEARANCE + SILK_WIDTH / 2)

    # Side lines (avoid pad area)
    silk_side_x = max(bw2, pad_x_extent + SILK_CLEARANCE + SILK_WIDTH / 2)

    # Draw top and bottom lines within body width
    if bw2 > 0.2:
        fp.lines.append(FpLine(-bw2, silk_top_y, bw2, silk_top_y, "F.SilkS", SILK_WIDTH))
        fp.lines.append(FpLine(-bw2, silk_bot_y, bw2, silk_bot_y, "F.SilkS", SILK_WIDTH))

    # Pin 1 indicator: small filled circle
    if pin1_mark:
        mark_x = -(pad_x_extent + SILK_CLEARANCE + 0.3)
        mark_y = silk_top_y
        fp.circles.append(FpCircle(
            cx=mark_x, cy=mark_y,
            radius=0.1,
            layer="F.SilkS",
            width=SILK_WIDTH,
            fill=True,
        ))


def add_polarity_mark(
    fp: Footprint,
    x: float,
    y: float,
    layer: str = "F.Fab",
) -> None:
    """Add a polarity indicator (small line or dot) on the fabrication layer."""
    fp.lines.append(FpLine(x - 0.2, y, x + 0.2, y, layer, FAB_WIDTH))


def generate_paste_segments(
    pad_width: float,
    pad_height: float,
    target_coverage: float = 0.40,
    min_gap: float = 0.25,
) -> list[tuple[float, float, float, float]]:
    """Generate paste mask aperture segments for thermal pads.

    IPC-7351B recommends 40% paste coverage for exposed pads > 4mm.
    Segments are arranged in an NxN grid with gaps between them.

    Args:
        pad_width: Total pad width.
        pad_height: Total pad height.
        target_coverage: Target paste area as fraction of pad area (default 0.40).
        min_gap: Minimum gap between apertures (default 0.25 mm).

    Returns:
        List of (cx, cy, width, height) tuples for each paste aperture,
        relative to pad center.
    """
    # For pads <= 4mm, use a single reduced aperture
    if pad_width <= 4.0 and pad_height <= 4.0:
        ratio = target_coverage ** 0.5  # sqrt to get linear scale factor
        return [(0, 0, pad_width * ratio, pad_height * ratio)]

    # Determine grid size: start with 2x2, increase if needed
    for n in range(2, 8):
        aperture_w = (pad_width - (n - 1) * min_gap) / n
        aperture_h = (pad_height - (n - 1) * min_gap) / n
        if aperture_w > 0 and aperture_h > 0:
            actual_coverage = (n * aperture_w * n * aperture_h) / (pad_width * pad_height)
            if actual_coverage <= target_coverage * 1.1:
                break

    # Adjust aperture size to hit target coverage
    total_pad_area = pad_width * pad_height
    target_aperture_area = total_pad_area * target_coverage / (n * n)
    aperture_w = (target_aperture_area / (pad_width * pad_height) * pad_width * pad_height) ** 0.5
    # Keep aspect ratio proportional to pad
    aspect = pad_width / pad_height
    aperture_h = (target_aperture_area / aspect) ** 0.5
    aperture_w = aperture_h * aspect

    # Ensure apertures fit with gaps
    max_w = (pad_width - (n - 1) * min_gap) / n
    max_h = (pad_height - (n - 1) * min_gap) / n
    aperture_w = min(aperture_w, max_w)
    aperture_h = min(aperture_h, max_h)

    segments = []
    pitch_x = (pad_width - aperture_w) / max(n - 1, 1)
    pitch_y = (pad_height - aperture_h) / max(n - 1, 1)
    start_x = -(pad_width - aperture_w) / 2
    start_y = -(pad_height - aperture_h) / 2

    for row in range(n):
        for col in range(n):
            cx = start_x + col * pitch_x
            cy = start_y + row * pitch_y
            segments.append((cx, cy, aperture_w, aperture_h))

    return segments
