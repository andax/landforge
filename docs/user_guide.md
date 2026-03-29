# LandForge User Guide

A practical guide for PCB designers using the LandForge IPC-7351B footprint library
in KiCad.

---

## Table of Contents

1. [Installation](#1-installation)
2. [Library Organization](#2-library-organization)
3. [Understanding Density Levels](#3-understanding-density-levels)
4. [Choosing the Right Density Level](#4-choosing-the-right-density-level)
5. [Selecting Footprints](#5-selecting-footprints)
6. [Reading the IPC Name](#6-reading-the-ipc-name)
7. [Design Workflow](#7-design-workflow)
8. [Courtyard and Spacing](#8-courtyard-and-spacing)
9. [Solder Paste and Stencils](#9-solder-paste-and-stencils)
10. [Thermal Pad Handling](#10-thermal-pad-handling)
11. [BGA Considerations](#11-bga-considerations)
12. [Mixing with KiCad Stock Library](#12-mixing-with-kicad-stock-library)
13. [Common Questions](#13-common-questions)

---

## 1. Installation

### 1.1 Adding the Footprint Libraries

1. Open KiCad > **Preferences > Manage Footprint Libraries**
2. Select the **Project Libraries** tab (for per-project use) or **Global Libraries**
   tab (for all projects)
3. Click the **folder icon** ("Add existing library to table")
4. Navigate to `landforge/output/` and select the `.pretty` directories you need

**Recommended minimum set for most projects:**

| Library | Contains |
|---------|---------|
| `IPC7351B_Chip.pretty` | Resistors, capacitors, inductors, diodes (chip) |
| `IPC7351B_Molded.pretty` | Tantalum caps, molded diodes/inductors |
| `IPC7351B_SOT.pretty` | SOT23, SOT223, SOT89, SOT143 |
| `IPC7351B_SOIC.pretty` | SOIC, SOP, SSOP, TSSOP, MSOP |
| `IPC7351B_QFN.pretty` | QFN packages |
| `IPC7351B_BGA.pretty` | BGA, FBGA |
| `LandForge_Crystal.pretty` | SMD crystals and oscillators |

### 1.2 Adding the 3D Model Path

1. Open KiCad > **Preferences > Configure Paths**
2. Add a new path variable:
   - **Name:** `LANDFORGE_3DMODEL_DIR`
   - **Path:** `/path/to/landforge/output_3d/`
3. Click OK

### 1.3 Verifying Installation

1. Open the Footprint Browser (in Schematic Editor or PCB Editor)
2. Search for "RESC" -- you should see chip resistor footprints
3. Open one -- it should render with pads, courtyard, silkscreen, and fab layer

---

## 2. Library Organization

LandForge footprints are organized by **IPC component family**, not by component
function. This differs from KiCad's stock library where resistors, capacitors, and
inductors are in separate libraries even though they use the same package.

```
IPC7351B_Chip.pretty/       ← All 2-terminal chip packages (R, C, L, D)
IPC7351B_Molded.pretty/     ← Molded body packages (tantalum, power inductors)
IPC7351B_MELF.pretty/       ← MELF cylindrical packages
IPC7351B_SOT.pretty/        ← SOT23, SOT89, SOT143, SOT223
IPC7351B_SOD.pretty/        ← SOD123, SOD323, SODFL
IPC7351B_DPAK.pretty/       ← DPAK, D2PAK
IPC7351B_Electrolytic.pretty/ ← Aluminum electrolytic
IPC7351B_SOIC.pretty/       ← SOIC, SOP, SSOP, TSSOP, MSOP
IPC7351B_QFP.pretty/        ← QFP, LQFP, TQFP
IPC7351B_SOJ.pretty/        ← SOJ (J-lead)
IPC7351B_PLCC.pretty/       ← PLCC (J-lead 4-side)
IPC7351B_DIP.pretty/        ← DIP through-hole
IPC7351B_BGA.pretty/        ← BGA, FBGA, CGA, LGA
IPC7351B_QFN.pretty/        ← QFN
IPC7351B_SON.pretty/        ← SON
IPC7351B_DFN.pretty/        ← DFN, PQFN, PSON
IPC7351B_LCC.pretty/        ← LCC (leadless chip carrier)
LandForge_WLCSP.pretty/    ← Wafer-level chip scale
LandForge_SC70.pretty/      ← SC-70 SOT variants
LandForge_Crystal.pretty/   ← SMD crystals and oscillators
```

Each library contains footprints at **all three density levels** (A, B, C).
The density level is indicated by the suffix letter in the footprint name.

---

## 3. Understanding Density Levels

Every LandForge footprint exists in three variants, corresponding to the three
IPC-7351B density levels:

### Level A -- Most Land Protrusion (suffix: M)

- **Largest pads** and most courtyard space
- Maximum solder fillet for best mechanical strength
- Best for prototyping, hand-soldering, rework
- Best for high-reliability products (medical, aerospace, automotive)
- Best for wave soldering
- Courtyard excess: typically 0.50mm per side

### Level B -- Nominal Land Protrusion (suffix: N)

- **Standard pad sizes** for general production
- Robust solder joints suitable for most products
- **Default choice** for typical reflow-soldered designs
- Good balance between reliability and board density
- Courtyard excess: typically 0.25mm per side

### Level C -- Least Land Protrusion (suffix: L)

- **Smallest pads** for maximum board density
- Minimum solder joint -- still meets IPC-A-610 acceptability
- For space-constrained designs (mobile, wearables, IoT)
- Requires tighter process control during assembly
- Not recommended for wave soldering
- May not be suitable for all product classes
- Courtyard excess: typically 0.10mm per side

### Quick Decision Matrix

| Situation | Recommended Level |
|-----------|------------------|
| First prototype, might need rework | **A** |
| General production, reflow solder | **B** |
| High-reliability / aerospace / medical | **A** |
| Dense consumer electronics (phone, watch) | **C** |
| Mixed SMD + through-hole, wave solder | **A** |
| Hand-soldering by technicians | **A** |
| Automated pick-and-place + reflow | **B** or **C** |
| Lead-free process (requires more wetting) | **A** or **B** |
| Space is tight but reliability matters | **B** |

---

## 4. Choosing the Right Density Level

### 4.1 Project-Wide vs. Per-Component Selection

You can use the same density level for the entire board, or mix levels:

**Same level everywhere (recommended for most projects):**
- Simpler to manage
- Consistent courtyard spacing
- Assembly house knows what to expect

**Mixed levels (advanced):**
- Use Level C for dense areas (under RF shields, around BGA breakout)
- Use Level A for power components that need thermal relief
- Use Level B for everything else

IPC-7351B explicitly supports mixing: "The use of one level for a specific feature
does not mean that other features must be of the same level."

### 4.2 Combining Density Level with IPC Performance Class

IPC-7351B density levels combine with IPC performance classes (1, 2, 3):

| | Class 1 (Consumer) | Class 2 (Dedicated Service) | Class 3 (High Reliability) |
|---|---|---|---|
| **Level A** | 1A -- Overkill | 2A -- Conservative | **3A -- Recommended** |
| **Level B** | **1B -- Typical** | **2B -- Standard** | 3B -- Acceptable |
| **Level C** | 1C -- Dense | 2C -- Tight | 3C -- Use with caution |

### 4.3 Assembly House Considerations

Before choosing Level C, confirm with your assembly house:
- What is their placement accuracy? (Level C assumes ±0.05mm or better)
- What is their solder paste printing capability?
- Do they have experience with fine-pitch / high-density boards?

If in doubt, **use Level B**. It works for everything.

---

## 5. Selecting Footprints

### 5.1 From a Schematic Symbol

When assigning footprints in the KiCad Schematic Editor:

1. Open the symbol properties (double-click or press E)
2. Click the Footprint field
3. In the footprint browser, search using any of:
   - **IPC name:** `RESC1608` (finds all 0603 resistor variants)
   - **EIA code:** `0603` (finds all 0603-sized components)
   - **Metric code:** `1608` (same as above)
   - **Component type:** `resistor chip`
   - **Density level:** `density_B` (finds all Level B footprints)

4. Choose the correct variant based on:
   - Component type (RESC for resistor, CAPC for capacitor, etc.)
   - Body size (must match your component's datasheet dimensions)
   - Density level (M, N, or L suffix)

### 5.2 Step-by-Step: Selecting a Footprint for a 100nF 0402 Capacitor

1. Look up the component datasheet
2. Find the package dimensions:
   - Body: 1.0 x 0.5 mm (EIA 0402, metric 1005)
   - Height: 0.5 mm
   - Terminal length: 0.15 - 0.30 mm

3. In the footprint browser, search for `CAPC1005` or `0402`

4. You'll see three variants:
   - `CAPC1.00.5X050M` -- Level A (largest pads)
   - `CAPC1.00.5X050N` -- Level B (standard)
   - `CAPC1.00.5X050L` -- Level C (smallest pads)

5. Choose based on your project's density level decision

6. Assign the footprint to the symbol

### 5.3 Step-by-Step: Selecting a Footprint for an STM32 in LQFP-48

1. Datasheet says: LQFP-48, 7x7mm body, 0.5mm pitch, 1.4mm height

2. Search for `QFP50P` (QFP at 0.50mm pitch) or `LQFP-48` in tags

3. Find: `QFP50P900X900X140-48N`
   - 0.50mm pitch
   - 9.00mm lead span (each direction)
   - 1.40mm height
   - 48 pins
   - Level B (nominal)

4. Verify the lead span matches your datasheet:
   - Body 7.0mm + leads extending ~1.0mm each side = ~9.0mm span

5. Assign to symbol

### 5.4 Step-by-Step: Selecting a Footprint for a QFN-32

1. Datasheet says: QFN-32, 5x5mm body, 0.5mm pitch, exposed pad 3.4x3.4mm

2. Search for `QFN50P500X500` (QFN at 0.50mm pitch, 5x5mm)

3. Find: `QFN50P500X500X100-33T340N`
   - 0.50mm pitch
   - 5.00 x 5.00mm body
   - 1.00mm height
   - 33 pads (32 signal + 1 thermal)
   - Thermal pad 3.40mm
   - Level B

4. **Important:** The thermal pad dimension (T340 = 3.40mm) must match your
   component's exposed pad. If the datasheet says 3.1mm, you need a different
   variant or must adjust.

---

## 6. Reading the IPC Name

Every LandForge footprint name is a standardized IPC-7351B identifier that encodes
the physical dimensions. Here's how to decode it:

### 6.1 Chip Components (2-terminal)

```
RESC 1.6 0.8 X 055 N
│    │   │   │ │   └── Density: N=Nominal (Level B)
│    │   │   │ └────── Height: 0.55 mm
│    │   │   └──────── Separator
│    │   └──────────── Body width: 0.8 mm
│    └──────────────── Body length: 1.6 mm
└───────────────────── Prefix: Chip Resistor
```

**Prefixes:** RESC (resistor), CAPC (capacitor), CAPCP (cap polar), INDC (inductor),
DIOC (diode)

### 6.2 Leaded IC Packages

```
SOIC 127 P 600 X 175 - 8 N
│    │   │ │   │ │   │ │ └── Density: N=Nominal
│    │   │ │   │ │   │ └──── Pin count: 8
│    │   │ │   │ │   └────── Separator
│    │   │ │   │ └────────── Height: 1.75 mm
│    │   │ │   └──────────── Separator
│    │   │ └──────────────── Lead span: 6.00 mm
│    │   └────────────────── P = Pitch follows
│    └────────────────────── Pitch: 1.27 mm
└─────────────────────────── Prefix: SOIC
```

### 6.3 No-Lead Packages (QFN, SON)

```
QFN 50 P 500 X 500 X 100 - 33 T 340 N
│   │  │ │   │ │   │ │   │ │  │ │   └── Density
│   │  │ │   │ │   │ │   │ │  │ └────── Thermal pad: 3.40 mm
│   │  │ │   │ │   │ │   │ │  └──────── T = Thermal pad follows
│   │  │ │   │ │   │ │   │ └────────── Total pad count (incl. thermal)
│   │  │ │   │ │   │ │   └──────────── Separator
│   │  │ │   │ │   │ └──────────────── Height: 1.00 mm
│   │  │ │   │ │   └────────────────── Separator
│   │  │ │   │ └────────────────────── Body length: 5.00 mm
│   │  │ │   └──────────────────────── Separator
│   │  │ └──────────────────────────── Body width: 5.00 mm
│   │  └────────────────────────────── P = Pitch follows
│   └───────────────────────────────── Pitch: 0.50 mm
└────────────────────────────────────── Prefix: QFN
```

### 6.4 BGA

```
BGA 100 C 100 P 10 X 10 _ 1200 X 1200 X 185 N
│   │   │ │   │ │  │ │  │ │    │ │    │ │   └── Density
│   │   │ │   │ │  │ │  │ │    │ │    │ └────── Height: 1.85mm
│   │   │ │   │ │  │ │  │ │    │ └────────────── Body width: 12.00mm
│   │   │ │   │ │  │ │  │ └────────────────────── Body length: 12.00mm
│   │   │ │   │ │  │ │  └──────────────────────── Separator
│   │   │ │   │ │  │ └─────────────────────────── Ball rows: 10
│   │   │ │   │ │  └───────────────────────────── Separator
│   │   │ │   │ └──────────────────────────────── Ball columns: 10
│   │   │ │   └────────────────────────────────── P = Pitch follows
│   │   │ └────────────────────────────────────── Pitch: 1.00mm
│   │   └──────────────────────────────────────── C=Collapsible, N=Non-collapsible
│   └──────────────────────────────────────────── Total ball/pin count
└──────────────────────────────────────────────── Prefix: BGA
```

### 6.5 Density Suffix Quick Reference

| Suffix | Level | Meaning |
|--------|-------|---------|
| **M** | A | **M**ost land protrusion (largest pads) |
| **N** | B | **N**ominal land protrusion (standard) |
| **L** | C | **L**east land protrusion (smallest pads) |

---

## 7. Design Workflow

### 7.1 Recommended Workflow

1. **Start of project:** Decide on density level for the board (usually B)

2. **Schematic capture:**
   - Select components in schematic
   - Assign footprints using the density level suffix you chose
   - For components needing different density (e.g., power parts), use Level A

3. **PCB layout:**
   - Import netlist / update PCB
   - All footprints come in with correct pads and courtyard
   - Use courtyard clearance checking during placement

4. **DRC:**
   - Run Design Rules Check
   - Courtyard violations indicate components too close together
   - The courtyard already includes the IPC-recommended clearance for your
     density level, so courtyard-to-courtyard clearance of 0 is acceptable

5. **Manufacturing output:**
   - Generate Gerbers -- paste layer will have correct apertures
   - Generate pick-and-place file -- component centers are at footprint origin
   - Generate BOM -- IPC names in footprint field aid procurement

### 7.2 Switching Density Levels Mid-Project

If you need to switch from Level B to Level C (e.g., board is too large):

1. In Schematic Editor, use Edit > Find and Replace on footprint fields
2. Replace suffix `N"` with `L"` (careful with quotes to avoid partial matches)
3. Update PCB from schematic
4. Re-run DRC -- some components may now be too close (reduced courtyard)

---

## 8. Courtyard and Spacing

### 8.1 What the Courtyard Means

The courtyard rectangle represents the **minimum keep-out area** around a component.
It accounts for:
- The component body
- The land pattern (pads)
- Pick-and-place nozzle clearance
- Minimum electrical/mechanical clearance to adjacent components

### 8.2 Courtyard Clearance Rules

| Density Level | Typical Courtyard Excess | Meaning |
|---------------|------------------------:|---------|
| A (Most) | 0.50 mm per side | Generous spacing -- easy to rework |
| B (Nominal) | 0.25 mm per side | Standard spacing |
| C (Least) | 0.10 mm per side | Tight spacing -- limited rework access |

**In KiCad DRC:** Set the courtyard clearance rule to **0 mm**. The courtyard
already includes the IPC-specified excess. Any overlap means the IPC spacing
is violated.

### 8.3 BGA Courtyard

BGA packages have much larger courtyard excess (2.0 / 1.0 / 0.5 mm) because
they need space for rework equipment (hot-air nozzle) and board-level testing.

---

## 9. Solder Paste and Stencils

### 9.1 Standard Pads

For regular SMD pads, the paste aperture matches the copper pad 1:1.
No manual adjustment is needed.

### 9.2 Fine-Pitch Pads (<=0.5mm)

Fine-pitch pads may have slightly reduced paste apertures (90-95% of pad size)
to prevent solder bridging. This is handled automatically by LandForge for
applicable families.

### 9.3 Thermal Pad Paste (Exposed Pads)

Large exposed pads (QFN, DPAK, QFP-EP) have **segmented paste apertures** to
prevent voiding during reflow. The IPC-7351B recommendation is:

- Total paste area = **40%** of exposed pad area
- Divided into an NxN grid of smaller rectangles
- Gaps between segments >= 0.25mm

This is built into every LandForge footprint with an exposed pad. You do not
need to modify the paste layer manually.

---

## 10. Thermal Pad Handling

### 10.1 Exposed Pad Connection

Components with exposed pads (QFN, SON, DPAK, etc.) need the exposed pad
connected to a copper area in the PCB for thermal and electrical performance.

**In KiCad:**
1. The exposed pad is labeled as the last pad number (or "EP")
2. Connect it to the appropriate net (usually GND or a dedicated thermal pad net)
3. The pad has the `heatsink` property set

### 10.2 Thermal Vias

LandForge footprints with exposed pads include the pad but not thermal vias by
default. Add thermal vias in the PCB layout:

1. Place vias within the exposed pad area
2. Typical via size: 0.3mm drill, 0.6mm annular ring
3. Typical via pattern: 3x3 or 4x4 grid
4. Connect vias to inner ground plane

Some footprints may include `_ThermalVias` variants with pre-placed vias.

---

## 11. BGA Considerations

### 11.1 NSMD vs SMD Pad Definition

LandForge BGA footprints use **NSMD** (Non-Solder-Mask-Defined) pads by default:
- The solder mask opening is larger than the copper pad
- The copper pad defines the solder joint size
- This gives more consistent solder joint geometry

### 11.2 Ball Grid Naming

BGA pads follow the standard JEDEC naming convention:
- Columns: A, B, C, ... (letters, skipping I and O to avoid confusion with 1 and 0)
- Rows: 1, 2, 3, ... (numbers)
- Pin A1 is at the top-left corner (marked by a dot on the package)

### 11.3 Collapsible vs Non-Collapsible

- **Collapsible balls** (most standard BGAs): land pad is SMALLER than ball
- **Non-collapsible bumps** (WLCSP, some FBGA): land pad is LARGER than bump

The footprint name indicates which: `C` for collapsible, `N` for non-collapsible.

---

## 12. Mixing with KiCad Stock Library

LandForge footprints can coexist with KiCad's stock library. You might use:

- **LandForge** for standard passive components and ICs (consistent density levels)
- **KiCad stock** for manufacturer-specific connectors, modules, and exotic packages

There is no conflict -- they are separate libraries. However, be aware:
- KiCad stock footprints are approximately Level B but without density level variants
- KiCad's "HandSolder" variants are NOT the same as LandForge Level A
  (HandSolder pads are informally enlarged; Level A is calculated per IPC equations)

---

## 13. Common Questions

### "Which footprint do I use for a generic 0805 resistor?"

`RESC2012X55N` (Level B) -- or `M`/`L` variant depending on your density choice.
The "2012" means 2.0 x 1.2 mm metric, which is the 0805 EIA size.

### "The footprint names are hard to read. Can I search by 0805?"

Yes. LandForge footprints include the EIA code in their tags. Search for `0805`
or `2012` in the footprint browser and you'll find them.

### "My component datasheet says QFN-32 but I find multiple QFN-32 footprints."

QFN-32 is not a complete specification. You need to match:
1. **Body size** (e.g., 5x5mm vs 4x4mm)
2. **Pitch** (e.g., 0.5mm vs 0.4mm)
3. **Exposed pad size** (e.g., 3.4mm vs 3.1mm)
4. **Height** (usually less critical for footprint selection)

All of these are encoded in the IPC name. Match your datasheet dimensions.

### "Can I use Level C for prototypes?"

You can, but Level A is better for prototypes because:
- Larger pads are easier to hand-solder and rework
- Wider courtyard gives more room for probing
- If you find a bug, desoldering Level A pads is much easier

Switch to Level B or C for production.

### "Do I need to change my DRC settings?"

Set your courtyard-to-courtyard clearance to 0mm. The LandForge courtyard already
includes the IPC-specified minimum clearance for the chosen density level.

### "What about components not in LandForge?"

LandForge covers standard JEDEC/IPC package types. For manufacturer-specific
packages (e.g., a particular Molex connector, or an Infineon DirectFET), use
KiCad's stock library or create custom footprints from the manufacturer's
datasheet.

### "Is Level B the same as KiCad's stock footprints?"

Very close, but not identical. KiCad's stock footprints are labeled "IPC-7351
nominal" which corresponds to Level B, but:
- LandForge uses a rigorous equation-based calculation
- KiCad stock uses the `kicad-footprint-generator` with its own interpretation
- Pad dimensions typically agree within ±10-15%
- The differences are small enough that both produce good solder joints
