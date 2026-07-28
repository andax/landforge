# LandForge

Parametric KiCad footprint generator for standard JEDEC component packages,
calculated per IPC-7351B at all three density levels.

LandForge takes JEDEC standard component dimensions and runs them through the
IPC-7351B tolerance equations to produce mathematically correct land patterns.
Every pad size, gap, and courtyard traces directly back to the IPC equations
and the JEDEC package specification — no guesswork, no manual drawing.

The included component databases cover **211 standard JEDEC package sizes**
across 12 families (chip passives, molded body, MELF, electrolytic, SOT/SOD,
SOIC/QFP, BGA, QFN/SON/DFN, DIP, WLCSP, SC-70, and SMD crystal). Each size
is generated at all three IPC-7351B density levels, producing **633 ready-to-use
KiCad footprints**. Adding a new component size is a one-line CSV edit;
regeneration takes under 0.1 seconds.

## Why LandForge?

KiCad ships excellent footprints, but only at a single density level (roughly
IPC Level B) with no traceability to the underlying calculations. If you need
tighter spacing for a dense board, or larger pads for prototyping and rework,
you're on your own.

LandForge gives you three IPC-7351B calculated variants of every footprint:

| Level | Suffix | Use Case |
|-------|--------|----------|
| **A — Most** | M | Prototyping, hand-solder, high-reliability, wave solder |
| **B — Nominal** | N | General production, reflow solder (default) |
| **C — Least** | L | High-density, space-constrained, portable devices |

## What's Included

**211 JEDEC package sizes × 3 density levels = 633 footprints** across 12
libraries, covering the major IPC-7351B families plus commonly needed extensions:

| Library | Components | Footprints |
|---------|-----------|----------:|
| IPC7351B_Chip | Resistors, capacitors, inductors, diodes (01005–2512) | 135 |
| IPC7351B_Molded | Tantalum caps, molded diodes/inductors/fuses/LEDs | 60 |
| IPC7351B_MELF | MELF resistors and diodes | 18 |
| IPC7351B_Electrolytic | Aluminum electrolytic capacitors (3–16mm) | 42 |
| IPC7351B_SOT | SOT-23/89/143/223, SOD-123/323/523, DPAK, D2PAK | 33 |
| IPC7351B_SOIC | SOIC, SSOP, TSSOP, MSOP, QFP (8–256 pin) | 126 |
| IPC7351B_BGA | BGA and FBGA (0.50–1.27mm pitch) | 39 |
| IPC7351B_QFN | QFN, SON, DFN with exposed pad | 42 |
| IPC7351B_DIP | DIP through-hole (8–64 pin) | 33 |
| LandForge_WLCSP | Wafer-level chip scale packages | 36 |
| LandForge_SC70 | SC-70 family (SOT-323 through SOT-963) | 39 |
| LandForge_Crystal | SMD crystals and oscillators (2-pin and 4-pin) | 30 |

Every footprint includes:
- Rounded rectangle pads (modern best practice)
- Courtyard calculated per IPC with correct excess per density level
- Silkscreen with pad clearance and pin 1 indicator
- Fabrication layer with body outline and reference text
- Full traceability metadata (IPC table, equation inputs, calculated Z/G/X)
- 3D model reference (KiCad stock models where available)

## Quick Start

### Use the pre-built library

The `output/` directory contains pre-generated footprints for all 211 standard
JEDEC package sizes. No build step required — just point KiCad at the libraries:

1. Clone this repository
2. In KiCad: **Preferences → Manage Footprint Libraries**
3. Add the `.pretty` directories from `output/` you need
4. Footprints are now available in the footprint browser — search by IPC name
   (e.g., `RESC1608`) or common name (e.g., `0603`, `resistor`)

### Add a component size or regenerate

The pre-built library covers the standard JEDEC sizes. If your component uses
a non-standard package, add its dimensions to the appropriate CSV in `data/jedec/`
and regenerate:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and set up
git clone https://github.com/yourusername/landforge.git
cd landforge
uv sync

# Run tests
uv run pytest tests/ -v

# Regenerate all footprints
uv run python3 -m generator.generate_all
```

Generation takes under 0.1 seconds for all 633 footprints.

## Reading the Footprint Names

Every footprint uses the IPC-7351B naming convention:

```
RESC1608X055N
│   │   │   └── N = Nominal (Level B). M = Most (A), L = Least (C)
│   │   └────── Height: 0.55 mm
│   └────────── Body: 1.6 × 0.8 mm (metric 1608 = EIA 0603)
└────────────── Chip Resistor

SOIC127P600X175-8N
│   │   │   │   │└── Density level
│   │   │   │   └─── 8 pins
│   │   │   └─────── Height: 1.75 mm
│   │   └─────────── Lead span: 6.00 mm
│   └─────────────── Pitch: 1.27 mm
└─────────────────── SOIC package

