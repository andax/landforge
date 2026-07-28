# Stock Comparison Report

Automated comparison of LandForge Level B (Nominal) footprints against the KiCad stock libraries.

**IPC-7351B is the source of truth for this project.** KiCad stock footprints are hand-maintained, partly vendor-derived, and use coarser rounding, so differences are expected. REVIEW means a human should look, not that the footprint is wrong. FAIL means gross disagreement that most likely indicates a generator or CSV data bug.

- Stock libraries: `/home/andreas/Applications/kicad-10/share/kicad/footprints`
- Regenerate: `uv run python -m generator.stock_compare`
- Pairs compared: 167 (81 OK, 86 REVIEW, 0 FAIL)

Thresholds: pad center REVIEW > 0.15mm / FAIL > 0.5mm; pad size REVIEW > 20% / FAIL > 35%; courtyard REVIEW > 1.0mm. Positions are compared after centroid alignment of the shared pads. 'loose' mappings (stock part is only an analog) are capped at REVIEW.

## BGA (2 OK, 2 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| BGA100C080P10X10_900X900X120N | BGA-64_9.0x9.0mm_Layout10x10_P0.8mm | 64/100/64 | 0.02mm | 36% | REVIEW | stock perimeter-only variant uses ball-sized 0.5 pads (vendor NSMD); IPC Table 3-17/14-5 gives 0.30-0.35 for a 0.40 ball; pad A1 size dev 36% (0.32x0.32 vs 0.5x0.5) |
| BGA100C100P10X10_1200X1200X185N | BGA-100_11.0x11.0mm_Layout10x10_P1.0mm_Ball0.5mm_Pad0.4mm_NSMD | 100 | 0.00mm | 0% | OK | body 12 vs 11 mm; same ball grid |
| BGA144C100P12X12_1500X1500X185N | BGA-144_13.0x13.0mm_Layout12x12_P1.0mm | 144 | 0.00mm | 20% | REVIEW | body 15 vs 13 mm; same ball grid; courtyard differs +2.00x+2.00mm |
| BGA256C100P16X16_1700X1700X185N | BGA-256_17.0x17.0mm_Layout16x16_P1.0mm_Ball0.5mm_Pad0.4mm_NSMD | 256 | 0.00mm | 0% | OK | JEDEC ball rows A-T skipping I O Q S |

## CAPAE (1 OK, 12 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| CAPAE300X540N | CP_Elec_3x5.4 | 2 | 0.23mm | 6% | REVIEW | pad 1 center off by 0.23mm |
| CAPAE400X540N | CP_Elec_4x5.4 | 2 | 0.23mm | 6% | REVIEW | pad 1 center off by 0.23mm |
| CAPAE500X540N | CP_Elec_5x5.4 | 2 | 0.28mm | 7% | REVIEW | pad 1 center off by 0.28mm |
| CAPAE500X580N | CP_Elec_5x5.8 | 2 | 0.28mm | 7% | REVIEW | pad 1 center off by 0.28mm |
| CAPAE630X540N | CP_Elec_6.3x5.4 | 2 | 0.38mm | 11% | REVIEW | pad 1 center off by 0.38mm |
| CAPAE630X580N | CP_Elec_6.3x5.8 | 2 | 0.28mm | 11% | REVIEW | pad 1 center off by 0.28mm |
| CAPAE630X770N | CP_Elec_6.3x7.7 | 2 | 0.28mm | 11% | REVIEW | pad 1 center off by 0.28mm |
| CAPAE800X540N | CP_Elec_8x5.4 | 2 | 0.20mm | 22% | REVIEW | pad 1 center off by 0.20mm; pad 1 size dev 22% (3.95x1.95 vs 4.0x2.5) |
| CAPAE800X620N | CP_Elec_8x6.2 | 2 | 0.20mm | 22% | REVIEW | pad 1 center off by 0.20mm; pad 1 size dev 22% (3.95x1.95 vs 4.0x2.5) |
| CAPAE800X1020N | CP_Elec_8x10 | 2 | 0.40mm | 22% | REVIEW | height 10.2 vs 10.0; pad 1 center off by 0.40mm; pad 1 size dev 22% (3.95x1.95 vs 3.5x2.5) |
| CAPAE1000X1020N | CP_Elec_10x10 | 2 | 0.10mm | 6% | OK | height 10.2 vs 10.0 |
| CAPAE1000X1250N | CP_Elec_10x12.5 | 2 | 0.30mm | 6% | REVIEW | pad 1 center off by 0.30mm |
| CAPAE1600X1650N | CP_Elec_16x17.5 | 2 | 0.22mm | 71% | REVIEW | height 16.5 vs 17.5; pad 1 center off by 0.22mm; pad 1 size dev 71% (5.1x2.75 vs 7.8x9.6); courtyard differs -1.70x-0.10mm |

