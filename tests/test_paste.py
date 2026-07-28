"""Tests for thermal pad paste segmentation (IPC-7351B 3.1.5.7)."""

import math

import pytest

from generator.core.paste import thermal_paste_segments


def total_area(segments):
    return sum(w * h for _, _, w, h in segments)


class TestSegmentation:
    def test_small_pad_single_aperture(self):
        """Pads 4.0mm or less get a single centered aperture."""
        segments = thermal_paste_segments(2.5, 2.5)
        assert len(segments) == 1
        cx, cy, w, h = segments[0]
        assert (cx, cy) == (0, 0)
        assert w == h == pytest.approx(2.5 * math.sqrt(0.40), abs=0.001)

    def test_forty_percent_coverage(self):
        """Total paste area is 40% of land area (3.1.5.7 default)."""
        for dims in [(2.0, 3.2), (5.4, 5.7), (8.75, 10.4), (4.0, 4.0)]:
            segments = thermal_paste_segments(*dims)
            land_area = dims[0] * dims[1]
            assert total_area(segments) == pytest.approx(
                0.40 * land_area, rel=0.01), dims

    def test_large_pad_segmented(self):
        """Above 4.0mm the pad is split into ceil(dim/4.0) cells per axis."""
        assert len(thermal_paste_segments(5.4, 5.7)) == 4    # 2x2
        assert len(thermal_paste_segments(8.75, 10.4)) == 9  # 3x3
        assert len(thermal_paste_segments(6.7, 3.2)) == 2    # 2x1

    def test_segments_inside_land(self):
        segments = thermal_paste_segments(8.75, 10.4)
        for cx, cy, w, h in segments:
            assert abs(cx) + w / 2 <= 8.75 / 2 + 1e-9
            assert abs(cy) + h / 2 <= 10.4 / 2 + 1e-9

    def test_gaps_between_segments(self):
        """Adjacent apertures must not touch (aperture < cell)."""
        segments = thermal_paste_segments(8.0, 8.0)  # 2x2, cell 4.0
        xs = sorted({cx for cx, _, _, _ in segments})
        w = segments[0][2]
        gap = (xs[1] - xs[0]) - w
        assert gap > 0.5  # sqrt(0.4) leaves ~37% of the cell as gap


class TestGeneratedFootprints:
    def _paste_only_pads(self, path):
        from generator.core.kicad_reader import read_footprint
        fp = read_footprint(path)
        return fp, [p for p in fp.pads
                    if p.layers == ["F.Paste"] and not p.number]

    def test_dpak_tab_paste(self):
        fp, paste = self._paste_only_pads(
            "output/IPC7351B_SOT.pretty/SOT228P980X230-3N.kicad_mod")
        tab = fp.copper_pads()["4"]
        assert len(paste) == 4  # 6.7 x 5.7 tab -> 2x2
        paste_area = sum(p.width * p.height for p in paste)
        assert paste_area == pytest.approx(
            0.40 * tab.width * tab.height, rel=0.01)
        # Apertures centered on the tab, not the footprint origin
        assert sum(p.x for p in paste) / 4 == pytest.approx(tab.x, abs=0.01)

    def test_qfn_ep_paste(self):
        fp, paste = self._paste_only_pads(
            "output/IPC7351B_QFN.pretty/QFN050P700X700X090-48T510N.kicad_mod")
        ep = fp.copper_pads()["49"]
        assert len(paste) == 4  # 5.1 x 5.1 EP -> 2x2
        paste_area = sum(p.width * p.height for p in paste)
        assert paste_area == pytest.approx(
            0.40 * ep.width * ep.height, rel=0.01)

    def test_small_ep_single_aperture(self):
        fp, paste = self._paste_only_pads(
            "output/IPC7351B_QFN.pretty/QFN050P300X300X090-16T150N.kicad_mod")
        assert len(paste) == 1  # 1.5mm EP -> single aperture

    def test_signal_pads_keep_full_paste(self):
        """Only the thermal pad loses its paste layer."""
        from generator.core.kicad_reader import read_footprint
        fp = read_footprint(
            "output/IPC7351B_SOT.pretty/SOT228P980X230-3N.kicad_mod")
        for num in ("1", "2", "3"):
            assert "F.Paste" in fp.copper_pads()[num].layers
