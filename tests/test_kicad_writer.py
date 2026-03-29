"""Tests for KiCad .kicad_mod file writer."""

from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType, PadProperty,
    FpLine, FpRect, FpText, Model3D,
    serialize_footprint,
)


class TestSerializeFootprint:
    """Test basic serialization."""

    def test_minimal_footprint(self):
        fp = Footprint(name="TEST")
        output = serialize_footprint(fp)
        assert '(footprint "TEST"' in output
        assert "(version 20260206)" in output
        assert '(generator "landforge")' in output
        assert "(attr smd)" in output

    def test_two_terminal_chip(self):
        """Test a simple 2-pad chip component."""
        fp = Footprint(
            name="RESC1608X55N",
            description="Chip resistor 0603",
            tags="resistor chip 0603 1608",
        )
        fp.pads.append(Pad(
            number="1", pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=-0.825, y=0, width=0.8, height=0.95,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))
        fp.pads.append(Pad(
            number="2", pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=0.825, y=0, width=0.8, height=0.95,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))
        fp.rects.append(FpRect(
            x1=-1.48, y1=-0.73, x2=1.48, y2=0.73,
            layer="F.CrtYd", width=0.05,
        ))

        output = serialize_footprint(fp)

        assert '(pad "1" smd roundrect' in output
        assert '(pad "2" smd roundrect' in output
        assert "(roundrect_rratio 0.25)" in output
        assert '"F.Cu"' in output
        assert '"F.CrtYd"' in output
        assert 'resistor chip 0603 1608' in output

    def test_3d_model_reference(self):
        fp = Footprint(name="TEST")
        fp.model = Model3D(
            path="${KICAD10_3DMODEL_DIR}/Resistor_SMD.3dshapes/R_0603.step"
        )
        output = serialize_footprint(fp)
        assert "Resistor_SMD.3dshapes/R_0603.step" in output
        assert "(xyz 0.0 0.0 0.0)" in output

    def test_through_hole_attr(self):
        fp = Footprint(name="DIP8", smd=False)
        output = serialize_footprint(fp)
        assert "(attr through_hole)" in output

    def test_pad_property_bga(self):
        fp = Footprint(name="BGA")
        fp.pads.append(Pad(
            number="A1", pad_type=PadType.SMD, shape=PadShape.CIRCLE,
            x=0, y=0, width=0.3, height=0.3,
            layers=["F.Cu", "F.Mask", "F.Paste"],
            roundrect_ratio=None,
            property=PadProperty.BGA,
        ))
        output = serialize_footprint(fp)
        assert "(pad_prop_bga)" in output

    def test_heatsink_pad(self):
        fp = Footprint(name="QFN")
        fp.pads.append(Pad(
            number="EP", pad_type=PadType.SMD, shape=PadShape.RECT,
            x=0, y=0, width=3.0, height=3.0,
            layers=["F.Cu", "F.Mask"],
            roundrect_ratio=None,
            property=PadProperty.HEATSINK,
        ))
        output = serialize_footprint(fp)
        assert "(pad_prop_heatsink)" in output

    def test_custom_properties(self):
        fp = Footprint(name="TEST")
        fp.properties["IPC_Table"] = "3-5"
        fp.properties["DensityLevel"] = "B"
        output = serialize_footprint(fp)
        assert '"IPC_Table" "3-5"' in output
        assert '"DensityLevel" "B"' in output


class TestFloatFormatting:
    """Test that floating point values are formatted cleanly."""

    def test_no_excessive_decimals(self):
        fp = Footprint(name="TEST")
        fp.pads.append(Pad(
            number="1", pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=-0.825, y=0, width=0.8, height=0.95,
            layers=["F.Cu"],
        ))
        output = serialize_footprint(fp)
        # Should not have "0.800000" etc.
        assert "0.800000" not in output
        assert "0.950000" not in output
