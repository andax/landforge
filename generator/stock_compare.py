"""
Compare generated Level B (Nominal) footprints against KiCad stock libraries.

This is a validation aid, not a correctness gate: IPC-7351B is the source
of truth for LandForge; KiCad stock footprints are hand-maintained,
partly vendor-derived, and use coarser rounding. Differences are expected
and are classified, not hidden:

  OK      -- geometry agrees within tight tolerances
  REVIEW  -- differs enough to deserve a human look (or the mapping is a
             known-loose analog); not necessarily wrong
  FAIL    -- gross disagreement (pad numbering mismatch, pitch error,
             >35% size deviation) that most likely indicates a bug in
             generator or CSV data

Mapping sources:
  - chip family: derived programmatically from data/jedec/chip_components.csv
    (RESC1608X055N <-> Resistor_SMD/R_0603_1608Metric etc.)
  - all other families: curated pairs in data/kicad_stock_map.csv

Run:  uv run python -m generator.stock_compare [--stock PATH] [--report PATH]

Writes docs/validation/stock_comparison_report.md and exits non-zero if
any pair is classified FAIL.
"""

from __future__ import annotations

import argparse
import csv
import glob
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

from generator.core.kicad_reader import ReadFootprint, read_footprint

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STOCK = Path("~/Applications/kicad-10/share/kicad/footprints").expanduser()
DEFAULT_REPORT = PROJECT_ROOT / "docs" / "validation" / "stock_comparison_report.md"
OUTPUT_DIR = PROJECT_ROOT / "output"
MAP_CSV = PROJECT_ROOT / "data" / "kicad_stock_map.csv"
CHIP_CSV = PROJECT_ROOT / "data" / "jedec" / "chip_components.csv"

# Classification thresholds (mm / percent)
CENTER_DEV_REVIEW = 0.15
CENTER_DEV_FAIL = 0.50
SIZE_DEV_REVIEW = 20.0
SIZE_DEV_FAIL = 35.0
COURTYARD_DEV_REVIEW = 1.0
DRILL_DEV_REVIEW = 0.2

CHIP_STOCK_LIBS = {
    "RESC": ("Resistor_SMD", "R"),
    "CAPC": ("Capacitor_SMD", "C"),
    "INDC": ("Inductor_SMD", "L"),
    "DIOC": ("Diode_SMD", "D"),
}

# Notes for programmatically mapped entries (chip family has no CSV row)
CHIP_NOTES = {
    "CAPC5750X250N": "2220 terminal length 0.50-1.00 per vendor datasheets",
}


@dataclass
class MapEntry:
    family: str
    ipc_library: str
    ipc_name: str
    stock_library: str
    stock_name: str
    subset: bool = False
    loose: bool = False
    pinmap: dict[str, str] = field(default_factory=dict)
    note: str = ""


@dataclass
class Result:
    entry: MapEntry
    verdict: str            # "OK" | "REVIEW" | "FAIL"
    shared: int = 0
    ours_total: int = 0
    stock_total: int = 0
    center_dev: float = 0.0
    size_dev: float = 0.0
    courtyard_dev: tuple[float, float] | None = None
    detail: str = ""


def _parse_flags(entry: MapEntry, flags: str) -> None:
    for flag in flags.split():
        if flag == "subset":
            entry.subset = True
        elif flag == "loose":
            entry.loose = True
        elif flag.startswith("pinmap="):
            for pair in flag[len("pinmap="):].split("+"):
                ours, stock = pair.split(":")
                entry.pinmap[ours] = stock