## CHIP (33 OK, 7 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| RESC0402X013N | R_01005_0402Metric | 2 | 0.00mm | 7% | OK |  |
| RESC0603X023N | R_0201_0603Metric | 2 | 0.01mm | 0% | OK |  |
| RESC1005X035N | R_0402_1005Metric | 2 | 0.05mm | 13% | OK |  |
| RESC1608X055N | R_0603_1608Metric | 2 | 0.01mm | 3% | OK |  |
| RESC2012X065N | R_0805_2012Metric | 2 | 0.05mm | 7% | OK |  |
| RESC3216X065N | R_1206_3216Metric | 2 | 0.08mm | 6% | OK |  |
| RESC3225X065N | R_1210_3225Metric | 2 | 0.08mm | 4% | OK |  |
| RESC3246X065N | R_1218_3246Metric | 2 | 0.06mm | 2% | OK |  |
| RESC4532X065N | R_1812_4532Metric | 2 | 0.05mm | 4% | OK |  |
| RESC5025X065N | R_2010_5025Metric | 2 | 0.12mm | 12% | OK |  |
| RESC6332X065N | R_2512_6332Metric | 2 | 0.12mm | 12% | OK |  |
| RESC1220X055N | R_0508_1220Metric | 2 | 0.01mm | 27% | REVIEW | pad 1 size dev 27% (0.69x2.22 vs 0.95x2.15) |
| RESC1632X055N | R_0612_1632Metric | 2 | 0.06mm | 7% | OK |  |
| RESC2038X065N | R_0815_2038Metric | 2 | 0.03mm | 0% | OK |  |
| RESC2550X065N | R_1020_2550Metric | 2 | 0.09mm | 11% | OK |  |
| RESC3264X065N | R_1225_3264Metric | 2 | 0.21mm | 17% | REVIEW | pad 1 center off by 0.21mm |
| CAPC0402X013N | C_01005_0402Metric | 2 | 0.00mm | 7% | OK |  |
| CAPC0603X023N | C_0201_0603Metric | 2 | 0.01mm | 0% | OK |  |
| CAPC1005X050N | C_0402_1005Metric | 2 | 0.02mm | 9% | OK |  |
| CAPC1608X080N | C_0603_1608Metric | 2 | 0.04mm | 8% | OK |  |
| CAPC2012X125N | C_0805_2012Metric | 2 | 0.01mm | 3% | OK |  |
| CAPC3216X160N | C_1206_3216Metric | 2 | 0.06mm | 7% | OK |  |
| CAPC3225X250N | C_1210_3225Metric | 2 | 0.06mm | 7% | OK |  |
| CAPC4520X200N | C_1808_4520Metric | 2 | 0.11mm | 31% | REVIEW | pad 1 size dev 31% (1.075x2.25 vs 1.55x2.3) |
| CAPC4532X250N | C_1812_4532Metric | 2 | 0.14mm | 23% | REVIEW | pad 1 size dev 23% (1.075x3.45 vs 1.4x3.4) |
| CAPC4564X250N | C_1825_4564Metric | 2 | 0.14mm | 23% | REVIEW | pad 1 size dev 23% (1.075x6.65 vs 1.4x6.8) |
| CAPC5750X250N | C_2220_5750Metric | 2 | 0.05mm | 19% | OK | 2220 terminal length 0.50-1.00 per vendor datasheets |
| CAPC5664X250N | C_2225_5664Metric | 2 | 0.20mm | 34% | REVIEW | pad 1 center off by 0.20mm; pad 1 size dev 34% (1.075x6.65 vs 1.625x6.6) |
| INDC0402X013N | L_01005_0402Metric | 2 | 0.00mm | 7% | OK |  |
| INDC0603X023N | L_0201_0603Metric | 2 | 0.01mm | 0% | OK |  |
| INDC1005X050N | L_0402_1005Metric | 2 | 0.03mm | 3% | OK |  |
| INDC1608X080N | L_0603_1608Metric | 2 | 0.03mm | 6% | OK |  |
| INDC2012X125N | L_0805_2012Metric | 2 | 0.10mm | 25% | REVIEW | pad 1 size dev 25% (1.025x1.5 vs 0.875x1.2) |
| INDC3216X160N | L_1206_3216Metric | 2 | 0.04mm | 3% | OK |  |
| INDC3225X250N | L_1210_3225Metric | 2 | 0.14mm | 14% | OK |  |
| INDC4532X250N | L_1812_4532Metric | 2 | 0.05mm | 4% | OK |  |
| DIOC1005X035N | D_0402_1005Metric | 2 | 0.03mm | 3% | OK |  |
| DIOC1608X055N | D_0603_1608Metric | 2 | 0.03mm | 6% | OK |  |
| DIOC2012X065N | D_0805_2012Metric | 2 | 0.03mm | 7% | OK |  |
| DIOC3216X065N | D_1206_3216Metric | 2 | 0.14mm | 14% | OK |  |

