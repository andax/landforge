# LandForge Test Plan

This document defines the validation procedures for each stage of LandForge
development. Every sub-stage has both **automated tests** (run via `uv run pytest`)
and **manual validation** procedures to be performed in KiCad.

---

## General Test Environment

- **KiCad version:** 10.0+
- **Python:** 3.10+ (managed by uv)
- **Test runner:** `uv run pytest tests/ -v`
- **OS:** Linux (tested on Ubuntu/Pop!_OS)

### How to Load LandForge Footprints in KiCad

**Add a library (recommended):**

1. Open KiCad > **Preferences > Manage Footprint Libraries...**
2. Click the folder icon ("Add existing library to table")
3. Navigate to `landforge/output/IPC7351B_Chip.pretty/` (or whichever library)
4. Set nickname (e.g., "IPC7351B_Chip")
5. The footprints are now available when placing footprints (press **A** in PCB Editor)

**Inspect a single .kicad_mod file:**

1. Open the **Footprint Editor** (from the KiCad main window or PCB Editor toolbar)
2. **File > Import > Import Footprint...**
3. Navigate to the `.kicad_mod` file

**Place a footprint in the PCB Editor:**

1. Press **A** (or **Place > Add Footprint**)
2. Click on the board — the Footprint Chooser dialog opens
3. Type to search (e.g., `RESC1608` or `0603`)
4. Select the footprint and click OK, then click to place

---

## Stage A: Foundation

### A1: Core Equation Engine

#### Automated Tests

```bash
uv run pytest tests/test_equations.py -v
```

| Test | What It Verifies |
|------|-----------------|
| `TestRounding::test_round_to_005` | Values round UP to 0.05mm grid |
| `TestRounding::test_round_down_to_005` | Values round DOWN to 0.05mm grid |
| `TestRounding::test_round_to_002` | Small chip 0.02mm rounding |
| `TestRMSToleranceAccumulation::test_so16_rms_tolerance` | RMS formula matches IPC-7351B page 11 |
| `TestRMSToleranceAccumulation::test_so16_g_dimension` | G_min calculation for SO16 |
| `TestChipComponentCalculation::test_0603_density_ordering` | Level A > B > C pad dimensions |
| `TestTableCompleteness::test_all_tables_present` | All 22 tables defined |
| `TestTableCompleteness::test_all_tables_have_decreasing_toe_fillet` | Fillet goals decrease A>B>C |

All 22 tests in `test_equations.py` must pass.

#### Manual Verification: IPC-7351B Cross-Check

**Purpose:** Verify calculations against the IPC-7351B standard text.

**Procedure:**

1. Open the IPC-7351B standard PDF

2. Go to page 11 (Section 3.1.1.1, SO16 worked example)

3. Run the following and compare each intermediate value:
   ```bash
   uv run python3 -c "
   from generator.core.ipc_equations import *
   from generator.core.tables import TABLE_3_2
   import math

   spec = ComponentDimensionsFromSpec(
       L_min=5.8, L_max=6.2, T_min=0.4, T_max=1.27, W_min=0.31, W_max=0.51)
   comp = spec.to_component_dimensions()

   print('=== SO16 Worked Example (IPC-7351B p.11) ===')
   print(f'L_tol = {comp.CL:.2f} (expected: 0.40)')
   print(f'S_min = {comp.S_min:.4f}')
   print(f'S_max = {comp.S_max:.4f}')
   print(f'CS (RMS-adjusted) = {comp.CS:.4f}')

   for level in DensityLevel:
       result = calculate_land_pattern(comp, TABLE_3_2, level)
       print(f'Level {level.name}: Z={result.Z:.2f} G={result.G:.2f} X={result.X:.2f}'
             f'  pad={result.pad_length:.3f}x{result.pad_width:.3f}'
             f'  c2c={result.pad_center_to_center:.3f}')
   "
   ```

4. **Check:** L_tol should be 0.40 mm (matches standard)

