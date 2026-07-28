# KiCad Ecosystem Alignment Review

Date: 2026-07-28. Assesses LandForge against KiCad's current state (v10,
released 2026-03) and announced direction (v11, expected ~2027-02), plus
the IPC standards situation. Sources listed at the end.

## Verdict

The project's architecture is strongly aligned with where KiCad is going.
The two ideas LandForge is built on -- footprints generated from data, and
STEP as the 3D format -- are exactly the direction the official KiCad
libraries took in v10. No course correction is needed; the recommendations
below are packaging and robustness work, not redesign.

## Findings

### 1. Data-generated footprints are the official direction (aligned)

KiCad 10 release notes: over 78% of official footprints are now generated
from data rather than drawn by hand, and integrated generators produce
both 3D models and footprints from unified data definitions. LandForge's
CSV -> equations -> writer pipeline is the same philosophy. Our Stage C
plan (3D models generated from the same CSVs) mirrors KiCad's "unified
data definitions" approach.

**Differentiation check:** the official kicad-footprint-generator produces
one pattern per package (roughly IPC nominal, vendor-adjusted, YAML-driven).
LandForge's niche -- strict IPC-7351B equations, all three density levels,
full audit trail in each footprint -- is not covered by the official
generator. The niche remains valid.

### 2. STEP-only 3D models (aligned; affects Stage C)

KiCad 10 ships STEP files only; VRML was dropped ("better geometric
accuracy and fewer differences between visualization and exports").
Stage C's CadQuery -> STEP AP214 plan is exactly right. Do not generate
VRML at all.

### 3. IPC-7351C: not coming (foundation is safe)

The 7351C draft was worked on for years and discarded; the committee
stopped meeting after the death of its architect, and IPC asked PCB
Libraries to stop labeling their work "IPC-7351C". IPC downgraded 7351
from Standard to Guideline. **IPC-7351B (2010) remains the latest
published revision** -- LandForge's governing document is not about to be
superseded. Two 7351C-direction ideas are already industry practice and
already in LandForge: rounded-rectangle pads with 25% corner radius, and
data-driven generation. The `tables.py` abstraction would accommodate a
future revision's fillet tables if one ever appears.

### 4. Version-pinned strings (small robustness gap)

Two places hard-code the KiCad major version:
- `kicad_writer.py` emits format `(version 20260206)` -- correct for v10.
- `ipc7352_chip.py` emits `${KICAD10_3DMODEL_DIR}` model paths (135
  footprints). This variable is renamed every major release
  (KICAD11_3DMODEL_DIR in v11).

v11 (~Feb 2027) will bump the file format. Because everything is
generated, migration is a regenerate-and-commit, which is exactly why
KiCad itself moved to generated footprints. Recommendation: centralize
both strings as named constants (single point of change), and decide the
3D path-variable strategy before Stage C1 extends model references to the
other 11 libraries.

### 5. PCM packaging (Stage D5 -- requirements confirmed)

The addon format for content libraries: ZIP with `footprints/*.pretty`,
`3dmodels/*.3dshapes`, `resources/icon.png`, and a `metadata.json`
(reverse-DNS identifier, versions array with sha256/size, min/max
kicad_version). Submission = merge request to gitlab.com/kicad/addons/metadata.
Our output/ layout maps 1:1 onto this. Two consequences:

- **PCM-installed libraries live under `${KICAD10_3RD_PARTY}`**, so
  Stage C's own 3D models must be referenced via that variable (not
  KICAD10_3DMODEL_DIR, which is only for stock models). The current chip
  mapping to *stock* models via KICAD10_3DMODEL_DIR is correct as-is,
  because stock models are present in every install.
- `kicad_version` metadata lets us pin per-major-version releases, which
  matches the regenerate-per-major-version model.

### 6. Component-management ecosystem (HTTP/database libraries)

KiCad 8+ supports HTTP libraries (Part-DB, InvenTree, PartsBox) and
database libraries for company part management; these layers reference
footprints as `LIBNICKNAME:FOOTPRINTNAME` strings. Implications:

