#!/usr/bin/env python3
"""
LandForge master generation script.

Generates all footprint libraries from component databases.
Run with: uv run python3 -m generator.generate_all
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Project root
ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
OUTPUT = ROOT / "output"


def generate_chip_library() -> int:
    """Generate IPC7351B_Chip.pretty from chip_components.csv."""
    from generator.families.ipc7352_chip import generate_chip_library

    csv_path = str(DATA / "jedec" / "chip_components.csv")
    out_dir = str(OUTPUT / "IPC7351B_Chip.pretty")
    return generate_chip_library(csv_path, out_dir)


def main():
    print("=" * 60)
    print("LandForge — IPC-7351B KiCad Library Generator")
    print("=" * 60)

    total = 0
    t0 = time.time()

    # B1: Chip passives
    print("\n[B1] Chip passives (RESC, CAPC, CAPCP, INDC, DIOC)...")
    n = generate_chip_library()
    print(f"     Generated {n} footprints")
    total += n

    # B2: Molded body + MELF + Electrolytic
    print("\n[B2] Molded body (CAPMP, DIOM, INDM, RESM, FUSM, LEDM)...")
    from generator.families.ipc7352_molded import generate_molded_library
    n = generate_molded_library(
        str(DATA / "jedec" / "molded_components.csv"),
        str(OUTPUT / "IPC7351B_Molded.pretty"),
    )
    print(f"     Generated {n} footprints")
    total += n

    print("\n[B2] MELF (RESMELF, DIOMELF)...")
    from generator.families.ipc7352_melf import generate_melf_library
    n = generate_melf_library(
        str(DATA / "jedec" / "melf_components.csv"),
        str(OUTPUT / "IPC7351B_MELF.pretty"),
    )
    print(f"     Generated {n} footprints")
    total += n

    print("\n[B2] Electrolytic (CAPAE)...")
    from generator.families.ipc7352_capae import generate_capae_library
    n = generate_capae_library(
        str(DATA / "jedec" / "electrolytic_components.csv"),
        str(OUTPUT / "IPC7351B_Electrolytic.pretty"),
    )
    print(f"     Generated {n} footprints")
    total += n

    # B3: SOT / SOD / DPAK
    print("\n[B3] SOT / SOD / DPAK...")
    from generator.families.ipc7352_sot import generate_sot_library
    n = generate_sot_library(
        str(DATA / "jedec" / "sot_components.csv"),
        str(OUTPUT / "IPC7351B_SOT.pretty"),
    )
    print(f"     Generated {n} footprints")
    total += n
    # B4-B5: SOIC / SOP / SSOP / TSSOP / MSOP / QFP
    print("\n[B4-B5] Gull-wing ICs (SOIC/SSOP/TSSOP/MSOP/QFP)...")
    from generator.families.ipc7353_soic import generate_gullwing_library
    n = generate_gullwing_library(
        str(DATA / "jedec" / "gullwing_ic.csv"),
        str(OUTPUT / "IPC7351B_SOIC.pretty"),
    )
    print(f"     Generated {n} footprints")
    total += n
    # B7: BGA / LGA
    print("\n[B7] BGA / FBGA...")
    from generator.families.ipc7358_bga import generate_bga_library
    n = generate_bga_library(
        str(DATA / "jedec" / "bga_components.csv"),
        str(OUTPUT / "IPC7351B_BGA.pretty"),
    )
    print(f"     Generated {n} footprints")
    total += n

    # B8: QFN / SON / DFN
    print("\n[B8] QFN / SON / DFN...")
    from generator.families.ipc7359_qfn import generate_nolead_library
    n = generate_nolead_library(
        str(DATA / "jedec" / "qfn_components.csv"),
        str(OUTPUT / "IPC7351B_QFN.pretty"),
    )
    print(f"     Generated {n} footprints")
    total += n

    # B10: DIP
    print("\n[B10] DIP (through-hole)...")
    from generator.families.ipc7357_dip import generate_dip_library
    n = generate_dip_library(
        str(DATA / "jedec" / "dip_components.csv"),
        str(OUTPUT / "IPC7351B_DIP.pretty"),
    )
    print(f"     Generated {n} footprints")
    total += n

    # B11: WLCSP
    print("\n[B11] WLCSP (Wafer-Level CSP)...")
    from generator.families.ext_wlcsp import generate_wlcsp_library
    n = generate_wlcsp_library(
        str(DATA / "jedec" / "wlcsp_components.csv"),
        str(OUTPUT / "LandForge_WLCSP.pretty"),
    )
    print(f"     Generated {n} footprints")
    total += n

    # B12: SC-70 family
    print("\n[B12] SC-70 family (SOT-323 through SOT-963)...")
    from generator.families.ext_sc70 import generate_sc70_library
    n = generate_sc70_library(
        str(DATA / "jedec" / "sc70_components.csv"),
        str(OUTPUT / "LandForge_SC70.pretty"),
    )
    print(f"     Generated {n} footprints")
    total += n

    # B13: SMD Crystal / Oscillator
    print("\n[B13] SMD Crystal / Oscillator...")
    from generator.families.ext_crystal import generate_crystal_library
    n = generate_crystal_library(
        str(DATA / "jedec" / "crystal_components.csv"),
        str(OUTPUT / "LandForge_Crystal.pretty"),
    )
    print(f"     Generated {n} footprints")
    total += n

    # Deferred: B6 (SOJ/PLCC), B9 (LCC) -- low priority legacy packages

    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"Total: {total} footprints in {elapsed:.2f} seconds")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
