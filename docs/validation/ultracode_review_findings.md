# Ultracode Multi-Agent Review Findings

Date: 2026-07-28. 23 agents (7 specialized reviewers + 16 adversarial
verifiers) over the full codebase, data, and shipped output, with the
IPC-7351B text as reference. 46 raw findings; the top 16 (all critical
and major) were adversarially verified: **16 confirmed, 0 refuted**.
30 minor raw findings remain unverified (see workflow transcript).

**STATUS: ALL ROOT CAUSES FIXED (same day).** Every table value involved
was re-verified against the rendered PDF pages (not the OCR text layer):
the OCR was faithful, and Table 3-13's "(to find G)/(to find Z)" labels
are confirmed on the printed page. Fixes: TABLE_3_13 pre-swapped; Note 1
reduced heel implemented (engine, Tables 3-2/3-3); BGA lands per Table
3-17 exactly; Reference/Value text placed outside the courtyard; molded
CSV corrected (SOD dup rows deleted, DO-214 dims from JEDEC, Kemet
terminal widths); QFP-80/128 replaced with real MS-026 variants;
SOT-23-5/6 on MO-178; SOD bodies unswapped with realistic tolerances;
4-pin crystals renumbered to the device convention (pin 1 bottom-left
CCW) with matching fab mark; negative-G now raises in the engine; new
shipped-output invariant tests (pad overlap, positive gap, reference
placement, density monotonicity) run over all 633 footprints.
Post-fix: 61 tests pass; stock comparison 167 pairs, 81 OK, 86
annotated REVIEW, 0 FAIL. Renames: SOT095P280X145-5/-6,
SOD37016X120/SOD25013X100/SOD16008X060, DIOM4326X230/DIOM4336X245/
DIOM6959X260, QFP065P1600X1600X120-80, QFP040P1600X1600X120-128;
deleted: DIOM2513/DIOM1608/DIOM1005 (gull-wing SODs, correctly covered
in the SOT library).

Grouped below by root cause. "Shipped" = committed files in output/.

## Critical

### RC1. TABLE_3_13 toe/heel inverted -- all 69 molded footprints wrong; 16 have overlapping (shorted) pads

`tables.py` TABLE_3_13 stores the standard's values as labeled
(toe=0.25/0.15/0.07, heel=0.80/0.50/0.20), but IPC-7351B labels them
"Toe (to find **G**)" / "Heel (to find **Z**)" -- and
`calculate_land_pattern` always computes Z from `toe` and G from `heel`.
The analogous reversed tables 3-4 and 3-8 are stored pre-swapped; 3-13
is not, and the `ipc7352_molded.py` docstring asserting it is correct is
backwards. Effect: every molded footprint's Z and G are 1.10/0.70/0.26 mm
(A/B/C) too small -- pads sit up to 0.65 mm/side inboard, and 16 shipped
footprints have **negative G with physically overlapping anode/cathode
pads** (worst: DIOM1005X050M, 1.30 mm copper overlap).

This also invalidates part of the stock comparison report: the molded
"REVIEW" offsets were attributed to vendor differences, but the shipped
pads are *inboard* of stock -- the bug, not vendor divergence, explains
them (correct CAPMP3216 Level B pads: +/-1.3875; stock +/-1.3525;
shipped +/-1.0375).

**Fix:** swap TABLE_3_13 to toe=0.80/0.50/0.20, heel=0.25/0.15/0.07;
fix the molded docstring; regenerate.

### RC2. molded_components.csv: five bad rows

- **SOD-123/323/523 rows are wrong duplicates** -- body length fed into
  the terminal-span field, so pads land under the plastic and 6 of 9
  footprints short. These packages are gull-wing (IPC itself names
  SOD-123 as such) and are already correctly generated in the SOT
  library. **Fix: delete the three DIOM SOD rows.**
- **SMA/SMB/SMC rows** hold DO-214 *body* width in the terminal-width
  column (pads ~2x taller than the terminal), and SMB/SMC spans are
  short vs JEDEC (SMB overall 5.00-5.59, SMC 7.75-8.26). **Fix: correct
  to DO-214AC/AA/AB terminal dims** (b: 1.27-1.63 / 1.96-2.21 /
  2.79-3.18).

### RC3. gullwing_ic.csv: two geometrically impossible QFP rows

