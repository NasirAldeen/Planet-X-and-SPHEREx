# Demo and submission guide

Planet X · SPHEREx Observatory makes the infrared sky inspectable across time.
Users choose a field, play chronological SPHEREx exposures and examine possible
changes through blinking, splitting, subtraction and stacking. Wavelength matching,
quality masks and source links help users question the evidence.

## Three-minute demonstration

1. Select Barnard’s Star. Explain that images are actual IRSA cutouts on a common
   sky grid. Show dates and the baseline. Do not promise a visible detection if
   motion is subpixel or the bright core is masked.
2. Play, pause and scrub. Explain why matching wavelengths matters.
3. Adjust Split; inspect signed Difference colors; Stack selected frames.
4. Open Epsilon Indi B, WISE 0855, RW Aurigae and R Draconis. Discuss motion versus
   variability, unresolved components, faintness and saturation.
5. Start a live coordinate query. Explain that it may take minutes and samples
   a subset of the archive. Show original FITS and export metadata.
6. Copy a field link. Emphasize public participation and evidence, not a claim
   that a new planet has been discovered.

## Coverage

| Challenge item | Implementation |
| --- | --- |
| Public-facing tool | Responsive web UI and deployable Python/Docker server. |
| RA/Dec input | Validated decimal and sexagesimal coordinates. |
| Time sequence | Playback, stepping, scrubbing and per-exposure dates. |
| Five test targets | Real bundled observations; see validation report. |
| New data | Refreshed SIA metadata and rebuildable samples. |
| Bands | Six arrays, measured center wavelengths and filtering. |
| Add/subtract | Mask-aware mean stack and signed difference. |
| Field size | 2–20 arcmin. |
| Coordinate URLs | RA, Dec, FOV, detector and target parameters. |
| Metadata | Release, scale, usable coverage, flag counts, versions, original FITS. |

Not implemented: Gaia/WISE overlays, calibrated spectra, automated candidate
detection or confirmed discoveries. These are optional extensions.

The team still needs its name/member credits and any portal-specific video or
presentation. Deploy the full app for a public URL; pushing code does not host the
backend. Review current competition rules, citations and AI disclosure. Inspect
the app in a browser and test a live query on the deployed host before recording.