def load_map_entries() -> tuple[list[MapEntry], list[tuple[str, str, str]]]:
    """All mapping entries plus known-unmappable footprints.

    Returns (entries, no_stock) where no_stock is a list of
    (family, library, name) for footprints with no stock equivalent that
    should be reported rather than silently skipped.
    """
    entries: list[MapEntry] = []
    no_stock: list[tuple[str, str, str]] = []

    # Programmatic chip family map
    with open(CHIP_CSV) as f:
        for row in csv.DictReader(f):
            prefix = row["prefix"]
            pattern = str(
                OUTPUT_DIR / "IPC7351B_Chip.pretty"
                / f"{prefix}{row['metric_code']}X*N.kicad_mod"
            )
            matches = glob.glob(pattern)
            if not matches:
                continue
            ipc_name = Path(matches[0]).stem
            if prefix not in CHIP_STOCK_LIBS:
                no_stock.append(("CHIP", "IPC7351B_Chip", ipc_name))
                continue
            lib, letter = CHIP_STOCK_LIBS[prefix]
            entries.append(MapEntry(
                family="CHIP",
                ipc_library="IPC7351B_Chip",
                ipc_name=ipc_name,
                stock_library=lib,
                stock_name=f"{letter}_{row['eia_code']}_{row['metric_code']}Metric",
                note=CHIP_NOTES.get(ipc_name, ""),
            ))

    # Curated map
    with open(MAP_CSV) as f:
        for row in csv.DictReader(f):
            entry = MapEntry(
                family=row["family"],
                ipc_library=row["ipc_library"],
                ipc_name=row["ipc_name"],
                stock_library=row["stock_library"],
                stock_name=row["stock_name"],
                note=row["note"].strip(),
            )
            _parse_flags(entry, row["flags"].strip())
            entries.append(entry)

    return entries, no_stock


def compare_pair(ours: ReadFootprint, stock: ReadFootprint,
                 entry: MapEntry) -> Result:
    ours_pads = {entry.pinmap.get(num, num): pad
                 for num, pad in ours.copper_pads().items()}
    stock_pads = stock.copper_pads()

    shared = sorted(set(ours_pads) & set(stock_pads))
    result = Result(entry=entry, verdict="OK", shared=len(shared),
                    ours_total=len(ours_pads), stock_total=len(stock_pads))

    issues: list[str] = []
    sets_match = set(ours_pads) == set(stock_pads)
    if not shared:
        result.verdict = "FAIL"
        result.detail = "no shared pad numbers"
        return result
    if not sets_match and not entry.subset:
        issues.append(("FAIL", f"pad set mismatch "
                       f"(ours {len(ours_pads)}, stock {len(stock_pads)})"))

    # Centroid-normalize positions: stock footprints (e.g. THT DIP) may
    # anchor the origin at pin 1 instead of the pattern center.
    def centroid(pads: dict, keys: list[str]) -> tuple[float, float]:
        xs = [pads[k].x for k in keys]
        ys = [pads[k].y for k in keys]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    ocx, ocy = centroid(ours_pads, shared)
    scx, scy = centroid(stock_pads, shared)

    worst_center = ("", 0.0)
    worst_size = ("", 0.0, "")
    worst_drill = 0.0
    for num in shared:
        op, sp = ours_pads[num], stock_pads[num]
        dev = math.dist((op.x - ocx, op.y - ocy), (sp.x - scx, sp.y - scy))
        if dev > worst_center[1]:
            worst_center = (num, dev)
        ow, oh = op.size_normalized
        sw, sh = sp.size_normalized
        for o, s in ((ow, sw), (oh, sh)):
            pct = abs(o - s) / s * 100.0 if s else 0.0
            if pct > worst_size[1]:
                worst_size = (num, pct, f"{ow}x{oh} vs {sw}x{sh}")
        if op.drill is not None and sp.drill is not None:
            worst_drill = max(worst_drill, abs(op.drill - sp.drill))

    result.center_dev = worst_center[1]
    result.size_dev = worst_size[1]

    if result.center_dev > CENTER_DEV_FAIL:
        issues.append(("FAIL", f"pad {worst_center[0]} center off by "
                       f"{result.center_dev:.2f}mm"))
    elif result.center_dev > CENTER_DEV_REVIEW:
        issues.append(("REVIEW", f"pad {worst_center[0]} center off by "
                       f"{result.center_dev:.2f}mm"))
    if result.size_dev > SIZE_DEV_FAIL:
        issues.append(("FAIL", f"pad {worst_size[0]} size dev "
                       f"{result.size_dev:.0f}% ({worst_size[2]})"))
    elif result.size_dev > SIZE_DEV_REVIEW:
        issues.append(("REVIEW", f"pad {worst_size[0]} size dev "
                       f"{result.size_dev:.0f}% ({worst_size[2]})"))
    if worst_drill > DRILL_DEV_REVIEW:
        issues.append(("REVIEW", f"drill differs by {worst_drill:.2f}mm"))

    if ours.courtyard_bbox and stock.courtyard_bbox:
        ob, sb = ours.courtyard_bbox, stock.courtyard_bbox
        dw = (ob[2] - ob[0]) - (sb[2] - sb[0])
        dh = (ob[3] - ob[1]) - (sb[3] - sb[1])
        result.courtyard_dev = (dw, dh)
        if max(abs(dw), abs(dh)) > COURTYARD_DEV_REVIEW:
            issues.append(("REVIEW",
                           f"courtyard differs {dw:+.2f}x{dh:+.2f}mm"))

    if any(level == "FAIL" for level, _ in issues):
        result.verdict = "FAIL"
    elif issues:
        result.verdict = "REVIEW"

    # A known-loose mapping cannot be more than REVIEW: the stock part is
    # only an analog, so gross deviation does not indicate a generator bug.
    if entry.loose and result.verdict == "FAIL":
        result.verdict = "REVIEW"

    result.detail = "; ".join(msg for _, msg in issues)
    return result