## CRYSTAL (0 OK, 9 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| XTAL200X120X060-2N | Crystal_SMD_2012-2Pin_2.0x1.2mm | 2 | 0.31mm | 54% | REVIEW | stock crystal patterns are vendor-derived; pad 1 center off by 0.31mm; pad 1 size dev 54% (0.925x1.25 vs 0.6x1.1) |
| XTAL320X150X080-2N | Crystal_SMD_3215-2Pin_3.2x1.5mm | 2 | 0.32mm | 14% | REVIEW | non-polar 2-pin; stock numbers left pad 2; vendor-derived pattern; pad 1 center off by 0.32mm |
| XTAL500X320X100-2N | Crystal_SMD_5032-2Pin_5.0x3.2mm | 2 | 0.59mm | 46% | REVIEW | stock crystal patterns are vendor-derived; pad 1 center off by 0.59mm; pad 1 size dev 46% (1.075x3.25 vs 2.0x2.4) |
| XTAL700X500X150-2N | Crystal_SMD_7050-2Pin_7.0x5.0mm | 2 | 0.74mm | 68% | REVIEW | stock crystal patterns are vendor-derived; pad 1 center off by 0.74mm; pad 1 size dev 68% (1.275x5.05 vs 2.8x3.0) |
| OSCL200X160X060-4N | Crystal_SMD_2016-4Pin_2.0x1.6mm | 4 | 0.32mm | 6% | REVIEW | vendor-derived stock pattern; numbering now matches (pin 1 bottom-left CCW); pad 1 center off by 0.32mm |
| OSCL250X200X070-4N | Crystal_SMD_2520-4Pin_2.5x2.0mm | 4 | 0.36mm | 15% | REVIEW | vendor-derived stock pattern; numbering now matches (pin 1 bottom-left CCW); pad 1 center off by 0.36mm |
| OSCL320X250X090-4N | Crystal_SMD_3225-4Pin_3.2x2.5mm | 4 | 0.48mm | 29% | REVIEW | vendor-derived stock pattern; numbering now matches (pin 1 bottom-left CCW); pad 1 center off by 0.48mm; pad 1 size dev 29% (1.0x1.05 vs 1.4x1.2) |
| OSCL500X320X100-4N | Crystal_SMD_5032-4Pin_5.0x3.2mm | 4 | 0.79mm | 33% | REVIEW | vendor-derived stock pattern; numbering now matches (pin 1 bottom-left CCW); pad 1 center off by 0.79mm; pad 1 size dev 33% (1.075x1.45 vs 1.6x1.3) |
| OSCL700X500X150-4N | Crystal_SMD_7050-4Pin_7.0x5.0mm | 4 | 0.59mm | 39% | REVIEW | vendor-derived stock pattern; numbering now matches (pin 1 bottom-left CCW); pad 1 center off by 0.59mm; pad 1 size dev 39% (1.275x1.85 vs 2.1x1.7) |

## DFN (0 OK, 3 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| DFN050P300X300X090-8T240N | DFN-8-1EP_3x3mm_P0.5mm_EP1.7x2.4mm | 9 | 0.12mm | 75% | REVIEW | stock is vendor app-note pattern; verify lead lands against Table 3-15; pad 1 size dev 75% (0.575x0.35 vs 0.825x0.2) |
| DFN050P300X300X090-10T240N | DFN-10-1EP_3x3mm_P0.5mm_EP1.65x2.38mm | 11 | 0.11mm | 40% | REVIEW | stock is vendor app-note pattern; verify lead lands against Table 3-15; pad 1 size dev 40% (0.575x0.35 vs 0.85x0.25) |
| DFN065P200X200X090-6T120N | DFN-6-1EP_2x2mm_P0.65mm_EP1x1.6mm | 7 | 0.21mm | 40% | REVIEW | EP 0.6x1.2 vs 1x1.6; vendor EPs vary; pad 1 center off by 0.21mm; pad 7 size dev 40% (0.6x1.2 vs 1.0x1.6) |

