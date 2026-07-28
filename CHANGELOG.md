# Changelog

Footprint names are treated as a **stable API**: schematics, database
libraries, and inventory systems reference them as
`LibraryNickname:FootprintName` strings. Names change only when a data
correction changes the dimensions the name encodes, and every rename is
listed here.

## Unreleased (development toward v0.1)

### Fixed (2026-07-28, commits fbb5159 and 714e3e0)

Two validation rounds: an automated comparison against the KiCad 10
stock libraries, followed by a multi-agent adversarial review verified
against the IPC-7351B printed pages. All confirmed findings fixed --
details in `docs/validation/ultracode_review_findings.md` and
`docs/validation/stock_comparison_report.md`. Highlights: Table 3-13
toe/heel application (all molded footprints), Tables 3-2/3-3 Note 1
reduced heel, BGA lands per Table 3-17, DIP through-hole lands per
IPC-2221/7251, JEDEC BGA ball-row lettering, thermal tabs modeled as
flat leads, IPC-7351B 3.1.5.7 paste segmentation on thermal pads,
4-pin crystal pin numbering to the device convention, and
Reference/Value text placement outside the courtyard.

### Renamed (dimension corrections; old name -> new name, all 3 density levels)

| Old | New | Reason |
|---|---|---|
| SOT254P1400X440-3 | SOT254P1520X440-3 | D2PAK span per JEDEC TO-263 |
| SOT035P110X050-3 | SOT035P100X050-3 | SOT-883 leadless, body-flush span |
| SOT035P140X050-6 | SOT035P100X050-6 | SOT-963 leadless, body-flush span |
| SOT095P240X110-5 | SOT095P280X145-5 | SOT-23-5 per JEDEC MO-178 |
| SOT095P240X110-6 | SOT095P280X145-6 | SOT-23-6 per JEDEC MO-178 |
| SOD36027X120 | SOD37016X120 | SOD-123 span/body per datasheets |
| SOD25017X100 | SOD25013X100 | SOD-323 body width/length unswapped |
| SOD16012X060 | SOD16008X060 | SOD-523 body width/length unswapped |
| DIOM5336X240 | DIOM4326X230 | SMA per JEDEC DO-214AC (labels were swapped) |
| DIOM4724X240 | DIOM4336X245 | SMB per JEDEC DO-214AA (labels were swapped) |
| DIOM7661X240 | DIOM6959X260 | SMC per JEDEC DO-214AB |
| QFP065P1400X1400X120-80 | QFP065P1600X1600X120-80 | QFP-80 P0.65 is a 14x14 body (MS-026) |
| QFP050P1600X1600X120-128 | QFP040P1600X1600X120-128 | QFP-128 on 14x14 exists only at P0.4 (MS-026) |

### Removed

- `DIOM2513X110`, `DIOM1608X080`, `DIOM1005X050` (all levels): broken
  duplicates of SOD-123/323/523, which are gull-wing packages correctly
  generated in `IPC7351B_SOT.pretty` as `SOD37016X120`, `SOD25013X100`,
  and `SOD16008X060`.

### Added

- Thermal pad paste segmentation per IPC-7351B 3.1.5.7 (40% coverage).
- Stock-comparison validation tool (`generator/stock_compare.py`) and
  shipped-output invariant tests (`tests/test_invariants.py`).
- `.kicad_mod` reader (`generator/core/kicad_reader.py`).