def find_unmapped(entries: list[MapEntry]) -> list[tuple[str, str]]:
    """Level B footprints in output/ not covered by any mapping entry."""
    mapped = {(e.ipc_library, e.ipc_name) for e in entries}
    unmapped = []
    for lib_dir in sorted(OUTPUT_DIR.glob("*.pretty")):
        lib = lib_dir.stem
        for path in sorted(lib_dir.glob("*N.kicad_mod")):
            if (lib, path.stem) not in mapped:
                unmapped.append((lib, path.stem))
    return unmapped


def run(stock_path: Path, report_path: Path) -> int:
    if not stock_path.is_dir():
        print(f"error: stock footprint path not found: {stock_path}",
              file=sys.stderr)
        return 2

    entries, no_stock = load_map_entries()
    results: list[Result] = []
    for entry in entries:
        ours_path = (OUTPUT_DIR / f"{entry.ipc_library}.pretty"
                     / f"{entry.ipc_name}.kicad_mod")
        stock_file = (stock_path / f"{entry.stock_library}.pretty"
                      / f"{entry.stock_name}.kicad_mod")
        if not ours_path.exists() or not stock_file.exists():
            result = Result(entry=entry, verdict="FAIL",
                            detail=f"file missing: "
                            f"{ours_path if not ours_path.exists() else stock_file}")
            results.append(result)
            continue
        results.append(compare_pair(read_footprint(ours_path),
                                    read_footprint(stock_file), entry))

    unmapped = find_unmapped(entries)
    write_report(report_path, results, no_stock, unmapped, stock_path)

    counts = {v: sum(1 for r in results if r.verdict == v)
              for v in ("OK", "REVIEW", "FAIL")}
    print(f"compared {len(results)} pairs: "
          f"{counts['OK']} OK, {counts['REVIEW']} REVIEW, "
          f"{counts['FAIL']} FAIL; "
          f"{len(no_stock) + len(unmapped)} without stock equivalent")
    print(f"report: {report_path}")
    for r in results:
        if r.verdict == "FAIL":
            print(f"  FAIL {r.entry.ipc_name} vs {r.entry.stock_name}: "
                  f"{r.detail}")
    return 1 if counts["FAIL"] else 0


