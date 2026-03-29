"""
Integration test: generate R_0603 (RESC1608X55) at all 3 density levels.

Validates the complete pipeline from component dimensions through to
KiCad footprint output, and compares Level B against KiCad stock library.
"""

import os
import pytest

from generator.core.ipc_equations import DensityLevel
from generator.core.naming import density_suffix
from generator.core.kicad_writer import serialize_footprint, write_footprint


def generate_resc1608(level: DensityLevel):
    """Generate a complete RESC1608X55 footprint at the given density level.

    Uses the chip family generator for consistency.
    """
    from generator.families.ipc7352_chip import ChipComponentSpec, generate_chip_footprint

    spec = ChipComponentSpec(
        prefix="RESC",
        eia_code="0603",
        metric_code="1608",
        body_length=1.6,
        body_width=0.8,
        body_height=0.55,
        L_min=1.50, L_max=1.70,
        T_min=0.20, T_max=0.40,
        W_min=0.70, W_max=0.90,
    )
    return generate_chip_footprint(spec, level)


class TestRESC1608Generation:
    """Test complete footprint generation for 0603 chip resistor."""

    def test_generates_valid_footprint_all_levels(self):
        """Each density level should produce a valid footprint."""
        for level in DensityLevel:
            fp = generate_resc1608(level)
            output = serialize_footprint(fp)

            assert f'(footprint "RESC1608X055{density_suffix(level)}"' in output
            assert '(pad "1"' in output
            assert '(pad "2"' in output
            assert '"F.CrtYd"' in output
            assert '"F.Fab"' in output

    def test_density_level_affects_size(self):
        """Level A pads should be larger than B, which should be larger than C."""
        fps = {level: generate_resc1608(level) for level in DensityLevel}

        # Extract pad widths (the first pad's width attribute)
        pad_w = {level: fps[level].pads[0].width for level in DensityLevel}
        assert pad_w[DensityLevel.A] >= pad_w[DensityLevel.B] >= pad_w[DensityLevel.C]

    def test_level_b_pad_dimensions_close_to_kicad_stock(self):
        """Level B should be close to KiCad stock R_0603_1608Metric.

        KiCad stock: pad size 0.9 x 0.95 mm at centers ±0.775.
        (pad size in KiCad is width x height where width is along component axis)
        """
        fp = generate_resc1608(DensityLevel.B)
        pad1 = fp.pads[0]

        # KiCad stock: pad at x=-0.775, size 0.9 (length) x 0.95 (width)
        # Our pad_length and pad_width may differ slightly due to different
        # input dimensions, but should be in the same ballpark
        assert 0.6 < pad1.width < 1.2, f"Pad length {pad1.width} out of range"
        assert 0.7 < pad1.height < 1.2, f"Pad width {pad1.height} out of range"
        assert -1.0 < pad1.x < -0.5, f"Pad center {pad1.x} out of range"

    def test_courtyard_ordering(self):
        """Level A courtyard should be largest, C smallest."""
        fps = {level: generate_resc1608(level) for level in DensityLevel}

        # Extract courtyard rectangles
        def get_cy(fp):
            for r in fp.rects:
                if r.layer == "F.CrtYd":
                    return (r.x2 - r.x1, r.y2 - r.y1)
            return (0, 0)

        cy = {level: get_cy(fps[level]) for level in DensityLevel}

        # Both width and height should decrease from A to C
        assert cy[DensityLevel.A][0] >= cy[DensityLevel.B][0] >= cy[DensityLevel.C][0]
        assert cy[DensityLevel.A][1] >= cy[DensityLevel.B][1] >= cy[DensityLevel.C][1]

    def test_ipc_naming(self):
        """Verify IPC naming convention.

        RESC1608X055N = chip resistor, 1.6x0.8mm body, 0.55mm height, nominal.
        """
        fp_a = generate_resc1608(DensityLevel.A)
        fp_b = generate_resc1608(DensityLevel.B)
        fp_c = generate_resc1608(DensityLevel.C)

        assert fp_a.name == "RESC1608X055M"
        assert fp_b.name == "RESC1608X055N"
        assert fp_c.name == "RESC1608X055L"

    def test_write_to_file(self, tmp_path):
        """Test writing to actual .kicad_mod file."""
        fp = generate_resc1608(DensityLevel.B)
        path = str(tmp_path / f"{fp.name}.kicad_mod")
        write_footprint(fp, path)

        assert os.path.exists(path)
        with open(path) as f:
            content = f.read()
        assert '(footprint "RESC1608X055N"' in content
        assert content.endswith(")\n")

    def test_metadata_traceability(self):
        """Every footprint should have full calculation traceability."""
        fp = generate_resc1608(DensityLevel.B)

        assert "Table 3-5" in fp.description
        assert "Z=" in fp.description
        assert "G=" in fp.description
        assert "X=" in fp.description
        assert fp.properties["IPC_Table"] == "3-5"
        assert fp.properties["DensityLevel"] == "B"
