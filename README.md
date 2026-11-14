# Planet X · SPHEREx Observatory

A sky explorer for **NASA Space Apps 2026 — Planet X and SPHEREx**. Enter celestial
coordinates, play real infrared observations through time, and investigate
changes with aligned images and visible data-quality information.

**All displayed sky pixels originate in real SPHEREx FITS cutouts from NASA/IPAC
IRSA.** The five featured targets use bundled observations. Arbitrary coordinates
use the included Python archive server. No NASA API key is needed.

## Run on Windows

Python **3.14** is required for the pinned dependencies. From this repository:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

Open **http://127.0.0.1:8000**. Press Ctrl+C to stop. Once installed, `./run.ps1`
starts the application again. On macOS/Linux use `python3.14 -m venv .venv`, then
`.venv/bin/python` in place of `.\.venv\Scripts\python.exe`.

The frontend uses plain HTML/CSS/JavaScript, with no build step or installation.
Node.js 24 is used only for tests. Serve through HTTP; opening `index.html` as a
local file does not support data loading.

## Features

- Five real target sequences: **Barnard’s Star**, **Epsilon Indi B**, **WISE 0855**,
  **RW Aurigae**, and **R Draconis**.
- Playback, pause, scrubbing, thumbnails and keyboard controls: **← / →** and **Space**.
- Blink, adjustable split, signed difference, and mask-aware mean stacking.
- Reference selection and center-wavelength matching within **5%**.
- Decimal-degree and sexagesimal coordinates, fields **2–20 arcmin**, and all six arrays.
- Dates, source FITS, wavelengths, release, pixel coverage, flags and processing metadata.
- Shareable field links, PNG export and downloadable observation metadata.

Example field link:

```text
http://127.0.0.1:8000/?ra=133.79512916666667&dec=-7.245147222222222&fov=6&detector=D6&target=wise-0855#observatory
```

The array selector is not a claim that each exposure includes all 102 channels.
The actual wavelength varies with position and is read from the FITS spectral WCS.

## Public hosting

Use the included Dockerfile or import this repository into Render using
`render.yaml`. A hosting account may be needed; check current provider terms and
resource limits. **A Git push alone does not publish the Python backend.**

```sh
docker build -t planet-x-spherex .
docker run --rm -p 8000:8000 planet-x-spherex
```

The server uses Waitress, listens on `127.0.0.1:8000` locally, and accepts `HOST`
and `PORT` when deployed. Use HTTPS/reverse proxy and platform traffic controls
for a public launch. Live archive work has bounded concurrency and a basic per-IP
limit. Static hosting of `public/` supports bundled demos; arbitrary coordinates
require the Python server, which the interface explains if unavailable.

## Update observations

```powershell
.\.venv\Scripts\python.exe scripts/resolve_targets.py
.\.venv\Scripts\python.exe scripts/build_samples.py --refresh --limit 18
.\.venv\Scripts\python.exe scripts/validate_samples.py
```

Use `--target barnard` (or `epsilon-indi`, `wise-0855`, `rw-aurigae`, `r-draconis`)
to rebuild one target. Ignored `.cache/` holds downloaded cutouts. `--refresh`
refreshes metadata; immutable cutouts are reused. Configure future release names
in `COLLECTIONS` in `planetx/archive.py`; current releases are DR1 and QR3.
Live searches refresh metadata and sample up to 18 exposures over the available
baseline. This is a quick-look subset, not an exhaustive archive search.

## Test

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --test tests/frontend.test.mjs
node --check public/app.js
.\.venv\Scripts\python.exe scripts/validate_samples.py
```

Tests cover coordinates, alignment across orientations, quality masks, SIA column
parsing, spectral matching, masked arithmetic, API validation, rate limits,
static-file confinement and sharing. The sample validator generates
[docs/VALIDATION.md](docs/VALIDATION.md). CI repeats these checks on pushes and PRs.
Browser visual QA could not be completed because session browser automation
could not verify the current URL. Docker/Render deployment has not been verified.
The [real-data inspection sheet](docs/target-preview.png) shows the first and last
wavelength-matched images for each required field; it is not a browser screenshot.

## Methodology, credits and submission

Read [science and limitations](docs/SCIENCE.md), [data/software sources](docs/SOURCES.md),
and the [demo and submission guide](docs/SUBMISSION.md).

OpenAI Codex assisted with implementation, documentation and tests. No AI-generated
sky images, detections, spectra or measurements are presented as observations.
Synthetic arrays are used only in alignment tests. The team should review the
work and competition disclosure requirements before submitting.

Original code is MIT licensed; data and dependencies retain their own terms.
This independent project is not a NASA product and claims no discovery of Planet X.