def write_report(path: Path, results: list[Result],
                 no_stock: list[tuple[str, str, str]],
                 unmapped: list[tuple[str, str]], stock_path: Path) -> None:
    lines: list[str] = []
    w = lines.append
    counts = {v: sum(1 for r in results if r.verdict == v)
              for v in ("OK", "REVIEW", "FAIL")}

    w("# Stock Comparison Report")
    w("")
    w("Automated comparison of LandForge Level B (Nominal) footprints "
      "against the KiCad stock libraries.")
    w("")
    w("**IPC-7351B is the source of truth for this project.** KiCad stock "
      "footprints are hand-maintained, partly vendor-derived, and use "
      "coarser rounding, so differences are expected. REVIEW means a "
      "human should look, not that the footprint is wrong. FAIL means "
      "gross disagreement that most likely indicates a generator or "
      "CSV data bug.")
    w("")
    w(f"- Stock libraries: `{stock_path}`")
    w("- Regenerate: `uv run python -m generator.stock_compare`")
    w(f"- Pairs compared: {len(results)} "
      f"({counts['OK']} OK, {counts['REVIEW']} REVIEW, "
      f"{counts['FAIL']} FAIL)")
    w("")
    w("Thresholds: pad center REVIEW >"
      f" {CENTER_DEV_REVIEW}mm / FAIL > {CENTER_DEV_FAIL}mm; "
      f"pad size REVIEW > {SIZE_DEV_REVIEW:.0f}% / FAIL > "
      f"{SIZE_DEV_FAIL:.0f}%; courtyard REVIEW > "
      f"{COURTYARD_DEV_REVIEW}mm. Positions are compared after "
      "centroid alignment of the shared pads. 'loose' mappings "
      "(stock part is only an analog) are capped at REVIEW.")
    w("")

    fails = [r for r in results if r.verdict == "FAIL"]
    if fails:
        w("## Open findings (FAIL)")
        w("")
        w("Gross disagreements pointing at probable generator or CSV "
          "data bugs. Each needs to be resolved against IPC-7351B "
          "before Stage B validation can close.")
        w("")
        for r in fails:
            note = f" -- {r.entry.note}" if r.entry.note else ""
            w(f"- **{r.entry.ipc_name}** vs `{r.entry.stock_name}`: "
              f"{r.detail}{note}")
        w("")

    families = sorted({r.entry.family for r in results})
    for family in families:
        fam_results = [r for r in results if r.entry.family == family]
        fam_counts = {v: sum(1 for r in fam_results if r.verdict == v)
                      for v in ("OK", "REVIEW", "FAIL")}
        w(f"## {family} ({fam_counts['OK']} OK, "
          f"{fam_counts['REVIEW']} REVIEW, {fam_counts['FAIL']} FAIL)")
        w("")
        w("| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict "
          "| Notes |")
        w("|---|---|---|---|---|---|---|")
        for r in fam_results:
            pads = (f"{r.shared}" if r.ours_total == r.stock_total == r.shared
                    else f"{r.shared}/{r.ours_total}/{r.stock_total}")
            notes = "; ".join(x for x in (r.entry.note, r.detail) if x)
            w(f"| {r.entry.ipc_name} | {r.entry.stock_name} | {pads} "
              f"| {r.center_dev:.2f}mm | {r.size_dev:.0f}% "
              f"| {r.verdict} | {notes} |")
        w("")

    w("## Footprints without a stock equivalent")
    w("")
    w("Not compared -- KiCad stock has no matching generic footprint. "
      "These need manual validation against IPC-7351B directly.")
    w("")
    for family, lib, name in no_stock:
        w(f"- `{lib}/{name}` (no stock equivalent for this family)")
    for lib, name in unmapped:
        w(f"- `{lib}/{name}`")
    w("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock", type=Path, default=DEFAULT_STOCK,
                        help="path to KiCad stock footprints directory")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT,
                        help="markdown report output path")
    args = parser.parse_args()
    sys.exit(run(args.stock, args.report))


if __name__ == "__main__":
    main()