5. **Check:** The RMS tolerance `S_tol(RMS) = sqrt(0.4^2 + 2*0.87^2)` should be approximately 1.29 mm

6. **Check:** Z should increase and G should decrease from Level C to Level A

**Pass criteria:** All intermediate values match IPC-7351B within rounding precision.

---

### A2: KiCad File Writer + Layer Generators

#### Automated Tests

```bash
uv run pytest tests/test_kicad_writer.py -v
```

All 8 tests must pass.

#### Manual Verification: KiCad File Parsing

**Purpose:** Verify KiCad can parse the generated .kicad_mod files without errors.

**Procedure:**

1. Generate a test footprint:
   ```bash
   uv run python3 -c "
   from tests.test_integration import generate_resc1608
   from generator.core.ipc_equations import DensityLevel
   from generator.core.kicad_writer import write_footprint
   import os

   os.makedirs('output/test_validation', exist_ok=True)
   for level in DensityLevel:
       fp = generate_resc1608(level)
       write_footprint(fp, f'output/test_validation/{fp.name}.kicad_mod')
       print(f'Written: {fp.name}.kicad_mod')
   "
   ```

2. Add `output/test_validation/` as a library:
   **Preferences > Manage Footprint Libraries...** > folder icon >
   navigate to `output/test_validation/`

3. Open KiCad 10 > PCB Editor

4. Press **A** (Add Footprint), click the board, search for `RESC1608` in
   the Footprint Chooser. Place each of the 3 variants (M, N, L).

5. **Check: No parse errors** -- KiCad must load each footprint without warnings or errors

6. **Check: Visual inspection** -- the footprint should render with:
   - Two pads (rounded rectangles)
   - A courtyard rectangle (thin line)
   - A body outline on fabrication layer
   - Silkscreen lines above and below
   - Reference text "REF**" on silkscreen
   - Value text on fabrication layer

7. **Check: Layer assignment** -- in Properties panel verify:
   - Pads are on F.Cu, F.Mask, F.Paste
   - Courtyard is on F.CrtYd
   - Body outline is on F.Fab
   - Silkscreen is on F.SilkS

8. **Check: Pad properties** -- click each pad and verify:
   - Shape: Rounded rectangle
   - Pad type: SMD
   - Layers: F.Cu + F.Mask + F.Paste

**Pass criteria:** All 3 files open in KiCad without errors, all layers are correct.

---

### A3: Naming Convention + Integration Test

#### Automated Tests

```bash
uv run pytest tests/test_integration.py -v
```

All 7 tests must pass.

#### Manual Verification: Side-by-Side Comparison with KiCad Stock

**Purpose:** Compare LandForge Level B output against KiCad's stock `R_0603_1608Metric`.

**Procedure:**

1. Open KiCad PCB Editor, create a new empty board

2. Ensure both KiCad stock libraries and `output/test_validation/` are registered
   (see "How to Load" above)

3. Place the KiCad stock footprint:
   - Press **A**, click the board, search for `R_0603_1608Metric` in the chooser
   - Place it at coordinates (50, 50)

4. Place the LandForge Level B footprint:
   - Press **A**, click the board, search for `RESC1608X055N`
   - Place it at coordinates (60, 50) (10mm to the right)

5. **Measure and compare pads** (use KiCad Measure tool or pad properties):

   | Property | KiCad Stock | LandForge Level B | Acceptable Range |
   |----------|------------|-------------------|-----------------|
   | Pad width (X) | 0.9 mm | ? | 0.7 - 1.1 mm |
   | Pad height (Y) | 0.95 mm | ? | 0.8 - 1.1 mm |
   | Pad center X | ±0.775 mm | ? | ±0.6 to ±1.0 mm |
   | Pad shape | Rounded rect | Rounded rect | Must match |

6. **Measure and compare courtyard:**

   | Property | KiCad Stock | LandForge Level B | Note |
   |----------|------------|-------------------|------|
   | Width | 2.96 mm | ? | Should be similar |
   | Height | 1.46 mm | ? | Should be similar |

