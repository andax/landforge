"""Shipped-output invariants over every generated footprint.

These guard properties that no equation table or CSV row may violate,
regardless of family: pads on different nets must never overlap, and
the default silkscreen reference text must sit clear of the copper.
Added after the 2026-07-28 multi-agent review found 31 shipped files
with overlapping pads that no test had caught.
"""

import re
from pathlib import Path

import pytest

from generator.core.kicad_reader import read_footprint

OUTPUT = Path(__file__).resolve().parent.parent / "output"
ALL_FOOTPRINTS = sorted(OUTPUT.glob("*.pretty/*.kicad_mod"))


def _bbox(pad):
    w, h = pad.size_normalized
    return (pad.x - w / 2, pad.y - h / 2, pad.x + w / 2, pad.y + h / 2)


def _overlap(a, b, eps=1e-6):
    return (a[0] < b[2] - eps and b[0] < a[2] - eps
            and a[1] < b[3] - eps and b[1] < a[3] - eps)


def test_output_exists():
    assert len(ALL_FOOTPRINTS) > 600


def test_no_overlapping_pads_between_nets():
    """Copper pads with different numbers must never overlap."""
    bad = []
    for path in ALL_FOOTPRINTS:
        pads = read_footprint(path).copper_pads()
        items = sorted(pads.items())
        for i, (num_a, pad_a) in enumerate(items):
            box_a = _bbox(pad_a)
            for num_b, pad_b in items[i + 1:]:
                if _overlap(box_a, _bbox(pad_b)):
                    bad.append(f"{path.parent.name}/{path.stem}: "
                               f"pads {num_a} and {num_b}")
    assert not bad, "overlapping pads (shorted nets):\n" + "\n".join(bad)


def test_positive_pad_gap_in_descr():
    """No shipped footprint may document a non-positive inner gap."""
    bad = [f"{p.parent.name}/{p.stem}" for p in ALL_FOOTPRINTS
           if re.search(r"G=-|G=0\.00", p.read_text())]
    assert not bad, "non-positive G in descr:\n" + "\n".join(bad)


def test_reference_text_above_courtyard():
    """Reference silkscreen text must sit above the courtyard, off copper."""
    at_re = re.compile(
        r'\(property "Reference" "REF\*\*"\s*\(at 0 (-?[\d.]+) 0\)')
    bad = []
    for path in ALL_FOOTPRINTS:
        fp = read_footprint(path)
        if fp.courtyard_bbox is None:
            continue
        m = at_re.search(path.read_text())
        assert m, f"no Reference property in {path}"
        ref_y = float(m.group(1))
        # Text is 1.0mm tall, centered at ref_y: its lower edge must not
        # reach the courtyard top (courtyard encloses all copper).
        if ref_y + 0.5 > fp.courtyard_bbox[1] + 1e-6:
            bad.append(f"{path.parent.name}/{path.stem}: ref at {ref_y}, "
                       f"courtyard top {fp.courtyard_bbox[1]}")
    assert not bad, "Reference text inside courtyard:\n" + "\n".join(bad)


def test_density_level_monotonicity():
    """For every footprint triple, pad outer extent must be A >= B >= C."""
    triples = {}
    for path in ALL_FOOTPRINTS:
        # Collapsing-ball BGA lands shrink as density level rises by
        # design (Table 3-17: 25/20/15% reduction for A/B/C), so the
        # A >= B >= C extent rule does not apply to that library.
        if path.parent.name == "IPC7351B_BGA.pretty":
            continue
        stem = path.stem
        base, suffix = stem[:-1], stem[-1]
        if suffix in "MNL":
            triples.setdefault((path.parent.name, base), {})[suffix] = path
    checked = 0
    bad = []
    for (lib, base), variants in triples.items():
        if set(variants) != {"M", "N", "L"}:
            continue
        extents = {}
        for suffix, path in variants.items():
            pads = read_footprint(path).copper_pads().values()
            extents[suffix] = max(abs(p.x) + p.size_normalized[0] / 2
                                  for p in pads)
        if not (extents["M"] >= extents["N"] - 1e-6
                and extents["N"] >= extents["L"] - 1e-6):
            bad.append(f"{lib}/{base}: M={extents['M']:.3f} "
                       f"N={extents['N']:.3f} L={extents['L']:.3f}")
        checked += 1
    assert checked > 190
    assert not bad, "density levels not monotonic:\n" + "\n".join(bad)