## DIP (4 OK, 7 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| DIP762W330P254-8N | DIP-8_W7.62mm | 8 | 0.00mm | 0% | OK |  |
| DIP762W330P254-14N | DIP-14_W7.62mm | 14 | 0.00mm | 0% | REVIEW | courtyard differs +0.07x+1.50mm |
| DIP762W330P254-16N | DIP-16_W7.62mm | 16 | 0.00mm | 0% | OK |  |
| DIP762W330P254-18N | DIP-18_W7.62mm | 18 | 0.00mm | 0% | OK |  |
| DIP762W330P254-20N | DIP-20_W7.62mm | 20 | 0.00mm | 0% | OK |  |
| DIP1524W457P254-24N | DIP-24_W15.24mm | 24 | 0.00mm | 0% | REVIEW | courtyard differs +0.06x+1.02mm |
| DIP1524W457P254-28N | DIP-28_W15.24mm | 28 | 0.00mm | 0% | REVIEW | courtyard differs +0.06x+1.02mm |
| DIP1524W457P254-32N | DIP-32_W15.24mm | 32 | 0.00mm | 0% | REVIEW | courtyard differs +0.06x+1.04mm |
| DIP1524W457P254-40N | DIP-40_W15.24mm | 40 | 0.00mm | 0% | REVIEW | courtyard differs +0.06x+1.29mm |
| DIP1524W457P254-48N | DIP-48_W15.24mm | 48 | 0.00mm | 0% | REVIEW | courtyard differs +0.06x+1.33mm |
| DIP1524W457P254-64N | DIP-64_W15.24mm | 64 | 0.00mm | 0% | REVIEW | courtyard differs +0.06x+1.32mm |

## MELF (2 OK, 4 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| RESMELF220X110N | R_MicroMELF_MMU-0102 | 2 | 0.09mm | 17% | OK |  |
| RESMELF360X140N | R_MiniMELF_MMA-0204 | 2 | 0.19mm | 15% | REVIEW | pad 1 center off by 0.19mm |
| RESMELF580X220N | R_MELF_MMB-0207 | 2 | 0.26mm | 32% | REVIEW | pad 1 center off by 0.26mm; pad 1 size dev 32% (1.425x2.55 vs 2.1x2.6) |
| DIOMELF220X110N | D_MicroMELF | 2 | 0.24mm | 47% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; pad 1 center off by 0.24mm; pad 1 size dev 47% (1.175x1.25 vs 0.8x1.2) |
| DIOMELF360X140N | D_MiniMELF | 2 | 0.06mm | 3% | OK |  |
| DIOMELF580X220N | D_MELF | 2 | 0.31mm | 6% | REVIEW | pad 1 center off by 0.31mm |

## MOLDED (4 OK, 9 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| CAPMP2012X120N | CP_EIA-2012-12_Kemet-R | 2 | 0.05mm | 21% | REVIEW | pad 1 size dev 21% (1.375x1.05 vs 1.14x1.09) |
| CAPMP3216X180N | CP_EIA-3216-18_Kemet-A | 2 | 0.03mm | 18% | OK |  |
| CAPMP3528X210N | CP_EIA-3528-21_Kemet-B | 2 | 0.00mm | 25% | REVIEW | pad 1 size dev 25% (1.675x2.25 vs 1.34x2.39) |
| CAPMP6032X280N | CP_EIA-6032-28_Kemet-C | 2 | 0.28mm | 15% | REVIEW | pad 1 center off by 0.28mm |
| CAPMP7343X310N | CP_EIA-7343-31_Kemet-D | 2 | 0.24mm | 12% | REVIEW | EIA-7343 terminal width 2.3-2.5 (Kemet D); pad 1 center off by 0.24mm |
| CAPMP7343X430N | CP_EIA-7343-43_Kemet-X | 2 | 0.24mm | 12% | REVIEW | EIA-7343 terminal width 2.3-2.5 (Kemet X); pad 1 center off by 0.24mm |
| DIOM4336X245N | D_SMB | 2 | 0.04mm | 9% | OK | JEDEC DO-214AA (SMB); stock is vendor pattern |
| DIOM4326X230N | D_SMA | 2 | 0.08mm | 14% | OK | JEDEC DO-214AC (SMA); stock is vendor pattern |
| DIOM6959X260N | D_SMC | 2 | 0.14mm | 11% | OK | JEDEC DO-214AB (SMC); stock is vendor pattern |
| LEDM2012X080N | LED_0805_2012Metric | 2 | 0.00mm | 41% | REVIEW | stock LED pattern is vendor-derived, differs from molded table; pad 1 size dev 41% (1.375x1.2 vs 0.975x1.4) |
| LEDM3216X110N | LED_1206_3216Metric | 2 | 0.04mm | 26% | REVIEW | stock LED pattern is vendor-derived, differs from molded table; pad 1 size dev 26% (1.575x1.55 vs 1.25x1.75) |
| FUSM1608X080N | Fuse_0603_1608Metric | 2 | 0.03mm | 40% | REVIEW | stock fuse pattern derived from chip table; ours uses molded table; pad 1 size dev 40% (1.225x0.75 vs 0.875x0.95) |
| FUSM3216X160N | Fuse_1206_3216Metric | 2 | 0.04mm | 26% | REVIEW | stock fuse pattern derived from chip table; ours uses molded table; pad 1 size dev 26% (1.575x1.55 vs 1.25x1.75) |