- **Name stability is an API contract.** Renames (like this week's
  SOT254P1400 -> SOT254P1520 data correction) break stored references.
  Adopt a policy: renames only on data-correction grounds, always in a
  version bump, always listed in a changelog. Ship a CHANGELOG.md from
  the first tagged release.
- **Stable library nicknames**: document recommended nicknames (the
  .pretty basenames) and ship an fp-lib-table snippet in the install docs
  so teams reference footprints consistently.

### 7. KLC divergences (deliberate -- document them)

For a third-party IPC library, KLC is informative, not binding. Known
divergences to document in the user guide rather than "fix":

| Topic | KLC | LandForge | Position |
|---|---|---|---|
| EP paste coverage | 50-80%, recommend 65% | 40% | IPC-7351B 3.1.5.7 is explicit; keep 40% as default, consider a config knob |
| Naming | Human-readable (SOIC-8_3.9x4.9mm_P1.27mm) | IPC-7351B Table 3-23 | IPC naming is the product |
| Density variants | One footprint (+ _HandSolder) | Three (M/N/L) | The product's core feature |
| Courtyard | 0.25mm default | Per density table (0.5/0.25/0.1) | Level B matches KLC exactly |
| Roundrect 25% | Required | Used | Aligned |
| Pin 1 top-left | Required | Used | Aligned |

### 8. Feature gaps worth considering (future work)

- **ThermalVias variants**: KiCad stock ships `_ThermalVias` variants of
  EP packages (vias share the pad number; no paste over vias >= 0.3mm;
  B.Cu relief pad). A generator option could add these -- useful and
  cheap once the EP machinery exists.
- **HandSolder variants**: stock ships `_HandSolder` variants; LandForge's
  Level A (Most) already serves this purpose -- document the equivalence.
- **Design blocks** (v10 feature): not library-relevant today; no action.
- **v11 geometric constraints**: CAD-side feature; no library impact
  announced. Watch the Post-V10 dev news thread before v11.

## Prioritized recommendations

1. **(Before Stage C1)** Decide 3D model path strategy: stock-model reuse
   keeps `${KICAD10_3DMODEL_DIR}`; own generated models use
   `${KICAD10_3RD_PARTY}` paths matching the PCM identifier. Centralize
   the version-pinned strings as constants.
2. **(Stage D, promoted)** PCM `metadata.json` + zip build script; tag
   v0.x releases with per-KiCad-major `kicad_version` pins.
3. **(Policy, now)** CHANGELOG.md + name-stability policy: renames are
   breaking changes, only for data corrections, always logged.
4. **(Docs)** KLC-divergence section in the user guide (table above),
   including the 40%-vs-65% EP paste rationale.
5. **(Optional feature)** Paste-coverage config knob and _ThermalVias
   variant generation.
6. **(Watch)** KiCad v11 file-format bump (~Feb 2027): regenerate, retest
   with the stock comparison, release a v11-pinned package.

## Sources

- [KiCad 10.0.0 release notes](https://www.kicad.org/blog/2026/03/Version-10.0.0-Released/)
- [KiCad addon/PCM developer documentation](https://dev-docs.kicad.org/en/addons/index.html)
- [KiCad HTTP libraries documentation](https://dev-docs.kicad.org/en/apis-and-binding/http-libraries/index.html)
- [KiCad Library Conventions (KLC)](https://klc.kicad.org/) -- esp. [F6.3 SMD pad requirements](https://klc.kicad.org/footprint/f6/f6.3/), [F4.4 thermal pads](https://klc.kicad.org/footprint/f4/f4.4/)
- [Official kicad-footprint-generator](https://gitlab.com/kicad/libraries/kicad-footprint-generator)
- [KiCad future versions roadmap wiki](https://gitlab.com/kicad/code/kicad/-/wikis/KiCad-Future-Versions-Roadmap) and the Post-V10 dev news forum thread
- PCB Libraries forum threads on IPC-7351C status ([release-date thread](https://www.pcblibraries.com/forum/ipc-7351c-updates-release-date_topic2958.html), [status discussion](https://www.pcblibraries.com/forum/do-we-have-a-new-release-of-ipc7351c_topic3150.html))
- [Part-DB KiCad integration](https://www.kicad.org/external-tools/partdb/)
