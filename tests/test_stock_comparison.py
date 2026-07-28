"""Regression gate for the stock comparison (generator/stock_compare.py).

Compares generated Level B footprints against the local KiCad stock
libraries and fails on any NEW gross disagreement. Known-open findings
(documented in docs/validation/stock_comparison_report.md, awaiting
resolution against IPC-7351B) are baselined below; fixing one requires
removing it from KNOWN_OPEN so the evidence stays honest.

Skipped when the stock libraries are not installed on this machine.
"""

import pytest

from generator.stock_compare import (
    DEFAULT_STOCK, OUTPUT_DIR, compare_pair, load_map_entries,
)
from generator.core.kicad_reader import read_footprint

# Stage B open findings -- see "Open findings" in the report.
# All findings from the 2026-07-28 baseline run were resolved against
# IPC-7351B (tab geometry, CAPAE Table 3-20 dims, DIP THT lands per
# IPC-2221/7251, JEDEC BGA ball lettering, CSV terminal data). Any name
# appearing here again is a NEW regression to investigate, not history.
KNOWN_OPEN: set[str] = set()

pytestmark = pytest.mark.skipif(
    not DEFAULT_STOCK.is_dir(),
    reason=f"KiCad stock libraries not found at {DEFAULT_STOCK}",
)


def _run_comparison():
    entries, _ = load_map_entries()
    results = []
    for entry in entries:
        ours = (OUTPUT_DIR / f"{entry.ipc_library}.pretty"
                / f"{entry.ipc_name}.kicad_mod")
        stock = (DEFAULT_STOCK / f"{entry.stock_library}.pretty"
                 / f"{entry.stock_name}.kicad_mod")
        assert ours.exists(), f"mapped footprint missing: {ours}"
        assert stock.exists(), f"mapped stock footprint missing: {stock}"
        results.append(compare_pair(read_footprint(ours),
                                    read_footprint(stock), entry))
    return results


def test_no_new_failures():
    results = _run_comparison()
    fails = {r.entry.ipc_name for r in results if r.verdict == "FAIL"}

    new = fails - KNOWN_OPEN
    assert not new, (
        "NEW stock-comparison failures (regression?): " + ", ".join(sorted(new))
    )

    resolved = KNOWN_OPEN - fails
    assert not resolved, (
        "these findings no longer fail -- remove them from KNOWN_OPEN: "
        + ", ".join(sorted(resolved))
    )


def test_mapped_pairs_mostly_agree():
    """At least the clean majority must stay clean."""
    results = _run_comparison()
    ok = sum(1 for r in results if r.verdict == "OK")
    assert ok >= 60, f"OK count dropped to {ok} -- geometry regression?"