7. **Compare all 3 density levels visually:**
   - Place Level A, B, C next to each other (spaced 5mm apart)
   - **Check:** Level A should visually have the largest pads and courtyard
   - **Check:** Level C should have the smallest
   - **Check:** All three should have the same body outline on F.Fab

8. **Screenshot** the comparison and save as `docs/validation/stage_a_comparison.png`

**Pass criteria:**
- Level B pad dimensions are within ±20% of KiCad stock values
- Level A > B > C is visually apparent
- All footprints parse and render correctly

#### Manual Verification: DRC Check

**Purpose:** Verify footprints don't cause KiCad DRC violations.

**Procedure:**

1. With the board from step above still open

2. Run **Inspect > Design Rules Checker**

3. **Check:** No errors related to the LandForge footprints
   (Board-level DRC errors about missing netlist are expected and can be ignored)

4. **Check:** No courtyard overlap warnings between the footprints
   (they should be spaced far enough apart)

**Pass criteria:** No footprint-internal DRC errors.

---

## Stage B: Footprint Generation

### B1: Chip Passives

#### Automated Tests

```bash
uv run pytest tests/ -v -k "chip"
```

Plus: a new test file `tests/test_chip_family.py` (to be written in Stage B) that
verifies all generated chip footprints have valid dimensions.

#### Manual Verification: Batch Visual Inspection

**Purpose:** Spot-check representative footprints from the generated batch.

**Procedure:**

1. After generation, count the output:
   ```bash
   ls output/IPC7351B_Chip.pretty/*.kicad_mod | wc -l
   # Expected: ~300 files
   ```

2. Open KiCad Footprint Editor

3. Add `output/IPC7351B_Chip.pretty/` as a library

4. Browse the library and **inspect at least 6 footprints** spanning the size range:

   | Footprint | Check |
   |-----------|-------|
   | Smallest RESC (01005/0201) | Pads visible, not overlapping body |
   | RESC 0603 Level A, B, C | Size progression correct |
   | CAPC 1206 Level B | Reasonable for a 1206 capacitor |
   | Largest RESC (2512) | Pads proportional to body |
   | INDC 0805 Level B | Same structure as RESC but inductor tags |
   | DIOC 0603 Level B | Polarity mark present (if applicable) |

5. For each inspected footprint verify:
   - [ ] Pads are symmetric
   - [ ] Courtyard encloses both pads and body
   - [ ] Silkscreen does not overlap pads
   - [ ] Fab layer shows body outline at correct size
   - [ ] Reference text is readable
   - [ ] Footprint name matches IPC convention

6. **Size progression test:** Place the same resistor size (e.g., 0805) at all 3
   density levels side by side. Verify A is visually largest, C smallest.

7. **Cross-reference one footprint against KiCad stock:**
   - Pick `RESC3216X065N` (1206 Level B)
   - Compare against KiCad's `R_1206_3216Metric`
   - Pad dimensions should be within ±20%

**Pass criteria:** All checked footprints are visually correct, size progression
works, and at least one cross-reference against stock is within tolerance.

#### Manual Verification: Gerber Output

**Purpose:** Verify footprints produce correct manufacturing data.

**Procedure:**

1. Create a test board with one each of: 0402 Level B, 0603 Level B, 1206 Level B

2. Add copper zones and a board outline

3. Generate Gerber files (**File > Fabrication Outputs > Gerbers (.gbr)**)