QFN050P500X500X090-32T340N
│  │   │       │   │  │  └── Density level
│  │   │       │   │  └──── Thermal pad: 3.40 mm
│  │   │       │   └─────── 32 pads (+ thermal)
│  │   │       └─────────── Height: 0.90 mm
│  │   └─────────────────── Body: 5.00 × 5.00 mm
│  └─────────────────────── Pitch: 0.50 mm
└────────────────────────── QFN package
```

## Choosing a Density Level

| Situation | Level |
|-----------|-------|
| First prototype, might need rework | **A** (suffix M) |
| General production, reflow solder | **B** (suffix N) |
| High-reliability / aerospace / medical | **A** (suffix M) |
| Dense consumer electronics (phone, wearable) | **C** (suffix L) |
| Hand-soldering by technicians | **A** (suffix M) |
| Not sure | **B** (suffix N) |

See the [User Guide](docs/user_guide.md) for detailed guidance.

## How It Works

LandForge is a parametric generator, not a collection of manually drawn footprints.
The inputs are JEDEC component dimensions; the outputs are IPC-7351B compliant
KiCad footprints.

1. **JEDEC component databases** (`data/jedec/*.csv`) — standard package dimensions
   from JEDEC publications, one CSV per component family (211 sizes total)
2. **IPC-7351B equations** (`generator/core/ipc_equations.py`) — Z/G/X tolerance
   calculations from Section 3.1.5, with RMS tolerance accumulation
3. **IPC tolerance tables** (`generator/core/tables.py`) — all 22 IPC tables (3-2
   through 3-22) with fillet goals and courtyard excess per density level
4. **Family generators** (`generator/families/`) — pad layout templates for each
   package type (chip, molded, gull-wing, BGA, QFN, etc.)
5. **KiCad writer** (`generator/core/kicad_writer.py`) — serializes to `.kicad_mod`
   format (version 20260206)

```
JEDEC dimensions (CSV) → IPC-7351B equations → KiCad footprints (.kicad_mod)
                          ↑
                     22 tolerance tables
                     3 density levels (A/B/C)
```

Adding a new component size is a one-line CSV edit. Adding a new package family is
one Python module. Regeneration of all 633 footprints takes under 0.1 seconds.

## Project Structure

```
landforge/
├── generator/
│   ├── core/           # Equation engine, KiCad writer, layer generators, naming
│   ├── families/       # One module per component family (12 generators)
│   └── generate_all.py # Master generation script
├── data/jedec/         # JEDEC standard package dimensions (CSV, 211 sizes)
├── output/             # Generated KiCad libraries (.pretty directories)
├── tests/              # 61 automated tests (equations, invariants, stock comparison)
└── docs/
    ├── user_guide.md   # End-user guide for PCB designers
    ├── test_plan.md    # Validation procedures per development stage
    ├── kicad_alignment_review.md  # KiCad roadmap/ecosystem fit review
    └── validation/     # Validation evidence (stock comparison, review findings)
```

## Reference Standards

**IPC-7351B** (June 2010) — *Generic Requirements for Surface Mount Design and
Land Pattern Standard*. Published by IPC (Association Connecting Electronics
Industries). Defines the equations, tolerance tables, and naming conventions
used by LandForge. Covers component families IPC-7352 through IPC-7359
(discrete, gull-wing, J-lead, DIP, area array, and no-lead packages).

**JEDEC package standards** — The component dimension databases in `data/jedec/`
are derived from JEDEC standard package outlines (e.g., TO-236 for SOT-23,
MO-178 for SOT-23-5/6, MS-026 for LQFP, MO-220 for QFN, DO-214 for SMA/SMB/SMC). These define the physical dimensions (body size, lead span,
terminal width, tolerances) that feed into the IPC-7351B equations. When a
component conforms to a standard JEDEC package, the pre-generated footprint is
the correct IPC-7351B land pattern for that component.

## Validation

The library is validated in three independent ways (evidence in `docs/validation/`):

1. **Automated stock comparison** — every Level B footprint with a KiCad stock
   counterpart (167 pairs) is compared for pad numbering, positions, sizes, and
   courtyard: currently 81 match closely, 86 differ for documented reasons
   (IPC vs vendor-derived patterns), 0 unexplained.
2. **Shipped-output invariants** — every generated footprint is checked for
   overlapping pads, positive pad gaps, silkscreen text clear of copper, and
   density-level monotonicity on every regeneration.
3. **Multi-agent adversarial review** (2026-07) — equations and all 22 tolerance
   tables verified against the IPC-7351B text and rendered pages; all confirmed
   findings fixed (see `docs/validation/ultracode_review_findings.md`).

KiCad stock is used as a cross-check only; IPC-7351B is the source of truth.

## Status

- **Stage A** (Foundation): Complete — equation engine, KiCad writer
- **Stage B** (Footprints): Code complete and machine-validated — 633 footprints
  across 12 libraries, 61 tests; manual KiCad visual/Gerber spot checks remain
- **Stage C** (3D Models): Next — stock STEP model mapping first, then
  parametric CadQuery STEP generation from the same JEDEC databases
- **Stage D** (QA/Release): Planned — KiCad PCM packaging (`metadata.json` +
  addon zip), density selection guide, tagged releases with changelog

See `docs/kicad_alignment_review.md` for how this roadmap tracks KiCad's own
direction (data-generated footprints, STEP-only 3D, PCM distribution), and
`CHANGELOG.md` for footprint renames — names are treated as a stable API.

## Contributing

**Adding a new component size** — find the JEDEC package dimensions from the
component datasheet, add a row to the appropriate CSV in `data/jedec/`, and
regenerate. The IPC equations handle the rest.

**Adding a new package family** — create a generator module in `generator/families/`
following the existing patterns (see `ipc7352_chip.py` for a simple example),
add a CSV for the JEDEC dimensions, and wire it into `generate_all.py`.

Run tests before submitting:

```bash
uv run pytest tests/ -v
```

## License

[MIT](LICENSE)
