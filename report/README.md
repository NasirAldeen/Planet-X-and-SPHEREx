# Revised project report

Revision of the Planet X and SPHEREx project report, dated 15 November 2026.

## Files

- `SPHEREx_ProjectReport.pdf`: the final report, as edited by the team (14 pages). This is the version the site serves.
- `SPHEREx_Project_Report_Revised.pdf`: the draft before the team's final wording edits. The Word, Markdown and HTML files below match this draft.
- `SPHEREx_Project_Report_Revised.docx`: editable Word version.
- `SPHEREx_Project_Report_Revised.md`: editable source. The PDF, HTML and Word files are built from it.
- `SPHEREx_Project_Report_Revised.html`: browser version.
- `original/`: the first version of the report, unchanged (PDF and Markdown).
- `figures/`: Figures 1 to 6 and the equation images.
- `data/archive_verification.json`: what was read from each of the 20 FITS files (checksums, dates, wavelengths, flags).
- `data/archive_display.npz`: the display arrays behind Figures 2 to 4.
- `data/display_limits.json`, `data/mosaic_centre_counts.csv`: shared brightness limits and the counts behind Figure 5.
- `data/verified_exposures.json`: record of the two earlier R Draconis cutouts from the first version.
- `scripts/`: the three scripts below.

## Rebuilding

The image archive `PlanetX_Image_Set` is not copied here. Point the first script at its extracted folder.

1. `python -I scripts/analyze_archive.py <path to PlanetX_Image_Set> data` (needs numpy and astropy)
2. `python -I scripts/build_archive_figures.py` (needs numpy and matplotlib)
3. `python -I scripts/build_report.py` (needs matplotlib, Pillow, reportlab and python-docx; uses Windows Times New Roman and Arial)

Edit the Markdown, then run step 3. The reference list at the end of the Markdown is regenerated from `reference_catalog.json` on every build, so edit references there.

## What is not here

`judge100.pdf` was not available when this revision was made. The revision follows the lessons from it as summarised in the revision request.
