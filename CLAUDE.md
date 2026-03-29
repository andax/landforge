# LandForge - Development Guide

IPC-7351B compliant KiCad footprint library generator.

## Project Context

- **Reference standard:** IPC-7351B (June 2010)
- **KiCad stock libraries:** KiCad 10 standard libraries (used for comparison, not as source of truth)
- **Project plan:** See `IPC7351B_library_plan.md` in the companion documents repo
- **KiCad library analysis:** See `Kicad_library_readme.md` in the companion documents repo

## Tooling

- **Python:** managed by `uv` (not pip). Use `uv run`, `uv add`, `uv sync`.
- **Tests:** `uv run pytest tests/ -v`
- **Generate all footprints:** `uv run python3 -m generator.generate_all`

## Project Structure (as-built)

```
landforge/
├── generator/
│   ├── core/                    # Shared engine (equations, writer, layers, naming)
│   │   ├── ipc_equations.py     # Z/G/X equations, RMS tolerance, BGA calc, rounding
│   │   ├── tables.py            # All 22 IPC tolerance tables (3-2 through 3-22)
│   │   ├── kicad_writer.py      # .kicad_mod serializer (format v20260206)
│   │   ├── layers.py            # Courtyard, silkscreen, fab layer generators
│   │   └── naming.py            # IPC-7351B naming convention (Table 3-23)
│   ├── families/                # One module per component family
│   │   ├── ipc7352_chip.py      # RESC, CAPC, CAPCP, INDC, DIOC (Table 3-5/3-6)
│   │   ├── ipc7352_molded.py    # CAPMP, DIOM, INDM, RESM, FUSM, LEDM (Table 3-13)
│   │   ├── ipc7352_melf.py      # RESMELF, DIOMELF (Table 3-7)
│   │   ├── ipc7352_capae.py     # CAPAE electrolytic (Table 3-20)
│   │   └── ipc7352_sot.py       # SOT23/89/143/223, SOD, DPAK/D2PAK (Tables 3-2, 3-14)
│   └── generate_all.py          # Master generation script
├── data/jedec/                  # Component dimension databases (CSV)
│   ├── chip_components.csv      # 45 chip sizes (RESC/CAPC/CAPCP/INDC/DIOC)
│   ├── molded_components.csv    # 23 molded body sizes
│   ├── melf_components.csv      # 6 MELF sizes
│   ├── electrolytic_components.csv  # 14 electrolytic sizes
│   └── sot_components.csv       # 11 SOT/SOD/DPAK packages with pin layouts
├── output/                      # Generated KiCad libraries (.pretty dirs)
│   ├── IPC7351B_Chip.pretty/    # 135 footprints
│   ├── IPC7351B_Molded.pretty/  # 69 footprints
│   ├── IPC7351B_MELF.pretty/    # 18 footprints
│   ├── IPC7351B_Electrolytic.pretty/  # 42 footprints
│   └── IPC7351B_SOT.pretty/    # 33 footprints
├── tests/
│   ├── test_equations.py        # 22 tests: equations, tables, rounding, BGA
│   ├── test_kicad_writer.py     # 8 tests: serialization, formatting
│   └── test_integration.py      # 7 tests: R_0603 at A/B/C, stock comparison
├── docs/
│   ├── test_plan.md             # Stage-by-stage validation procedures
│   └── user_guide.md            # End-user guide for PCB designers
└── pyproject.toml               # uv project config
```

### Planned but not yet implemented

Remaining Stage B families (B4-B13):
- `ipc7353_soic.py` -- SOIC/SOP/SSOP/TSSOP/MSOP (2-side gull-wing ICs, Table 3-2/3-3)
- `ipc7355_qfp.py` -- QFP/TQFP/LQFP (4-side gull-wing, Table 3-2/3-3)
- `ipc7354_soj.py` -- SOJ (2-side J-lead, Table 3-4)
- `ipc7356_plcc.py` -- PLCC (4-side J-lead, Table 3-4)
- `ipc7358_bga.py` -- BGA/FBGA/CGA/LGA (area array, Table 3-17)
- `ipc7359_qfn.py` -- QFN/SON/DFN/PQFN/PSON (no-lead, Tables 3-15/16/18)
- `ipc7359_lcc.py` -- LCC (castellated, Table 3-8)
- `ipc7357_dip.py` -- DIP (through-hole, Table 3-12)
- `ext_wlcsp.py` -- WLCSP (extended, adapts BGA)
- `ext_sc70.py` -- SC-70 family (extended, adapts SOT)
- `ext_crystal.py` -- SMD crystals/oscillators (extended)

