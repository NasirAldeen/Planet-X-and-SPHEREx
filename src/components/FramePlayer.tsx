import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { FastForward, Pause, Play, Rewind, Telescope } from "lucide-react";
import { fmtDate, formatDec, formatRA, mjdToDate, propagate, sharedStretch, type Frame, type Sequence, type Target } from "../lib/sky";

type Mode = "frame" | "diff" | "stack";
type Dir = -1 | 0 | 1;

const MJD_2026 = 61041; // 2026-01-01
const STEP_MS = 650;
const PROJECT_DAYS = 365;

/** Infrared-style colour ramp: black → deep red → orange → white. */
function ramp(t: number): [number, number, number] {
  const c = Math.min(1, Math.max(0, t));
  const r = Math.min(255, c * 3.2 * 255);
  const g = Math.min(255, Math.max(0, c * 3.2 - 1) * 255);
  const b = Math.min(255, Math.max(0, c * 3.2 - 2) * 255);
  return [r, g, b];
}

/** Diverging ramp for differences: blue (fainter) – black – orange (brighter). */
function diverge(t: number): [number, number, number] {
  const c = Math.max(-1, Math.min(1, t));
  return c >= 0 ? [255 * c, 150 * c, 70 * c] : [60 * -c, 120 * -c, 255 * -c];
}

function drawFrame(
  canvas: HTMLCanvasElement,
  seq: Sequence,
  frame: Frame,
  base: Frame,
  mode: Mode,
  stretch: { lo: number; hi: number }
) {
  const { width: w, height: h } = seq;
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d")!;
  const img = ctx.createImageData(w, h);
  const span = stretch.hi - stretch.lo || 1;
  for (let i = 0; i < w * h; i++) {
    const v = frame.pixels[i];
    const o = i * 4;
    if (v === null || v === undefined || !Number.isFinite(v)) {
      // masked pixel: dim hatch so missing data is visible, never painted as zero flux
      const x = i % w,
        y = Math.floor(i / w);
      const on = (x + y) % 4 < 2;
      img.data.set(on ? [40, 46, 84, 255] : [18, 22, 44, 255], o);
      continue;
    }
    let rgb: [number, number, number];
    if (mode === "diff") {
      const b0 = base.pixels[i];
      if (b0 === null || b0 === undefined || !Number.isFinite(b0)) {
        img.data.set([18, 22, 44, 255], o);
        continue;
      }
      rgb = diverge((v - b0) / (span * 0.35));
    } else {
      // asinh stretch against the shared display range
      const n = (v - stretch.lo) / span;
      rgb = ramp(Math.asinh(Math.max(0, n) * 10) / Math.asinh(10));
    }
    img.data.set([rgb[0], rgb[1], rgb[2], 255], o);
  }
  ctx.putImageData(img, 0, 0);
}

type Props = { target: Target; seq: Sequence };

