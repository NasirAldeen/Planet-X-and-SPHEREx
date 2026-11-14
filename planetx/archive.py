"""IRSA SIA2 discovery and FITS cutouts, on a common celestial grid.

Science conventions are documented in docs/SCIENCE.md. No generated sky data
are used in the application. All displayed pixels originate in IRSA FITS files.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import re
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.io.votable import parse_single_table
from astropy.time import Time
from astropy.wcs import WCS
from scipy.ndimage import map_coordinates

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
COLLECTIONS = ("spherex_dr1", "spherex_qr3")
IRSA = "https://irsa.ipac.caltech.edu"


def request_bytes(url, params=None, cache=True):
    """Retry transient archive errors; verify TLS and bound every download."""
    CACHE.mkdir(exist_ok=True)
    key = hashlib.sha256((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    path = CACHE / key
    if cache and path.exists():
        return path.read_bytes()
    for attempt in range(3):
        try:
            with requests.get(url, params=params, timeout=(15, 90), stream=True,
                              headers={"User-Agent": "Planet-X-SPHEREx/1.0"}) as response:
                response.raise_for_status()
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > 40_000_000:
                        raise ValueError("Archive response exceeds the 40 MB safety limit.")
                    chunks.append(chunk)
                data = b"".join(chunks)
            if cache:
                path.write_bytes(data)
            return data
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(1 + attempt)


def validate_query(ra, dec, fov, detector):
    ra, dec, fov = float(ra), float(dec), float(fov)
    if not all(math.isfinite(v) for v in (ra, dec, fov)):
        raise ValueError("Coordinates and field of view must be finite numbers.")
    if not 0 <= ra < 360 or not -90 <= dec <= 90:
        raise ValueError("RA must be 0–360° (excluding 360); declination −90–90°.")
    if not 2 <= fov <= 20:
        raise ValueError("Field of view must be between 2 and 20 arcminutes.")
    if detector not in [f"D{i}" for i in range(1, 7)]:
        raise ValueError("Choose detector D1–D6.")
    return ra, dec, fov, detector


def discover(ra, dec, detector, collections=COLLECTIONS, refresh=False):
    rows, notices = [], []
    for collection in collections:
        if collection not in COLLECTIONS:
            raise ValueError("Unsupported collection.")
        try:
            payload = request_bytes(IRSA + "/SIA", {
                "COLLECTION": collection, "POS": f"CIRCLE {ra} {dec} 0.001",
                "RESPONSEFORMAT": "VOTABLE"}, cache=not refresh)
            table = parse_single_table(io.BytesIO(payload)).to_table(use_names_over_ids=True)
            for row in table:
                if str(row["energy_bandpassname"]) != "SPHEREx-" + detector:
                    continue
                url = str(row["access_url"])
                if not url.startswith(IRSA + "/ibe/data/spherex/"):
                    continue
                rows.append({"url": url, "mjd": float(row["t_min"]),
                             "collection": collection, "obs_id": str(row["obs_id"]),
                             "detector": detector})
        except Exception as exc:
            notices.append(f"{collection}: archive query failed ({type(exc).__name__}).")
    # Prefer the first configured release when identical observations overlap.
    unique = {(r["obs_id"], r["detector"]): r for r in reversed(rows)}
    return sorted(unique.values(), key=lambda r: r["mjd"]), notices


def common_grid(ra, dec, fov):
    # Native SPHEREx sampling is about 6.15 arcsec; no artificial fine pixels.
    n = max(20, min(196, round(fov * 60 / 6.15)))
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [(n + 1) / 2, (n + 1) / 2]
    wcs.wcs.crval = [ra, dec]
    wcs.wcs.cdelt = [-fov / 60 / n, fov / 60 / n]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    yy, xx = np.mgrid[:n, :n]
    return wcs, wcs.pixel_to_world(xx, yy), n


def align_hdul(hdul, world, center):
    """Bilinear reprojection; conservative nearest-neighbor quality masking."""
    image = hdul["IMAGE"]
    source_wcs = WCS(image.header).celestial
    x, y = source_wcs.world_to_pixel(world)
    x = np.nan_to_num(x, nan=-1e6)
    y = np.nan_to_num(y, nan=-1e6)
    raw = np.array(image.data, dtype=float)
    flags = np.asarray(hdul["FLAGS"].data) if "FLAGS" in hdul else np.zeros(raw.shape)
    # SOURCE (21) and FULLSAMPLE (12) are informational, not unusable pixels.
    # Every other set bit is conservatively masked, including unknown future flags.
    informational = (1 << 21) | (1 << 12)
    bad = ~np.isfinite(raw) | ((flags.astype(np.int64) & ~informational) != 0)
    if "ZODI" in hdul and hdul["ZODI"].data.shape == raw.shape:
        raw -= hdul["ZODI"].data
    raw[bad] = np.nan
    pixels = map_coordinates(raw, [y, x], order=1, mode="constant", cval=np.nan,
                             prefilter=False)
    projected_bad = map_coordinates(bad.astype(float), [y, x], order=1,
                                   mode="constant", cval=1, prefilter=False) > 0
    pixels[projected_bad] = np.nan
    finite = np.isfinite(pixels)
    background = float(np.median(pixels[finite])) if finite.any() else 0.0
    pixels -= background
    wavelength = bandwidth = None
    try:
        cx, cy = source_wcs.world_to_pixel(center)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spectral_header = image.header.copy()
            for key in list(spectral_header):
                if re.match(r"^(A|B|AP|BP)_(ORDER|\d+_\d+)$", key):
                    del spectral_header[key]
            spectral = WCS(spectral_header, fobj=hdul, key="W")
            spectral.sip = None
            wave, width = spectral.pixel_to_world(cx, cy)
        wavelength = float(wave.to_value(u.um))
        bandwidth = float(width.to_value(u.um))
        if not math.isfinite(wavelength):
            wavelength = bandwidth = None
    except (ValueError, KeyError, TypeError, AttributeError):
        pass
    values, counts = np.unique(flags, return_counts=True)
    return pixels, {
        "wavelength_um": wavelength, "bandwidth_um": bandwidth,
        "unit": image.header.get("BUNIT", "MJy/sr"),
        "background_removed": background,
        "masked_fraction": round(1 - float(finite.mean()), 4),
        "flag_values": {str(int(v)): int(c) for v, c in zip(values, counts) if v != 0},
        "informational_flags_retained": ["SOURCE (21)", "FULLSAMPLE (12)"],
        "version": str(hdul[0].header.get("VERSION", "unknown")),
    }


def build_sequence(ra, dec, fov=6, detector="D3", limit=18, refresh=False, progress=None):
    ra, dec, fov, detector = validate_query(ra, dec, fov, detector)
    def report(message):
        if progress:
            progress(message)
    report("Searching the IRSA SPHEREx archive…")
    rows, notices = discover(ra, dec, detector, refresh=refresh)
    if not rows:
        raise ValueError("No observations returned for this detector and position. "
                         "Try another detector or retry if the archive is unavailable. " + " ".join(notices))
    # Even temporal sampling preserves the full baseline without downloading every exposure.
    indices = np.unique(np.linspace(0, len(rows) - 1, min(limit, len(rows))).round().astype(int))
    selected = [rows[i] for i in indices]
    _, world, n = common_grid(ra, dec, fov)
    center = SkyCoord(ra * u.deg, dec * u.deg)
    frames = []
    def load(row):
        params = {"center": f"{ra},{dec}", "size": f"{fov / 60 * 1.5:.8f}"}
        payload = request_bytes(row["url"], params)
        with fits.open(io.BytesIO(payload), memmap=False) as hdul:
            pixels, metadata = align_hdul(hdul, world, center)
        if metadata["masked_fraction"] > .95:
            raise ValueError("Less than 5% usable coverage")
        date = Time(row["mjd"], format="mjd").to_datetime(timezone=timezone.utc).isoformat()
        data = [float(f"{v:.6g}") if np.isfinite(v) else None for v in pixels.ravel()]
        return {**row, **metadata, "date": date,
                "cutout_url": requests.Request("GET", row["url"], params=params).prepare().url,
                "pixels": data}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(load, row): row for row in selected}
        for completed, future in enumerate(as_completed(futures), 1):
            try:
                frames.append(future.result())
            except Exception as exc:
                notices.append(f"Skipped {futures[future]['obs_id']}: {type(exc).__name__}: {exc}")
                report(notices[-1])
            report(f"Aligned {completed}/{len(selected)} cutouts; {len(frames)} usable.")
    frames.sort(key=lambda r: r["mjd"])
    if not frames:
        raise ValueError("The archive returned no usable cutouts. Retry or use a bundled target.")
    return {
        "schema_version": 1, "source": "NASA/IPAC IRSA · SPHEREx",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ra": ra, "dec": dec, "fov_arcmin": fov, "detector": detector,
        "width": n, "height": n, "pixel_scale_arcsec": fov * 60 / n,
        "orientation": "North up, East left", "collections": list(COLLECTIONS),
        "available_observations": len(rows), "frames": frames, "notices": notices,
        "processing": "WCS TAN/SIP alignment; all FLAGS except SOURCE and FULLSAMPLE masked; ZODI subtracted when available; "
                      "per-frame median sky removed; shared display stretch. Quick-look, not precision photometry.",
    }