## MSOP (2 OK, 2 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| MSOP065P490X110-8N | MSOP-8_3x3mm_P0.65mm | 8 | 0.00mm | 25% | REVIEW | pad 1 size dev 25% (1.625x0.5 vs 1.625x0.4) |
| MSOP065P490X110-12N | MSOP-12_3x4.039mm_P0.65mm | 12 | 0.04mm | 25% | REVIEW | pad 1 size dev 25% (1.625x0.5 vs 1.45x0.4) |
| MSOP050P490X110-10N | MSOP-10_3x3mm_P0.5mm | 10 | 0.01mm | 14% | OK |  |
| MSOP050P490X110-16N | MSOP-16_3x4.039mm_P0.5mm | 16 | 0.04mm | 12% | OK |  |

## QFN (7 OK, 0 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| QFN050P300X300X090-16T150N | QFN-16-1EP_3x3mm_P0.5mm_EP1.45x1.45mm | 17 | 0.05mm | 3% | OK | EP 1.50 vs 1.45 |
| QFN050P400X400X090-20T250N | QFN-20-1EP_4x4mm_P0.5mm_EP2.5x2.5mm | 21 | 0.05mm | 6% | OK |  |
| QFN050P400X400X090-24T250N | QFN-24-1EP_4x4mm_P0.5mm_EP2.5x2.5mm | 25 | 0.04mm | 9% | OK |  |
| QFN050P500X500X090-32T340N | QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm | 33 | 0.05mm | 1% | OK | EP 3.40 vs 3.45 |
| QFN040P500X500X090-40T340N | QFN-40-1EP_5x5mm_P0.4mm_EP3.6x3.6mm | 41 | 0.05mm | 20% | OK | EP 3.40 vs 3.60 |
| QFN050P700X700X090-48T510N | QFN-48-1EP_7x7mm_P0.5mm_EP5.1x5.1mm | 49 | 0.04mm | 9% | OK |  |
| QFN050P900X900X090-64T710N | QFN-64-1EP_9x9mm_P0.5mm_EP7.15x7.15mm | 65 | 0.05mm | 1% | OK | EP 7.10 vs 7.15 |

## QFP (8 OK, 4 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| QFP050P900X900X120-48N | LQFP-48_7x7mm_P0.5mm | 48 | 0.10mm | 10% | OK |  |
| QFP050P1200X1200X120-64N | LQFP-64_10x10mm_P0.5mm | 64 | 0.09mm | 5% | OK |  |
| QFP050P1600X1600X120-100N | LQFP-100_14x14mm_P0.5mm | 100 | 0.09mm | 2% | OK |  |
| QFP050P2200X2200X120-144N | LQFP-144_20x20mm_P0.5mm | 144 | 0.10mm | 10% | OK |  |
| QFP050P2600X2600X120-176N | LQFP-176_24x24mm_P0.5mm | 176 | 0.09mm | 8% | OK |  |
| QFP050P3000X3000X120-208N | LQFP-208_28x28mm_P0.5mm | 208 | 0.09mm | 8% | OK |  |
| QFP065P1200X1200X120-52N | LQFP-52_10x10mm_P0.65mm | 52 | 0.10mm | 25% | REVIEW | pad 1 size dev 25% (1.625x0.5 vs 1.475x0.4) |
| QFP080P900X900X120-32N | LQFP-32_7x7mm_P0.8mm | 32 | 0.01mm | 18% | OK |  |
| QFP080P1200X1200X120-44N | LQFP-44_10x10mm_P0.8mm | 44 | 0.03mm | 20% | REVIEW | pad 1 size dev 20% (1.775x0.55 vs 1.475x0.55) |
| QFP040P3000X3000X120-256N | PQFP-256_28x28mm_P0.4mm | 256 | 0.19mm | 52% | REVIEW | PQFP lead geometry differs from generic QFP; pad 1 center off by 0.19mm; pad 1 size dev 52% (1.525x0.25 vs 1.0x0.26) |
| QFP065P1600X1600X120-80N | TQFP-80_14x14mm_P0.65mm | 80 | 0.03mm | 25% | REVIEW | JEDEC MS-026, 14x14 P0.65; pad 1 size dev 25% (1.575x0.5 vs 1.475x0.4) |
| QFP040P1600X1600X120-128N | LQFP-128_14x14mm_P0.4mm | 128 | 0.03mm | 7% | OK | JEDEC MS-026, 14x14 P0.4 |

