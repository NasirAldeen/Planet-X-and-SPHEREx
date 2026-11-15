# SPHEREx Voyage

A sky explorer for **NASA Space Apps 2026: Planet X and SPHEREx**. Launch from the first page, travel at light speed, and arrive at a 3D map of the sky. Pick one of five benchmark objects and replay real SPHEREx infrared observations of it through time.

The five targets are Barnard's Star, Epsilon Indi B, WISE 0855, RW Aurigae and R Draconis.

## Run it

Node.js 20 or newer is required.

```sh
npm install
npm run dev
```

Open the address Vite prints (by default http://localhost:5173). `npm run build` type-checks and writes a static site to `dist/`.

## What it does

- **Launch sequence.** A third-person chase view of the ship with a countdown, then a light-speed tunnel. "Return to launch" plays the journey in reverse.
- **Globe view.** The targets sit at their real right ascension and declination. Drag to look around.
- **Reference view.** "Step back" pulls the camera outside the sky sphere for a wide shot with the Milky Way band.
- **Frame player.** Plays each target's SPHEREx cutouts in date order on a timeline that keeps the real gaps between observations.
  - **Rewind and play** step through real frames only.
  - **Change** subtracts the first frame and warns when the two frames differ in wavelength.
  - **Stack** averages every frame, skipping flagged pixels.
  - **Project +1 year** draws where catalogue motion would carry a moving target. It is labelled as a projection and never shows invented pixels.
- **Documents.** The project report, its figures and its references.
- **Links.** `?target=wise-0855` opens a target directly. `?ra=133.79&dec=-7.24` pins a position (no images are loaded for arbitrary positions yet).

## What is real and what is not

| Item | Source |
| --- | --- |
| Sky frames in the player | Original SPHEREx spectral-image cutouts (DR1 and QR3) from NASA/IPAC IRSA |
| "More views of this field" images | Previews rendered from SPHEREx mosaics and dated cutouts retrieved from IRSA |
| WISE 0855 context image | NASA/JPL PIA18002, credit NASA/JPL-Caltech/Penn State University. Not a SPHEREx image |
| Milky Way band | Generated points placed along the real galactic plane. Not a photograph |
| Grey dust, dotted lines, ship, tunnel | Decoration |

Frames are quick-look displays, not calibrated photometry. This project claims no new planet, no measured motion and no measured brightness change. See `public/docs/SPHEREx_ProjectReport.pdf` for the limits.

## Not built yet

Live archive queries for arbitrary coordinates, a field-of-view selector, per-detector stacking, spectra, Gaia and WISE overlays, and decoded contamination flags.

## Earlier version

The previous Python and plain-JavaScript observatory is preserved in this repository's git history (commit `7587518`).

## Licence and credits

The MIT licence in `LICENSE` covers the original source code in this repository. It does not cover third-party material:

- SPHEREx data: NASA/JPL-Caltech, served by the NASA/IPAC Infrared Science Archive.
- `public/docs/PIA18002.jpg`: NASA/JPL-Caltech/Penn State University, used under the JPL image use policy.
- The light-speed fragment shader in `src/components/Warp.tsx` is by Matthias Hurrle (@atzedent), taken from the "light-speed" component on 21st.dev, where its licence is listed as unknown. Confirm the licence or replace the shader before reusing it.
- Research papers summarised in `public/data/references.json` remain under their authors' and publishers' rights.

No NASA endorsement is implied.

## Also in this repository

- `report/`: the revised project report as PDF, Word and Markdown, the first version (`report/original/`), and the scripts and verification data behind its figures. The same PDF is served by the site from `public/docs/`.
- `media/SPHEREx_Voyage_Teaser.mp4`: a 30-second teaser video with sound. `media/make_teaser.py` is the script that drew it. The galaxy and the route in the video are artistic.

The SPHEREx image archive used by the report (about 106 MB of FITS files from NASA/IPAC IRSA) and the third-party research papers are not included here. The report lists the source link and checksum record for every file.