## Architecture Decisions

### Family module consolidation

The plan listed separate files for SOT, SOD, and DPAK. In practice, they share the
same multi-pin gull-wing generator -- only the pin layout data (in CSV) differs.
Combined into `ipc7352_sot.py` with a flexible `SotSpec` dataclass that supports
different pin arrangements and optional thermal tabs.

Similar consolidation may happen for:
- SOIC + SOP + SSOP + TSSOP + MSOP → one `ipc7353_soic.py` with pin-count-driven generation
- QFN + SON + DFN → possibly one module since the pad calculation is very similar

### Data-driven design

Each family has:
1. A **generator module** (`generator/families/`) -- implements the template (pad layout,
   layer geometry, naming)
2. A **CSV database** (`data/jedec/`) -- component dimensions from JEDEC/IPC sources
3. A **hook in `generate_all.py`** -- wires them together

Adding a new component size = add a row to the CSV. Adding a new family = write one
module + one CSV + a few lines in generate_all.py.

### Generated output is committed to git

The `output/*.pretty/` directories contain the generated .kicad_mod files and ARE
committed to git. This is intentional:
- Users can clone the repo and use the footprints immediately without running the generator
- Changes to generated output are visible in diffs for review
- The CSV databases + generator are the source of truth; output can always be regenerated

## Coding Conventions

### KiCad orientation

- Component body long axis along **X**
- Pads placed along **X** axis (pin 1 at negative X)
- Y axis is perpendicular to leads
- Pin 1 is always at **top-left** (negative X, negative Y)

### IPC naming (naming.py)

- Chip body dimensions: tenths of mm, 2 digits, no decimal. `1.6mm → "16"`, `0.8mm → "08"`
- Lead span / height / pitch: hundredths of mm, 3 digits. `6.00mm → "600"`, `0.55mm → "055"`
- Density suffix: M (Level A/Most), N (Level B/Nominal), L (Level C/Least)
- Example: `RESC1608X055N` = chip resistor, 1.6×0.8mm body, 0.55mm height, nominal

### Pad conventions

- Shape: `roundrect` with `roundrect_rratio 0.25` (all SMD pads)
- Shape: `circle` for BGA balls
- Layers: `["F.Cu", "F.Mask", "F.Paste"]` for signal pads
- Layers: `["F.Cu", "F.Mask"]` for thermal pads (paste handled separately)
- Property: `PadProperty.HEATSINK` for exposed/thermal pads
- Property: `PadProperty.BGA` for BGA balls

### Layer conventions

| Layer | Width | Content |
|-------|-------|---------|
| F.SilkS | 0.12mm | Component outline hints, pin 1 marker |
| F.CrtYd | 0.05mm | Courtyard rectangle (snapped to 0.05mm grid) |
| F.Fab | 0.10mm | Body outline, ${REFERENCE} text, polarity marks |

### Courtyard calculation

`courtyard = max(body, pad_extent) + 2 * courtyard_excess`, per axis, snapped to 0.05mm grid.
Courtyard excess comes from the tolerance table and varies by density level.

### Tolerance table notes

- Table 3-13 (molded body): toe/heel are **reversed** vs gull-wing. The table data
  already encodes this (heel has the larger value for outer Z dimension).
- Table 3-17 (BGA): uses percentage-based calculation, not Z/G/X equations.
  See `calculate_bga_land_diameter()`.
- Table 3-18 (PQFN/PSON/DFN): uses "periphery" approach. The toe field holds
  the periphery value.

### Rounding

- Standard components: `round_to(value, 0.05)` for Z and X (round up), `round_down_to(value, 0.05)` for G
- Small chip (< 0603): `round_to(value, 0.02)` (Table 3-6)
- Integer micrometer arithmetic internally to avoid float precision issues

### Multi-pin packages (SOT and beyond)

Pin layouts for packages with irregular pin arrangements (SOT-23, SOT-89, DPAK)
are defined in CSV as semicolon-separated triplets:
```
pins = "1:-1:-0.95;2:-1:0.95;3:1:0"
       pin_num:x_side:y_offset
```
Where x_side is -1 (left) or +1 (right), y_offset is mm from center.

For regular IC packages (SOIC, QFP, QFN) with uniform pin arrays, the pin positions
will be generated programmatically from pitch and pin count (not listed in CSV).

## Current Status

**Stage A:** Complete (core engine, 37 tests passing)
**Stage B:** B1-B5, B7-B8, B10-B13 complete. B6 (SOJ/PLCC) and B9 (LCC) deferred.
**Total footprints:** 642 across 12 libraries, generated in 0.08 seconds