## SC70 (0 OK, 13 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| SOT065P220X110-3N | SOT-323_SC-70 | 3 | 0.17mm | 32% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; pad 3 center off by 0.17mm; pad 1 size dev 32% (1.225x0.5 vs 0.925x0.45) |
| SOT065P220X110-4N | SOT-343_SC-70-4 | 4 | 0.19mm | 17% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; pad 1 center off by 0.19mm |
| SOT065P220X110-5N | SOT-353_SC-70-5 | 5 | 0.21mm | 43% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; pad 4 center off by 0.21mm; pad 1 size dev 43% (1.225x0.5 vs 1.025x0.35) |
| SOT065P220X110-6N | SOT-363_SC-70-6 | 6 | 0.17mm | 43% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; pad 1 center off by 0.17mm; pad 1 size dev 43% (1.225x0.5 vs 1.025x0.35) |
| SOT050P160X060-3N | SOT-523 | 3 | 0.14mm | 125% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; consider Level C for micro packages; pad 1 size dev 125% (1.15x0.4 vs 0.51x0.4) |
| SOT050P160X060-5N | SOT-553 | 5 | 0.05mm | 70% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; consider Level C for micro packages; pad 1 size dev 70% (1.15x0.4 vs 0.675x0.35) |
| SOT050P160X060-6N | SOT-563 | 6 | 0.04mm | 70% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; consider Level C for micro packages; pad 1 size dev 70% (1.15x0.4 vs 0.675x0.35) |
| SOT050P180X055-5N | SOT-665 | 5 | 0.06mm | 130% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; consider Level C for micro packages; pad 1 size dev 130% (1.15x0.4 vs 0.5x0.38) |
| SOT050P180X055-6N | SOT-666 | 6 | 0.08mm | 130% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; consider Level C for micro packages; pad 1 size dev 130% (1.15x0.4 vs 0.5x0.375) |
| SOT040P140X050-3N | SOT-723 | 3 | 0.13mm | 144% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; consider Level C for micro packages; pad 1 size dev 144% (1.1x0.35 vs 0.45x0.4); courtyard differs +1.20x-0.10mm |
| SOT035P100X050-3N | SOT-883 | 3 | 0.18mm | 81% | REVIEW | leadless XSON3, Table 3-16 no-lead fillets; stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; pad 3 center off by 0.18mm; pad 1 size dev 81% (0.725x0.25 vs 0.4x0.25) |
| SOT035P100X050-6N | SOT-963 | 6 | 0.06mm | 238% | REVIEW | leadless XSON6, Table 3-16 no-lead fillets; stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; pad 1 size dev 238% (0.675x0.2 vs 0.2x0.2) |
| SOT080P180X070-3N | SOT-416 | 3 | 0.32mm | 104% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; pad 1 center off by 0.32mm; pad 1 size dev 104% (1.225x0.45 vs 0.6x0.5) |

## SOD (0 OK, 3 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| SOD37016X120N | D_SOD-123 | 2 | 0.07mm | 61% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; pad 1 size dev 61% (1.45x1.25 vs 0.9x1.2) |
| SOD25013X100N | D_SOD-323 | 2 | 0.14mm | 79% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; pad 1 size dev 79% (1.075x0.5 vs 0.6x0.45) |
| SOD16008X060N | D_SOD-523 | 2 | 0.01mm | 71% | REVIEW | stock uses vendor-minimal pattern; IPC-7351B Level B is intentionally larger; pad 1 size dev 71% (1.025x0.45 vs 0.6x0.7) |

## SOIC (7 OK, 0 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| SOIC127P600X175-8N | SOIC-8_3.9x4.9mm_P1.27mm | 8 | 0.00mm | 3% | OK |  |
| SOIC127P600X175-14N | SOIC-14_3.9x8.7mm_P1.27mm | 14 | 0.00mm | 3% | OK |  |
| SOIC127P600X175-16N | SOIC-16_3.9x9.9mm_P1.27mm | 16 | 0.00mm | 3% | OK |  |
| SOIC127P1030X265-18N | SOIC-18W_7.5x11.6mm_P1.27mm | 18 | 0.01mm | 1% | OK |  |
| SOIC127P1030X265-20N | SOIC-20W_7.5x12.8mm_P1.27mm | 20 | 0.01mm | 1% | OK |  |
| SOIC127P1030X265-24N | SOIC-24W_7.5x15.4mm_P1.27mm | 24 | 0.01mm | 1% | OK |  |
| SOIC127P1030X265-28N | SOIC-28W_7.5x17.9mm_P1.27mm | 28 | 0.01mm | 1% | OK |  |

