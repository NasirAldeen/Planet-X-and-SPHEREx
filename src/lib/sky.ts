import * as THREE from "three";

export type Target = {
  id: string;
  name: string;
  kind: string;
  detector: string;
  hint: string;
  ra: number;
  dec: number;
  fov: number;
  pm_ra_cosdec: number; // mas/yr
  pm_dec: number; // mas/yr
  coordinate_note: string;
  source_url: string;
};

export type Frame = {
  obs_id: string;
  mjd: number;
  date: string;
  detector: string;
  wavelength_um: number;
  bandwidth_um: number;
  masked_fraction: number;
  background_removed: number;
  version: string;
  collection: string;
  url: string;
  pixels: (number | null)[];
};

export type Sequence = {
  width: number;
  height: number;
  pixel_scale_arcsec: number;
  orientation: string;
  processing: string;
  frames: Frame[];
};

const DEG = Math.PI / 180;

/** Planetarium view: camera at the origin, looking outward; RA grows to the left as seen from Earth. */
export function radecToVec3(raDeg: number, decDeg: number, r = 10): THREE.Vector3 {
  const ra = raDeg * DEG;
  const dec = decDeg * DEG;
  return new THREE.Vector3(
    -r * Math.cos(dec) * Math.sin(ra),
    r * Math.sin(dec),
    -r * Math.cos(dec) * Math.cos(ra)
  );
}

export function formatRA(deg: number): string {
  const h = deg / 15;
  const hh = Math.floor(h);
  const m = Math.floor((h - hh) * 60);
  const s = ((h - hh) * 60 - m) * 60;
  return `${hh}h ${String(m).padStart(2, "0")}m ${s.toFixed(1).padStart(4, "0")}s`;
}

export function formatDec(deg: number): string {
  const sign = deg < 0 ? "−" : "+";
  const a = Math.abs(deg);
  const d = Math.floor(a);
  const m = Math.floor((a - d) * 60);
  const s = ((a - d) * 60 - m) * 60;
  return `${sign}${d}° ${String(m).padStart(2, "0")}′ ${s.toFixed(0).padStart(2, "0")}″`;
}

/** Linear proper-motion offset in arcsec (east, north) from the frame's own date to a target date. */
export function propagate(t: Target, fromMjd: number, toMjd: number) {
  const years = (toMjd - fromMjd) / 365.25;
  return { east: (t.pm_ra_cosdec / 1000) * years, north: (t.pm_dec / 1000) * years };
}

export function mjdToDate(mjd: number): Date {
  return new Date((mjd - 40587) * 86400000);
}

export function fmtDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

/** Robust shared stretch: percentiles over all valid pixels of every frame. */
export function sharedStretch(frames: Frame[]): { lo: number; hi: number } {
  const vals: number[] = [];
  for (const f of frames) for (const v of f.pixels) if (v !== null && Number.isFinite(v)) vals.push(v);
  vals.sort((a, b) => a - b);
  const q = (p: number) => vals[Math.min(vals.length - 1, Math.floor(p * vals.length))] ?? 0;
  return { lo: q(0.02), hi: q(0.995) };
}
