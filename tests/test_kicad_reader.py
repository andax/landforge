"""Tests for the .kicad_mod reader (generator/core/kicad_reader.py)."""

from generator.core.kicad_reader import parse_footprint, parse_sexpr
from generator.core.kicad_writer import (
    Footprint, Pad, PadShape, PadType, FpRect, serialize_footprint,
)


class TestSexprParser:
    def test_nested_lists_and_atoms(self):
        node = parse_sexpr('(a (b 1 2.5) (c "quoted string"))')
        assert node == ["a", ["b", "1", "2.5"], ["c", "quoted string"]]

    def test_quoted_string_with_escapes(self):
        node = parse_sexpr(r'(descr "a \"b\" c")')
        assert node == ["descr", 'a "b" c']

    def test_empty_string_atom(self):
        node = parse_sexpr('(pad "" smd rect)')
        assert node == ["pad", "", "smd", "rect"]


class TestRoundTrip:
    """Serialize with kicad_writer, parse back with kicad_reader."""

    def _make_footprint(self) -> Footprint:
        fp = Footprint(name="TEST0001X001N", description="round trip test")
        fp.pads.append(Pad(
            number="1", pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=-0.8125, y=0.0, width=0.825, height=0.95,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))
        fp.pads.append(Pad(
            number="2", pad_type=PadType.SMD, shape=PadShape.ROUNDRECT,
            x=0.8125, y=0.0, width=0.825, height=0.95,
            layers=["F.Cu", "F.Mask", "F.Paste"],
        ))
        fp.rects.append(FpRect(
            x1=-1.5, y1=-0.75, x2=1.5, y2=0.75,
            layer="F.CrtYd", width=0.05,
        ))
        return fp

    def test_pads_and_courtyard_survive(self):
        parsed = parse_footprint(serialize_footprint(self._make_footprint()))
        assert parsed.name == "TEST0001X001N"
        assert parsed.smd
        pads = parsed.copper_pads()
        assert sorted(pads) == ["1", "2"]
        assert pads["1"].x == -0.8125
        assert pads["1"].size_normalized == (0.825, 0.95)
        assert pads["1"].layers == ["F.Cu", "F.Mask", "F.Paste"]
        assert parsed.courtyard_bbox == (-1.5, -0.75, 1.5, 0.75)


class TestStockFormat:
    """Constructs stock libraries actually use, beyond what we write."""

    def test_rotated_pad_normalizes_size(self):
        text = """(footprint "ROT"
            (attr smd)
            (pad "1" smd roundrect (at 1.0 2.0 90) (size 0.5 1.5)
                (layers "F.Cu" "F.Mask"))
        )"""
        pad = parse_footprint(text).copper_pads()["1"]
        assert pad.rotation == 90
        assert pad.size_normalized == (1.5, 0.5)

    def test_tht_pad_with_drill(self):
        text = """(footprint "THT"
            (attr through_hole)
            (pad "1" thru_hole rect (at 0 0) (size 1.6 1.6) (drill 0.8)
                (layers "*.Cu" "*.Mask"))
        )"""
        parsed = parse_footprint(text)
        assert not parsed.smd
        pad = parsed.copper_pads()["1"]
        assert pad.drill == 0.8
        assert pad.on_copper

    def test_paste_only_pad_excluded_from_copper(self):
        text = """(footprint "PASTE"
            (attr smd)
            (pad "9" smd rect (at 0 0) (size 2 2) (layers "F.Cu" "F.Mask"))
            (pad "9" smd rect (at 0 0) (size 0.9 0.9) (layers "F.Paste"))
        )"""
        pads = parse_footprint(text).copper_pads()
        # The copper pad wins; the paste aperture helper is ignored
        assert pads["9"].size_normalized == (2.0, 2.0)

    def test_courtyard_from_circle(self):
        text = """(footprint "CIRC"
            (attr smd)
            (fp_circle (center 0 0) (end 2.5 0)
                (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))
        )"""
        assert parse_footprint(text).courtyard_bbox == (-2.5, -2.5, 2.5, 2.5)