## SOT (3 OK, 5 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| SOT095P240X110-3N | SOT-23 | 3 | 0.17mm | 10% | REVIEW | pad 3 center off by 0.17mm |
| SOT095P280X145-5N | SOT-23-5 | 5 | 0.03mm | 8% | OK | JEDEC MO-178 dims |
| SOT095P280X145-6N | SOT-23-6 | 6 | 0.03mm | 8% | OK | JEDEC MO-178 dims |
| SOT095P240X110-4N | SOT-143 | 4 | 0.16mm | 89% | REVIEW | real SOT-143 pin 1 is wider; ours uses uniform pins; pad 1 center off by 0.16mm; pad 1 size dev 89% (1.325x0.5 vs 0.7x1.0) |
| SOT150P400X160-3N | SOT-89-3 | 3/4/3 | 0.06mm | 33% | REVIEW | ours has separate tab pad 4; stock merges tab into pin 2 and uses vendor pattern; pad 1 size dev 33% (1.6x0.6 vs 1.3x0.9) |
| SOT230P670X180-4N | SOT-223 | 4 | 0.43mm | 33% | REVIEW | tab modeled as flat lead per Table 3-2 with JEDEC TO-261 tab width 2.9-3.1; pad 4 center off by 0.43mm; pad 1 size dev 33% (2.125x1.0 vs 2.0x1.5) |
| SOT228P980X230-3N | TO-252-3_TabPin4 | 4 | 0.00mm | 19% | OK | tab modeled as flat lead per Table 3-14 with JEDEC TO-252 tab contact dims |
| SOT254P1520X440-3N | TO-263-3_TabPin4 | 4 | 0.94mm | 18% | REVIEW | tab per Table 3-14 with JEDEC TO-263 dims; stock lead/tab lands are vendor thermal-enhanced and extend inward; pad 4 center off by 0.94mm |

## SSOP (0 OK, 6 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| SSOP065P780X200-14N | SSOP-14_5.3x6.2mm_P0.65mm | 14 | 0.10mm | 25% | REVIEW | pad 1 size dev 25% (2.15x0.5 vs 1.9x0.4) |
| SSOP065P780X200-16N | SSOP-16_5.3x6.2mm_P0.65mm | 16 | 0.01mm | 21% | REVIEW | pad 1 size dev 21% (2.15x0.5 vs 1.775x0.5) |
| SSOP065P780X200-20N | SSOP-20_5.3x7.2mm_P0.65mm | 20 | 0.10mm | 25% | REVIEW | pad 1 size dev 25% (2.15x0.5 vs 1.9x0.4) |
| SSOP065P780X200-24N | SSOP-24_5.3x8.2mm_P0.65mm | 24 | 0.10mm | 25% | REVIEW | pad 1 size dev 25% (2.15x0.5 vs 1.9x0.4) |
| SSOP065P780X200-28N | SSOP-28_5.3x10.2mm_P0.65mm | 28 | 0.10mm | 25% | REVIEW | pad 1 size dev 25% (2.15x0.5 vs 1.9x0.4) |
| SSOP065P530X175-8N | SSOP-8_2.95x2.8mm_P0.65mm | 8 | 0.44mm | 67% | REVIEW | closest stock analog; body width differs; pad 1 center off by 0.44mm; pad 1 size dev 67% (2.075x0.5 vs 1.6x0.3); courtyard differs +1.40x+0.20mm |

## TSSOP (7 OK, 0 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| TSSOP065P640X120-8N | TSSOP-8_4.4x3mm_P0.65mm | 8 | 0.03mm | 7% | OK |  |
| TSSOP065P640X120-14N | TSSOP-14_4.4x5mm_P0.65mm | 14 | 0.03mm | 7% | OK |  |
| TSSOP065P640X120-16N | TSSOP-16_4.4x5mm_P0.65mm | 16 | 0.03mm | 7% | OK |  |
| TSSOP065P640X120-20N | TSSOP-20_4.4x6.5mm_P0.65mm | 20 | 0.03mm | 7% | OK |  |
| TSSOP065P640X120-24N | TSSOP-24_4.4x7.8mm_P0.65mm | 24 | 0.03mm | 7% | OK |  |
| TSSOP065P640X120-28N | TSSOP-28_4.4x9.7mm_P0.65mm | 28 | 0.03mm | 7% | OK |  |
| TSSOP050P810X120-48N | TSSOP-48_6.1x12.5mm_P0.5mm | 48 | 0.02mm | 7% | OK |  |

