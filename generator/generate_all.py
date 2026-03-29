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
    # B4: SOIC / SOP
    # B5: QFP
    # B6: SOJ / PLCC
    # B7: BGA / LGA
    # B8: QFN / SON / DFN
    # B9: LCC + Chip Arrays
    # B10: DIP
    # B11: WLCSP
    # B12: SC-70
    # B13: Crystal / Oscillator

    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"Total: {total} footprints in {elapsed:.2f} seconds")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