4. Open Gerbers in a viewer (KiCad's built-in Gerber viewer or gerbv)

5. **Check copper layer:** Pads are filled, correct size, correct position

6. **Check solder mask layer:** Openings slightly larger than pads

7. **Check paste layer:** Apertures match pad size

8. **Check silkscreen layer:** Lines present, not overlapping pads

9. **Check courtyard:** Not in Gerbers (expected -- courtyard is design-time only)

**Pass criteria:** All Gerber layers render correctly for the test footprints.

---

### B2: Molded Body + MELF + Electrolytic

#### Manual Verification

**Procedure:**

1. Inspect at least 3 footprints:
   - CAPMP (tantalum cap) -- verify polarity mark on fab layer
   - DIOM (molded diode) -- verify polarity mark
   - RESMELF -- verify pad shape appropriate for cylindrical body
   - CAPAE (electrolytic) -- verify pad spacing matches diameter

2. **Special check for Table 3-13 (molded body):**
   - The outer pad extent (Z) should use the HEEL fillet (larger value)
   - The inner gap (G) should use the TOE fillet (smaller value)
   - This is the reverse of gull-wing components
   - Verify by comparing pad_center_to_center: it should be larger relative
     to body size than for a chip resistor of similar dimensions

3. **CAPAE diameter check:** For a 10mm diameter electrolytic, the courtyard
   should be circular-ish (rectangular but roughly matching the body)

---

### B3: SOT / SOD / DPAK

#### Manual Verification

**Procedure:**

1. Generate and place `SOT095P240X110-3N` (SOT-23)

2. Place KiCad stock `SOT-23` next to it

3. **Compare:**
   - 3 pads in correct triangular arrangement
   - Pin 1 at top-left
   - Pad sizes similar to KiCad stock
   - Silkscreen shows pin 1 indicator

4. **DPAK thermal tab check:**
   - Generate a DPAK footprint
   - Verify the large thermal tab pad is present
   - Check paste mask: the thermal pad should have segmented paste apertures
     (not a single large opening)
   - In KiCad, click the thermal pad and verify:
     - Pad property: heatsink
     - Layers include F.Cu and F.Mask
     - Paste is handled separately (via paste aperture pads or custom shape)

5. **SOD polarity check:**
   - Generate a SOD123 footprint
   - Verify cathode marking on fab layer

---

### B4-B5: SOIC / SOP / QFP

#### Manual Verification

**Procedure:**

1. **SOIC-8 comparison:**
   - Generate `SOIC127P600X175-8N`
   - Place next to KiCad stock `SOIC-8_3.9x4.9mm_P1.27mm`
   - Verify: 8 pads, pin 1 at top-left, 1.27mm pitch, correct lead span
   - Measure pin 1-to-pin 1 distance across the body: should be ~6.0mm (lead span)
   - Pad dimensions within ±20% of stock

2. **QFP-48 comparison:**
   - Generate a QFP at 0.5mm pitch, 48 pins
   - Place next to KiCad stock `LQFP-48_7x7mm_P0.5mm`
   - Verify: pads on all 4 sides, 12 per side, pin 1 marked
   - **Pitch check:** measure distance between adjacent pad centers = 0.5mm

3. **Fine pitch clearance check:**
   - For a 0.5mm pitch QFP, verify the gap between adjacent pads is > 0.10mm
   - In KiCad, use the Measure tool between pad edges

4. **Exposed pad variant:**
   - If HTSSOP or MSOP-EP footprints are generated, verify:
     - Center exposed pad is present
     - Paste mask on exposed pad is segmented (multiple smaller rectangles)
     - Exposed pad has heatsink property

---

### B6: J-Leaded (SOJ / PLCC)

#### Manual Verification

**Procedure:**

1. Generate a PLCC-44 footprint

2. Verify: pads on all 4 sides, J-lead pad geometry (wider than gull-wing)

3. **J-lead vs gull-wing pad comparison:**
   - J-lead pads should extend INWARD (under the body) more than outward
   - Compare pad_center_to_center: for J-leads it should be smaller relative
     to body size than gull-wing (leads curl under)

---

### B7: BGA / LGA

#### Manual Verification

**Procedure:**

1. Generate a BGA-256 (1.0mm pitch, 16x16 grid)

2. Open in KiCad and verify:
   - Circular pads arranged in grid
   - Pad naming: A1, A2, ... B1, B2, ... (alpha rows, numeric columns)
   - Pin A1 at top-left corner
   - Pad property: BGA

3. **Pad diameter check:**
   - For a 0.5mm ball, collapsible, Level B: land should be ~0.40mm
   - Measure pad diameter in KiCad properties

4. **Solder mask check:**
   - BGA pads should be NSMD (non-solder-mask-defined)
   - Mask opening should be slightly larger than pad
   - Verify in KiCad: pad solder mask expansion > 0

5. **Courtyard check:**
   - BGA courtyard should be significantly larger than body
   - Level B excess: 1.0mm on each side

---

### B8: QFN / SON / DFN

#### Manual Verification

**Procedure:**

1. Generate `QFN050P500X500X090-32T340N` (QFN-32 + thermal pad)

2. Compare with KiCad stock QFN-32 of similar size

3. **Verify:**
   - Perimeter pads present on all 4 sides
   - Center thermal/exposed pad present
   - Pin 1 marked on silkscreen and fab layer
   - Thermal pad has heatsink property
   - Paste on thermal pad is segmented

4. **Solder mask opening check (IPC 15.2.4):**
   - QFN pad solder mask opening should be 0.075-0.15mm larger than the pad
   - In KiCad pad properties, check solder mask expansion

5. **QFN vs SON:**
   - QFN: pads on 4 sides
   - SON: pads on 2 sides only
   - Generate one of each and verify the difference

---

### B9-B10: LCC + DIP

#### Manual Verification

Quick visual check -- these are lower priority families.

1. LCC: verify castellated pad arrangement (pads at board edge)
2. DIP: verify through-hole pads, correct row spacing (7.62mm or 15.24mm)

---

### B11-B13: Extended Families (WLCSP, SC-70, Crystal)

#### Manual Verification

**Procedure:**

1. **WLCSP:**
   - Generate a WLCSP-49 (7x7, 0.4mm pitch)
   - Verify circular pads in grid (similar to BGA but smaller)
   - Pad diameter should be slightly LARGER than ball (non-collapsible)

2. **SC-70 (SOT-323):**
   - Generate SOT-323 equivalent
   - Compare with KiCad stock `SOT-323_SC-70`
   - 3 pads, pin 1 at top-left

3. **SMD Crystal:**
   - Generate a 3225 4-pin crystal
   - Verify 4 pads in rectangular arrangement
   - Compare with KiCad stock `Crystal_SMD_3225-4Pin_3.2x2.5mm`

---

## Stage C: 3D Models

### C1: Stock Model Reuse Mapping

#### Manual Verification

**Procedure:**

1. Pick 5 footprints that should have stock model mappings:
   - RESC1608X055N (should map to R_0603_1608Metric.step)
   - SOIC127P600X175-8N (should map to SOIC-8_3.9x4.9mm.step)
   - SOT095P240X110-3N (should map to SOT-23.step)
   - A QFP variant
   - A DIP variant

2. For each, open in KiCad PCB editor and press Alt+3 (3D viewer)

3. **Check:** 3D model appears, centered on footprint, correct orientation

4. **Check:** Pin 1 of 3D model aligns with pin 1 of footprint

5. **Check:** Body outline on fab layer matches 3D model body

---

### C2-C5: Generated 3D Models

#### Manual Verification

**Procedure:**

1. After each batch of 3D model generation, pick 3 representative models

2. Open the corresponding footprint in KiCad 3D viewer

3. **Check for each model:**
   - [ ] Model appears (not missing/invisible)
   - [ ] Model is correctly centered on footprint
   - [ ] Model is not floating above or sunk below the board
   - [ ] Pin 1 alignment matches between 2D footprint and 3D model
   - [ ] Body size approximately matches fab layer outline
   - [ ] Leads/terminals align with pads
   - [ ] Colors are realistic (black body, silver leads)

4. **BGA-specific 3D check:**
   - Solder balls should be visible on the bottom of the package
   - Ball grid should align with pad grid

5. **QFN-specific 3D check:**
   - Side terminals should align with perimeter pads
   - Exposed pad on bottom should be visible

---

## Stage D: QA + Release

### D1: Automated Regression

```bash
uv run pytest tests/ -v --tb=long
```

**All tests must pass.** Any failure blocks release.

### D2: Full Library DRC

**Procedure:**

1. Create a test board (`docs/validation/drc_test.kicad_pcb`)

2. Place one footprint from each family (representative selection):
   - RESC 0603 Level B
   - CAPC 0805 Level B
   - CAPMP (tantalum) Level B
   - SOT-23 Level B
   - SOIC-8 Level B
   - QFP-48 Level B
   - PLCC-44 Level B
   - BGA-100 Level B
   - QFN-32 Level B
   - DIP-16 Level B
   - WLCSP-49 Level B
   - SOT-323 Level B
   - Crystal 3225 Level B

3. Space footprints far apart (no overlap)

4. Run DRC

5. **Check:** Zero footprint-related errors

6. **Check:** Courtyard dimensions are present for all footprints

7. Save board as validation reference

### D3: Gerber Verification

**Procedure:**

1. Using the DRC test board from D2

2. Add a board outline and ground plane

3. Generate full Gerber set + drill files

4. Open in Gerber viewer

5. **Check each layer:**

   | Layer | What to Verify |
   |-------|---------------|
   | F.Cu | All pads present, correct size, no gaps |
   | F.Mask | Openings around all pads, no stray openings |
   | F.Paste | Apertures for all SMD pads, thermal pad segmented |
   | F.SilkS | Component outlines visible, no overlap with pads |
   | Edge.Cuts | Board outline present |
   | Drill | Through-hole drill hits for DIP |

6. **Overlay check:** Stack F.Cu + F.Mask in viewer, verify mask openings
   are larger than pads on all sides

### D4: Documentation Review

**Procedure:**

1. Read `docs/user_guide.md` end-to-end

2. Follow the installation instructions -- do they work?

3. Follow the "selecting a footprint" guide -- is it clear?

4. Check that all linked files exist

5. Verify the density level guide matches the IPC-7351B standard

### D5: Release Checklist

- [ ] All automated tests pass
- [ ] DRC test board has zero errors
- [ ] Gerber output is correct
- [ ] Documentation is complete and accurate
- [ ] All output directories contain the expected number of files
- [ ] fp-lib-table entries work in KiCad
- [ ] 3D models load correctly for spot-checked footprints
- [ ] README.md is present and up to date
- [ ] Version tagged in git

---

## Appendix: Quick Reference Commands

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_equations.py -v

# Run tests matching a keyword
uv run pytest tests/ -v -k "chip"

# Generate test footprints for manual inspection
uv run python3 -c "
from tests.test_integration import generate_resc1608
from generator.core.ipc_equations import DensityLevel
from generator.core.kicad_writer import write_footprint
import os
os.makedirs('output/test_validation', exist_ok=True)
for level in DensityLevel:
    fp = generate_resc1608(level)
    write_footprint(fp, f'output/test_validation/{fp.name}.kicad_mod')
    print(f'Written: {fp.name}.kicad_mod')
"

# Count footprints in a library
ls output/IPC7351B_Chip.pretty/*.kicad_mod | wc -l

# Print a footprint's dimensions for debugging
uv run python3 -c "
from generator.core.ipc_equations import *
from generator.core.tables import TABLE_3_5
spec = ComponentDimensionsFromSpec(L_min=1.50, L_max=1.70, T_min=0.20, T_max=0.40, W_min=0.70, W_max=0.90)
comp = spec.to_component_dimensions()
for level in DensityLevel:
    r = calculate_land_pattern(comp, TABLE_3_5, level)
    print(f'{level.name}: Z={r.Z:.2f} G={r.G:.2f} X={r.X:.2f} pad={r.pad_length:.3f}x{r.pad_width:.3f}')
"
```
