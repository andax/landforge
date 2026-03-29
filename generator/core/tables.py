"""
IPC-7351B Tolerance Tables (Tables 3-2 through 3-22).

Each table defines solder fillet goals (J_T, J_H, J_S) for density levels A, B, C,
plus courtyard excess and round-off factor.

Source: IPC-7351B Section 3.1.5.1, pages 15-24.
"""

from .ipc_equations import ToleranceTable, FilletGoals, CourtyardExcess

# Table 3-2: Flat Ribbon L and Gull-Wing Leads (pitch > 0.625 mm)
# Applies to: SOIC, SOP (>0.625mm), QFP (>0.625mm), SOT, SOD
TABLE_3_2 = ToleranceTable(
    name="3-2",
    description="Flat ribbon L and gull-wing leads, pitch > 0.625 mm",
    fillet_A=FilletGoals(toe=0.55, heel=0.45, side=0.05),
    fillet_B=FilletGoals(toe=0.35, heel=0.35, side=0.03),
    fillet_C=FilletGoals(toe=0.15, heel=0.25, side=0.01),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-3: Flat Ribbon L and Gull-Wing Leads (pitch <= 0.625 mm)
# Applies to: SOP fine pitch, QFP fine pitch, SSOP, TSSOP, MSOP
TABLE_3_3 = ToleranceTable(
    name="3-3",
    description="Flat ribbon L and gull-wing leads, pitch <= 0.625 mm",
    fillet_A=FilletGoals(toe=0.55, heel=0.45, side=0.01),
    fillet_B=FilletGoals(toe=0.35, heel=0.35, side=-0.02),
    fillet_C=FilletGoals(toe=0.15, heel=0.25, side=-0.04),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-4: J Leads
# Applies to: PLCC, SOJ
# Note: For J-leads, heel is the OUTER dimension, toe is INNER
TABLE_3_4 = ToleranceTable(
    name="3-4",
    description="J leads (PLCC, SOJ)",
    fillet_A=FilletGoals(toe=0.55, heel=0.10, side=0.05),
    fillet_B=FilletGoals(toe=0.35, heel=0.00, side=0.03),
    fillet_C=FilletGoals(toe=0.15, heel=-0.10, side=0.01),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-5: Rectangular or Square-End Components >= 1608 (0603)
# Applies to: RESC, CAPC, INDC, DIOC (0603 and larger)
TABLE_3_5 = ToleranceTable(
    name="3-5",
    description="Rectangular/square-end chip components >= 1608 (0603)",
    fillet_A=FilletGoals(toe=0.55, heel=0.00, side=0.05),
    fillet_B=FilletGoals(toe=0.35, heel=0.00, side=0.00),
    fillet_C=FilletGoals(toe=0.15, heel=0.00, side=-0.05),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-6: Rectangular or Square-End Components < 1608 (0603)
# Applies to: RESC, CAPC, INDC, DIOC (0402, 0201, 01005)
TABLE_3_6 = ToleranceTable(
    name="3-6",
    description="Rectangular/square-end chip components < 1608 (0603)",
    fillet_A=FilletGoals(toe=0.30, heel=0.00, side=0.05),
    fillet_B=FilletGoals(toe=0.20, heel=0.00, side=0.00),
    fillet_C=FilletGoals(toe=0.10, heel=0.00, side=-0.05),
    courtyard=CourtyardExcess(A=0.20, B=0.15, C=0.10),
    roundoff=0.02,  # Finer rounding for small components
)

# Table 3-7: Cylindrical End Cap Terminations (MELF)
# Applies to: RESMELF, DIOMELF
TABLE_3_7 = ToleranceTable(
    name="3-7",
    description="Cylindrical end cap (MELF)",
    fillet_A=FilletGoals(toe=0.60, heel=0.20, side=0.10),
    fillet_B=FilletGoals(toe=0.40, heel=0.10, side=0.05),
    fillet_C=FilletGoals(toe=0.20, heel=0.02, side=0.01),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-8: Leadless Chip Carrier with Castellated Terminations
# Applies to: LCC, LCCS
TABLE_3_8 = ToleranceTable(
    name="3-8",
    description="Leadless chip carrier with castellated terminations (LCC)",
    fillet_A=FilletGoals(toe=0.65, heel=0.25, side=0.05),
    fillet_B=FilletGoals(toe=0.55, heel=0.15, side=-0.05),
    fillet_C=FilletGoals(toe=0.45, heel=0.05, side=-0.15),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-9: Concave Chip Array Component Lead Package
# Applies to: RESCAV, CAPCAV, INDCAV, OSCSC
TABLE_3_9 = ToleranceTable(
    name="3-9",
    description="Concave chip array",
    fillet_A=FilletGoals(toe=0.55, heel=-0.05, side=-0.05),
    fillet_B=FilletGoals(toe=0.45, heel=-0.07, side=-0.07),
    fillet_C=FilletGoals(toe=0.35, heel=-0.10, side=-0.10),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-10: Convex Chip Array Component Lead Package
# Applies to: RESCAXE, RESCAXS
TABLE_3_10 = ToleranceTable(
    name="3-10",
    description="Convex chip array",
    fillet_A=FilletGoals(toe=0.55, heel=-0.05, side=-0.05),
    fillet_B=FilletGoals(toe=0.45, heel=-0.07, side=-0.07),
    fillet_C=FilletGoals(toe=0.35, heel=-0.10, side=-0.10),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-11: Flat Chip Array Component Lead Package
# Applies to: RESCAF, CAPCAF, INDCAF
TABLE_3_11 = ToleranceTable(
    name="3-11",
    description="Flat chip array",
    fillet_A=FilletGoals(toe=0.55, heel=-0.05, side=-0.05),
    fillet_B=FilletGoals(toe=0.45, heel=-0.07, side=-0.07),
    fillet_C=FilletGoals(toe=0.35, heel=-0.10, side=-0.10),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-12: Butt Joints
# Applies to: DIP (butt-mounted)
TABLE_3_12 = ToleranceTable(
    name="3-12",
    description="Butt joints (DIP)",
    fillet_A=FilletGoals(toe=1.0, heel=1.0, side=0.3),
    fillet_B=FilletGoals(toe=0.8, heel=0.8, side=0.2),
    fillet_C=FilletGoals(toe=0.6, heel=0.6, side=0.1),
    courtyard=CourtyardExcess(A=1.50, B=0.80, C=0.20),
)

# Table 3-13: Inward Flat Ribbon L-Leads (Molded Inductors, Diodes, Polarized Caps)
# Applies to: CAPMP, INDM, DIOM, RESM, FUSM, LEDM
# Note: toe and heel are SWAPPED vs gull-wing: toe=inner(G), heel=outer(Z)
TABLE_3_13 = ToleranceTable(
    name="3-13",
    description="Inward flat ribbon L-leads (molded body)",
    fillet_A=FilletGoals(toe=0.25, heel=0.80, side=0.01),
    fillet_B=FilletGoals(toe=0.15, heel=0.50, side=-0.05),
    fillet_C=FilletGoals(toe=0.07, heel=0.20, side=-0.10),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-14: Flat Lug Leads
# Applies to: DPAK (TO-252), D2PAK (TO-263)
TABLE_3_14 = ToleranceTable(
    name="3-14",
    description="Flat lug leads (DPAK/D2PAK)",
    fillet_A=FilletGoals(toe=0.55, heel=0.45, side=0.05),
    fillet_B=FilletGoals(toe=0.35, heel=0.35, side=0.03),
    fillet_C=FilletGoals(toe=0.15, heel=0.25, side=0.01),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-15: Quad Flat No-Lead (QFN)
# Applies to: QFN
TABLE_3_15 = ToleranceTable(
    name="3-15",
    description="Quad flat no-lead (QFN)",
    fillet_A=FilletGoals(toe=0.40, heel=0.00, side=-0.04),
    fillet_B=FilletGoals(toe=0.30, heel=0.00, side=-0.04),
    fillet_C=FilletGoals(toe=0.20, heel=0.00, side=-0.04),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-16: Small Outline No-Lead (SON)
# Applies to: SON
TABLE_3_16 = ToleranceTable(
    name="3-16",
    description="Small outline no-lead (SON)",
    fillet_A=FilletGoals(toe=0.40, heel=0.00, side=-0.04),
    fillet_B=FilletGoals(toe=0.30, heel=0.00, side=-0.04),
    fillet_C=FilletGoals(toe=0.20, heel=0.00, side=-0.04),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-17: Ball Grid Array
# Note: BGA uses a different calculation method (periphery-based).
# The fillet fields are not used directly; see calculate_bga_land_diameter().
# Courtyard excess is significantly larger for BGA.
TABLE_3_17 = ToleranceTable(
    name="3-17",
    description="Ball grid array (BGA)",
    fillet_A=FilletGoals(toe=0.0, heel=0.0, side=0.0),  # Not used for BGA
    fillet_B=FilletGoals(toe=0.0, heel=0.0, side=0.0),
    fillet_C=FilletGoals(toe=0.0, heel=0.0, side=0.0),
    courtyard=CourtyardExcess(A=2.00, B=1.00, C=0.50),
)

# Table 3-18: Small Outline and Quad Flat No-Lead with Pullback Leads
# Applies to: PSON, PQFN, DFN
# Uses periphery-based calculation: toe field holds the periphery value.
TABLE_3_18 = ToleranceTable(
    name="3-18",
    description="Pullback no-lead (PQFN, PSON, DFN)",
    fillet_A=FilletGoals(toe=0.05, heel=0.0, side=0.0),
    fillet_B=FilletGoals(toe=0.00, heel=0.0, side=0.0),
    fillet_C=FilletGoals(toe=-0.05, heel=0.0, side=0.0),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-19: Corner Concave Component Oscillator Lead Package
# Applies to: OSCCC
TABLE_3_19 = ToleranceTable(
    name="3-19",
    description="Corner concave oscillator (OSCCC)",
    fillet_A=FilletGoals(toe=0.35, heel=0.10, side=0.0),
    fillet_B=FilletGoals(toe=0.25, heel=0.00, side=0.0),
    fillet_C=FilletGoals(toe=0.15, heel=-0.05, side=0.0),
    courtyard=CourtyardExcess(A=0.50, B=0.25, C=0.10),
)

# Table 3-20: Aluminium Electrolytic Capacitor and 2-pin Crystal
# Applies to: CAPAE
# Note: For CAPAE >= 10mm diameter, toe increases to 1.00/0.70/0.40
TABLE_3_20 = ToleranceTable(
    name="3-20",
    description="Aluminum electrolytic capacitor (CAPAE)",
    fillet_A=FilletGoals(toe=0.70, heel=0.00, side=0.50),
    fillet_B=FilletGoals(toe=0.50, heel=-0.10, side=0.40),
    fillet_C=FilletGoals(toe=0.30, heel=-0.20, side=0.30),
    courtyard=CourtyardExcess(A=1.00, B=0.50, C=0.25),
)

# Table 3-20 variant for large electrolytics (>= 10mm diameter)
TABLE_3_20_LARGE = ToleranceTable(
    name="3-20L",
    description="Aluminum electrolytic capacitor >= 10mm (CAPAE)",
    fillet_A=FilletGoals(toe=1.00, heel=0.00, side=0.50),
    fillet_B=FilletGoals(toe=0.70, heel=-0.10, side=0.40),
    fillet_C=FilletGoals(toe=0.40, heel=-0.20, side=0.30),
    courtyard=CourtyardExcess(A=1.00, B=0.50, C=0.25),
)

# Table 3-21: Column and Land Grid Array
# Applies to: CGA, LGA
# Note: Only Level B is defined in the standard
TABLE_3_21 = ToleranceTable(
    name="3-21",
    description="Column and land grid array (CGA, LGA)",
    fillet_A=FilletGoals(toe=0.0, heel=0.0, side=0.0),
    fillet_B=FilletGoals(toe=0.0, heel=0.0, side=0.0),
    fillet_C=FilletGoals(toe=0.0, heel=0.0, side=0.0),
    courtyard=CourtyardExcess(A=1.00, B=1.00, C=1.00),
)

# Table 3-22: Small Outline Components, Flat Lead
# Applies to: SODFL, SOTFL
TABLE_3_22 = ToleranceTable(
    name="3-22",
    description="Small outline flat lead (SODFL, SOTFL)",
    fillet_A=FilletGoals(toe=0.30, heel=0.00, side=0.05),
    fillet_B=FilletGoals(toe=0.20, heel=0.00, side=0.00),
    fillet_C=FilletGoals(toe=0.10, heel=0.00, side=-0.05),
    courtyard=CourtyardExcess(A=0.20, B=0.15, C=0.10),
    roundoff=0.02,  # Same fine rounding as small chip components
)


# Lookup by table number
TABLES = {
    "3-2": TABLE_3_2,
    "3-3": TABLE_3_3,
    "3-4": TABLE_3_4,
    "3-5": TABLE_3_5,
    "3-6": TABLE_3_6,
    "3-7": TABLE_3_7,
    "3-8": TABLE_3_8,
    "3-9": TABLE_3_9,
    "3-10": TABLE_3_10,
    "3-11": TABLE_3_11,
    "3-12": TABLE_3_12,
    "3-13": TABLE_3_13,
    "3-14": TABLE_3_14,
    "3-15": TABLE_3_15,
    "3-16": TABLE_3_16,
    "3-17": TABLE_3_17,
    "3-18": TABLE_3_18,
    "3-19": TABLE_3_19,
    "3-20": TABLE_3_20,
    "3-20L": TABLE_3_20_LARGE,
    "3-21": TABLE_3_21,
    "3-22": TABLE_3_22,
}