export default function FramePlayer({ target, seq }: Props) {
  const frames = useMemo(() => [...seq.frames].sort((a, b) => a.mjd - b.mjd), [seq]);
  const stretch = useMemo(() => sharedStretch(frames), [frames]);
  // mask-aware mean of every frame: flagged pixels are skipped, never counted as zero
  const stacked = useMemo(() => {
    const n = seq.width * seq.height;
    const pixels: (number | null)[] = new Array(n);
    for (let p = 0; p < n; p++) {
      let sum = 0,
        k = 0;
      for (const f of frames) {
        const v = f.pixels[p];
        if (v !== null && v !== undefined && Number.isFinite(v)) {
          sum += v;
          k++;
        }
      }
      pixels[p] = k ? sum / k : null;
    }
    const frame: Frame = { ...frames[0], pixels };
    return { frame, stretch: sharedStretch([frame]) };
  }, [frames, seq.width, seq.height]);
  const [i, setI] = useState(frames.length - 1);
  const [dir, setDir] = useState<Dir>(0);
  const [mode, setMode] = useState<Mode>("frame");
  const [projDays, setProjDays] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // reset when the target changes
  useEffect(() => {
    setI(frames.length - 1);
    setDir(0);
    setProjDays(0);
    setMode("frame");
  }, [frames]);

  // chronological playback / rewind, always stepping through real frames
  useEffect(() => {
    if (dir === 0) return;
    const id = window.setInterval(() => {
      setI((cur) => {
        const next = cur + dir;
        if (next < 0 || next > frames.length - 1) {
          setDir(0);
          return cur;
        }
        return next;
      });
    }, STEP_MS);
    return () => window.clearInterval(id);
  }, [dir, frames.length]);

  // projection animation (future): animate days 0 → PROJECT_DAYS, no new data is shown
  const projRaf = useRef(0);
  const startProjection = () => {
    setDir(0);
    setI(frames.length - 1);
    cancelAnimationFrame(projRaf.current);
    const t0 = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - t0) / 3000);
      setProjDays(Math.round(p * PROJECT_DAYS));
      if (p < 1) projRaf.current = requestAnimationFrame(tick);
    };
    projRaf.current = requestAnimationFrame(tick);
  };
  useEffect(() => () => cancelAnimationFrame(projRaf.current), []);

  const frame = frames[i];
  const base = frames[0];

  useEffect(() => {
    if (!canvasRef.current || !frame) return;
    if (mode === "stack") drawFrame(canvasRef.current, seq, stacked.frame, base, "frame", stacked.stretch);
    else drawFrame(canvasRef.current, seq, frame, base, mode, stretch);
  }, [seq, frame, base, mode, stretch, stacked]);

  if (!frame) return null;

  const first = frames[0].mjd;
  const last = frames[frames.length - 1].mjd;
  const total = last - first + PROJECT_DAYS;
  const pct = (mjd: number) => ((mjd - first) / total) * 100;
  const dLambda = Math.abs(frame.wavelength_um - base.wavelength_um) / base.wavelength_um;
  const mixing = mode === "diff" && i !== 0 && dLambda > 0.05;

  // expected position marker (display convention: north up, east left)
  const scale = seq.pixel_scale_arcsec;
  const propagated = /propagated/i.test(target.coordinate_note);
  const shownMjd = last + projDays;
  const off = propagate(target, propagated ? MJD_2026 : first, projDays > 0 ? shownMjd : frame.mjd);
  const px = (seq.width / 2 - off.east / scale + 0.5) / seq.width;
  const py = (seq.height / 2 - off.north / scale + 0.5) / seq.height;
  const inside = px > 0 && px < 1 && py > 0 && py < 1;
  const projecting = projDays > 0;
  const showMarker = propagated || projecting;

  // projection geometry: where the target was at the last real frame, and how far it is drawn from there
  const off0 = propagate(target, propagated ? MJD_2026 : first, last);
  const x0 = (seq.width / 2 - off0.east / scale + 0.5) / seq.width;
  const y0 = (seq.height / 2 - off0.north / scale + 0.5) / seq.height;
  const pmPerYear = Math.hypot(target.pm_ra_cosdec, target.pm_dec) / 1000; // arcsec per year
  const movedArcsec = (pmPerYear * projDays) / 365.25;
  const moves = pmPerYear > 0.1;
  // the shift is only a pixel or two, so an inset redraws it enlarged to a fixed size
  const fullPct = (((pmPerYear * PROJECT_DAYS) / 365.25 / scale) / seq.width) * 100;
  const mag = moves ? 34 / fullPct : 1;
  const ix = (px - x0) * 100 * mag;
  const iy = (py - y0) * 100 * mag;

  const rewinding = dir === -1;

  return (
    <div className="player">
      <div className={`screen${rewinding ? " is-rewinding" : ""}${projecting ? " is-projecting" : ""}`}>
        <canvas ref={canvasRef} className="screen__canvas" aria-label={`SPHEREx frame of ${target.name}, ${fmtDate(mjdToDate(frame.mjd))}`} />
        {showMarker && inside && (
          <motion.div
            className={`marker${projecting ? " is-projected" : ""}`}
            animate={{ left: `${px * 100}%`, top: `${py * 100}%` }}
            transition={{ type: "spring", stiffness: 120, damping: 20 }}
            aria-hidden="true"
          />
        )}
        {projecting && moves && (
          <>
            {/* path from the last observed position to the projected one */}
            <svg className="proj-path" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              <line x1={x0 * 100} y1={y0 * 100} x2={px * 100} y2={py * 100} />
            </svg>
            <div className="marker is-origin" style={{ left: `${x0 * 100}%`, top: `${y0 * 100}%` }} aria-hidden="true" />
            <div className="proj-inset">
              <svg viewBox="-50 -50 100 100" aria-hidden="true">
                <circle cx="0" cy="0" r="5" className="o" />
                <line x1="0" y1="0" x2={ix} y2={iy} />
                <circle cx={ix} cy={iy} r="6" className="p" />
              </svg>
              <span>enlarged {mag.toFixed(0)}×</span>
            </div>
          </>
        )}
        <AnimatePresence>
          {rewinding && (
            <motion.div className="screen__rewind" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} aria-hidden="true">
              <span>REWIND</span>
            </motion.div>
          )}
          {projecting && (
            <motion.div className="screen__projection" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <span>PROJECTION · no observation</span>
              <strong>{moves ? `+${movedArcsec.toFixed(1)}″ · ${(movedArcsec / scale).toFixed(1)} pixels` : "no measurable motion expected"}</strong>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="timecode" aria-live="off">
        <strong>{projecting ? fmtDate(mjdToDate(shownMjd)) : fmtDate(mjdToDate(frame.mjd))}</strong>
        <span>
          {projecting
            ? `+${projDays} d beyond last frame · linear catalogue motion`
            : `frame ${i + 1} of ${frames.length} · ${frame.wavelength_um.toFixed(2)} µm · ${frame.detector}`}
        </span>
      </div>

      {/* timeline: ticks sit at their real dates, so irregular gaps stay visible */}
      <div className="timeline" role="group" aria-label="Observation dates">
        <div className="timeline__future" style={{ left: `${pct(last)}%` }} />
        {frames.map((f, k) => (
          <button
            key={f.obs_id}
            className={`tick${k === i && !projecting ? " is-on" : ""}`}
            style={{ left: `${pct(f.mjd)}%` }}
            onClick={() => {
              setDir(0);
              setProjDays(0);
              setI(k);
            }}
            title={`${fmtDate(mjdToDate(f.mjd))} · ${f.wavelength_um.toFixed(2)} µm`}
            aria-label={`Frame ${k + 1}, ${fmtDate(mjdToDate(f.mjd))}`}
          />
        ))}
        {projecting && <div className="timeline__head" style={{ left: `${pct(shownMjd)}%` }} />}
      </div>
      <div className="timeline__ends">
        <span>{fmtDate(mjdToDate(first))}</span>
        <span className="muted">projection →</span>
      </div>

      <div className="controls">
        <button className="ctl" onClick={() => { setProjDays(0); setDir(dir === -1 ? 0 : -1); }} aria-pressed={dir === -1} aria-label="Rewind through earlier frames">
          <Rewind size={16} aria-hidden="true" /> Rewind
        </button>
        <button className="ctl ctl--main" onClick={() => { setProjDays(0); setDir(dir === 1 ? 0 : 1); }} aria-pressed={dir === 1} aria-label={dir === 1 ? "Pause" : "Play forward"}>
          {dir === 1 ? <Pause size={16} aria-hidden="true" /> : <Play size={16} aria-hidden="true" />} {dir === 1 ? "Pause" : "Play"}
        </button>
        <button className={`ctl ctl--project${projecting ? " is-on" : ""}`} onClick={startProjection} aria-label="Project motion one year forward">
          <FastForward size={16} aria-hidden="true" /> Project +1 year
        </button>
        <div className="seg" role="group" aria-label="Display mode">
          <button className={mode === "frame" ? "is-on" : ""} onClick={() => setMode("frame")}>Image</button>
          <button className={mode === "diff" ? "is-on" : ""} onClick={() => setMode("diff")}>Change</button>
          <button className={mode === "stack" ? "is-on" : ""} onClick={() => { setDir(0); setProjDays(0); setMode("stack"); }}>Stack</button>
        </div>
      </div>

      {projecting && (
        <p className="note note--proj">
          <FastForward size={14} aria-hidden="true" />
          <span>
            <strong>Projection, not an observation.</strong>{" "}
            {moves
              ? `The blue ring is where the catalogue places ${target.name} at the last real frame; the orange ring is where its catalogue motion (${pmPerYear.toFixed(1)}″ per year) carries it by the date shown. The image underneath is still the last real frame.`
              : `${target.name} is studied for brightness changes. Its catalogue motion is too small to see in a year.`}
          </span>
        </p>
      )}
      {mode === "stack" && (
        <p className="note">
          <Telescope size={14} aria-hidden="true" /> Stack = the average of all {frames.length} frames ({fmtDate(mjdToDate(first))} to {fmtDate(mjdToDate(last))}), with its own brightness scale. Averaging lowers the noise, but it mixes wavelengths, and anything that moved between frames is smeared.
        </p>
      )}
      {mode === "diff" && (
        <p className="note">
          <Telescope size={14} aria-hidden="true" /> Change = this frame minus the first frame ({fmtDate(mjdToDate(base.mjd))}). Orange is brighter, blue is fainter.
          {mixing && <strong> These two frames differ in wavelength by {(dLambda * 100).toFixed(0)}%, so the difference mixes time and colour.</strong>}
        </p>
      )}
      <p className="credit">Image data: NASA/JPL-Caltech · SPHEREx, served by NASA/IPAC IRSA. Hatched pixels were flagged as unreliable and are left blank.</p>
      <details className="tech">
        <summary>Technical details</summary>
        <dl className="meta">
          <div><dt>Sky position (ICRS)</dt><dd>RA {formatRA(target.ra)} · Dec {formatDec(target.dec)}</dd></div>
          <div><dt>Image orientation</dt><dd>North up, east to the left</dd></div>
          <div><dt>Image size</dt><dd>{seq.width}×{seq.height} px at {scale.toFixed(2)}″ per pixel ({target.fov}′ field)</dd></div>
          <div><dt>Flagged pixels</dt><dd>{(frame.masked_fraction * 100).toFixed(1)}% of this frame</dd></div>
          <div><dt>Data release</dt><dd>{frame.collection.replace("spherex_", "").toUpperCase()}</dd></div>
          <div><dt>Observation ID</dt><dd>{frame.obs_id}</dd></div>
          <div><dt>Original file</dt><dd><a href={frame.url} target="_blank" rel="noreferrer">Open the FITS file at IRSA</a></dd></div>
          <div><dt>Processing</dt><dd>{seq.processing}</dd></div>
        </dl>
      </details>
    </div>
  );
}