QFP-80 @ 0.65 mm on a 12 mm body (needs 12.35 mm) and QFP-128 @ 0.5 mm
on a 14 mm body (needs 15.5 mm). All 6 shipped footprints have corner
pads from adjacent sides physically crossing (up to 0.5 mm copper
overlap = shorted adjacent pins). Real packages: QFP-80 P0.65 is
14x14 mm/16 mm span; QFP-128 P0.5 is 14x20 mm (rectangular).
**Fix: replace both rows with the real JEDEC MS-026 variants** (the
generator already supports rectangular bodies/spans).

### RC4. sot_components.csv: SOT-23-5/-6 and SOD body dims wrong

- **SOT-23-5/-6 copy the 3-lead TO-236 row.** The real package is JEDEC
  MO-178: span 2.60-3.00 (not 2.10-2.70), body 1.60 wide, height max
  1.45, lead width 0.30-0.50. Shipped pads sit ~0.2 mm/side inboard and
  the names encode a nonexistent package (correct: SOT095P280X145-5N).
- **SOD-123/323/523 have body_width/body_length swapped** (long axis
  perpendicular to the pads): fab outline rotated 90 degrees, courtyard
  oversized in Y, cathode mark misplaced, and the IPC name encodes the
  wrong body dimension. **Fix both; renames follow.**

### RC5. 4-pin crystal/oscillator pin numbering is electrically wrong

`ext_crystal.py` numbers 4-pin parts IC-style (1=top-left, CCW down the
left column). The universal device convention (verified against 10+
vendor footprints) is 1=bottom-left CCW with pins 1-2 along the long
edge. Because the pad grid is rectangular, no physical rotation
reconciles them: with a standard oscillator pinout every pin
(EN/GND/OUT/VDD) lands on the wrong pad. Affects all 18 OSCL
footprints. The earlier stock-comparison pinmap flag treated this as a
naming convention difference -- it is not. **Fix: renumber to
bottom-left CCW; drop the pinmap workaround from the map.**

## Major

### RC6. Tables 3-2/3-3 Note 1 (reduced heel) not implemented

For gull-wing parts where S_min <= A_max (heel under the body) the
standard requires reduced heel goals 0.25/0.15/0.05 unless lead-length
tolerance > 0.5. Not implemented anywhere; SOT-23 family, SOT-89,
SODs, and the SC70 micro packages get G up to 0.40 mm too small --
this is also the root cause of the 0.05 mm pad overlaps in shipped
SOT-553/563 footprints. **Fix: implement the conditional heel reduction
in the engine (caller supplies body A dimension).**

### RC7. BGA land diameter uses an invented percentage matrix

`calculate_bga_land_diameter` mixes density and ball-size breakpoints
found in neither Table 3-17 (density-only: -25/-20/-15% collapsing,
+15/+10/+5% non-collapsing) nor Tables 14-5/14-6 (ball-size-only).
Shipped BGA/WLCSP lands are one 0.05 step off (e.g. BGA100C100 land
0.45 vs correct 0.40; WLCSP bumps get +0% instead of +10%, and Level C
even *reduces* non-collapsing lands). **Fix: implement Table 3-17
exactly.**

### RC8. Reference silkscreen text hardcoded at (0,-1.5)

The writer emits `REF**` at (0,-1.5) on F.SilkS for every footprint;
in 211 of 642 shipped footprints the text box overlaps copper (all
BGAs/QFNs, most chips, the DPAK tab, etc.). **Fix: place the Reference
above the courtyard, computed per footprint.**

## Systemic gaps the review exposed

1. **No pad-overlap invariant test.** 31 shipped files contain
   overlapping different-numbered pads today; nothing in tests/ or the
   generators checks G > 0 or pad-to-pad clearance. Add a generation-time
   guard (error on negative G) and a shipped-output invariant test.
2. **Stock-comparison blind spots.** Footprints without stock mappings
   (QFP-80/128, DIOM SODs) were listed but never geometry-checked;
   `loose` REVIEW rows hid real defects (molded, SOT-23-5). The
   comparison is a cross-check, not a proof -- invariant tests must
   carry what stock cannot.
3. **stock_comparison_report.md misattributions.** Molded and DIOM
   REVIEW notes claim "IPC intentionally larger / vendor differs" where
   the true cause was RC1/RC2. Regenerate after fixes.

## Suggested fix order

1. RC1 (table swap) + RC6 (Note 1 heel) + RC7 (BGA %) -- engine/tables.
2. RC2/RC3/RC4 CSV corrections (renames: SOT-23-5/6, SODs, QFP-80/128).
3. RC5 crystal renumbering; RC8 reference placement.
4. Add negative-G guard + pad-overlap invariant test (all 642 files).
5. Regenerate, update kicad_stock_map.csv (renames, remove crystal
   pinmap, fix notes), rerun comparison, update baselines and docs.
