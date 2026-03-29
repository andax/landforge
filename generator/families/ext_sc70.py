"""
Extended: SC-70 Family (SOT-323 through SOT-1123) Generator.

These are JEDEC-registered small SOT variants not explicitly covered by
IPC-7351B but using the same Table 3-2 gull-wing equations.

Reuses the SOT generator with SC-70 family dimensions.
"""

from __future__ import annotations

from generator.families.ipc7352_sot import (
    SotSpec, generate_sot_footprint, load_sot_database, generate_sot_library,
)

# Re-export the generation function -- SC-70 packages use the exact same
# generator as SOT, just with different body dimensions in the CSV.
generate_sc70_library = generate_sot_library