## WLCSP (1 OK, 0 REVIEW, 0 FAIL)

| LandForge | KiCad stock | Pads | dCenter | dSize | Verdict | Notes |
|---|---|---|---|---|---|---|
| WLCSP36N040P6X6_257X257X055N | WLCSP-36_2.82x2.67mm_Layout6x6_P0.4mm | 36 | 0.00mm | 15% | OK | die size is vendor-specific; ball grid comparable |

## Footprints without a stock equivalent

Not compared -- KiCad stock has no matching generic footprint. These need manual validation against IPC-7351B directly.

- `IPC7351B_Chip/CAPCP1005X050N` (no stock equivalent for this family)
- `IPC7351B_Chip/CAPCP1608X080N` (no stock equivalent for this family)
- `IPC7351B_Chip/CAPCP2012X125N` (no stock equivalent for this family)
- `IPC7351B_Chip/CAPCP3216X160N` (no stock equivalent for this family)
- `IPC7351B_Chip/CAPCP3225X250N` (no stock equivalent for this family)
- `IPC7351B_BGA/BGA144C080P12X12_1100X1100X120N`
- `IPC7351B_BGA/BGA169C127P13X13_1900X1900X210N`
- `IPC7351B_BGA/BGA196C065P14X14_1000X1000X110N`
- `IPC7351B_BGA/BGA225C100P15X15_1700X1700X185N`
- `IPC7351B_BGA/BGA256C050P16X16_900X900X100N`
- `IPC7351B_BGA/BGA256C127P16X16_2300X2300X210N`
- `IPC7351B_BGA/BGA324C050P18X18_1000X1000X100N`
- `IPC7351B_BGA/BGA484C050P22X22_1200X1200X100N`
- `IPC7351B_BGA/BGA96C080P12X8_1000X700X120N`
- `IPC7351B_Chip/CAPCP1005X050N`
- `IPC7351B_Chip/CAPCP1608X080N`
- `IPC7351B_Chip/CAPCP2012X125N`
- `IPC7351B_Chip/CAPCP3216X160N`
- `IPC7351B_Chip/CAPCP3225X250N`
- `IPC7351B_Electrolytic/CAPAE1250X1350N`
- `IPC7351B_Molded/INDM2012X125N`
- `IPC7351B_Molded/INDM2520X200N`
- `IPC7351B_Molded/INDM3225X250N`
- `IPC7351B_Molded/INDM4532X320N`
- `IPC7351B_Molded/INDM5750X400N`
- `IPC7351B_Molded/RESM5025X250N`
- `IPC7351B_Molded/RESM6332X320N`
- `IPC7351B_QFN/QFN065P300X300X090-8T170N`
- `IPC7351B_QFN/SON050P300X300X090-10T240N`
- `IPC7351B_QFN/SON065P300X300X090-8T240N`
- `IPC7351B_QFN/SON127P500X600X090-8T440N`
- `IPC7351B_SOIC/QFP040P1600X1600X120-112N`
- `IPC7351B_SOIC/SSOP064P1020X310-48N`
- `IPC7351B_SOIC/SSOP064P1020X310-56N`
- `IPC7351B_SOIC/TSSOP050P810X120-32N`
- `IPC7351B_SOIC/TSSOP050P810X120-38N`
- `IPC7351B_SOIC/TSSOP050P810X120-56N`
- `LandForge_Crystal/OSCL120X100X040-4N`
- `LandForge_WLCSP/WLCSP100N040P10X10_444X444X055N`
- `LandForge_WLCSP/WLCSP100N050P10X10_507X507X055N`
- `LandForge_WLCSP/WLCSP121N040P11X11_487X487X055N`
- `LandForge_WLCSP/WLCSP144N040P12X12_530X530X055N`
- `LandForge_WLCSP/WLCSP16N040P4X4_196X196X055N`
- `LandForge_WLCSP/WLCSP20N040P4X5_176X203X055N`
- `LandForge_WLCSP/WLCSP25N050P5X5_255X255X055N`
- `LandForge_WLCSP/WLCSP49N040P7X7_310X310X055N`
- `LandForge_WLCSP/WLCSP64N040P8X8_354X354X055N`
- `LandForge_WLCSP/WLCSP81N040P9X9_397X397X055N`
- `LandForge_WLCSP/WLCSP9N050P3X3_170X170X055N`

