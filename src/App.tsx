import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, BookOpen, Compass, Home, Rocket, SkipForward, Telescope, X, ZoomOut } from "lucide-react";
import Starfield from "./components/Starfield";
import Chase from "./components/Chase";
import Warp from "./components/Warp";
import SkyMap, { type View } from "./components/SkyMap";
import FramePlayer from "./components/FramePlayer";
import Documents, { useReferences } from "./components/Documents";
import { CONSTELLATION, COPY } from "./lib/content";
import { fmtDate, mjdToDate, type Sequence, type Target } from "./lib/sky";

/** hero → launch (chase camera) → warp → map, and back again: map → back-warp → back-stars → hero */
type Phase = "hero" | "launch" | "warp" | "map" | "back-warp" | "back-stars";

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: 0.3 + i * 0.2, duration: 0.8, ease: "easeOut" as const } }),
};

function useSpeedRamp(initial: number) {
  const ref = useRef(initial);
  const token = useRef(0);
  const ramp = useCallback((to: number, ms: number) => {
    const id = ++token.current; // a newer ramp cancels an older one
    const from = ref.current;
    const t0 = performance.now();
    const tick = (now: number) => {
      if (id !== token.current) return;
      const p = Math.min(1, (now - t0) / ms);
      ref.current = from + (to - from) * (p * p);
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, []);
  const set = useCallback((v: number) => {
    token.current++;
    ref.current = v;
  }, []);
  return { ref, ramp, set };
}

export default function App() {
  const [phase, setPhase] = useState<Phase>("hero");
  const [view, setView] = useState<View>("globe");
  const [targets, setTargets] = useState<Target[]>([]);
  const [seqs, setSeqs] = useState<Record<string, Sequence>>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [custom, setCustom] = useState<Target | null>(null);
  const [showNames, setShowNames] = useState(true);
  const [docs, setDocs] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const refs = useReferences();
  const star = useSpeedRamp(2);
  const warp = useSpeedRamp(0.6);
  const shipOn = useRef(false);
  const shipStage = useRef<"launch" | "warp" | "return">("launch");

  // every timed step of a journey goes through here so Skip can cancel what is still pending
  const timers = useRef<number[]>([]);
  const later = useCallback((fn: () => void, ms: number) => {
    timers.current.push(window.setTimeout(fn, ms));
  }, []);
  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  }, []);
  useEffect(() => clearTimers, [clearTimers]);

  // load the five bundled target sequences (real SPHEREx cutouts)
  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const list: Target[] = await (await fetch("/data/targets.json")).json();
        if (!live) return;
        setTargets(list);
        const loaded: Record<string, Sequence> = {};
        await Promise.all(
          list.map(async (t) => {
            loaded[t.id] = await (await fetch(`/data/${t.id}.json`)).json();
          })
        );
        if (live) setSeqs(loaded);
      } catch {
        if (live) setError("Could not load the SPHEREx observations. Reload the page, or check that /data is being served.");
      }
    })();
    return () => {
      live = false;
    };
  }, []);

  // deep links: ?target=wise-0855 skips the intro, ?ra=..&dec=.. drops a pin
  useEffect(() => {
    const q = new URLSearchParams(location.search);
    const id = q.get("target");
    const ra = parseFloat(q.get("ra") ?? "");
    const dec = parseFloat(q.get("dec") ?? "");
    if (id || (Number.isFinite(ra) && Number.isFinite(dec))) setPhase("map");
    if (id) setSelectedId(id);
    else if (Number.isFinite(ra) && Number.isFinite(dec)) {
      setCustom(makeCustom(ra, dec));
      setSelectedId("custom");
    }
  }, []);

  const select = useCallback((id: string | null) => {
    setSelectedId(id);
    const u = new URL(location.href);
    u.search = "";
    if (id && id !== "custom") u.searchParams.set("target", id);
    history.replaceState(null, "", u);
  }, []);

  // ---- outbound journey: countdown in the cockpit → ignition → light speed → the sky
  const engage = () => {
    clearTimers();
    star.set(2);
    setPhase("launch");
  };
  const onIgnition = useCallback(() => {
    star.ramp(42, 2400);
    later(() => {
      setPhase("warp");
      warp.set(1.5); // enter the tunnel already moving, so it does not feel like braking
      warp.ramp(3.2, 3200);
      later(() => {
        setView("globe");
        setPhase("map");
      }, 4600);
    }, 2600);
  }, [star, warp, later]);

  // ---- return journey: the same movement, reversed
  const returnHome = () => {
    clearTimers();
    setDocs(false);
    select(null);
    setView("reference"); // 1. pull back out of the sky
    later(() => {
      setPhase("back-warp"); // 2. the tunnel, running backwards
      warp.set(-3.2);
      warp.ramp(-0.5, 3000);
      later(() => {
        setPhase("back-stars"); // 3. stars fall away behind us and slow down
        star.set(-42);
        star.ramp(2, 2200);
        later(() => setPhase("hero"), 2300); // 4. home
      }, 3200);
    }, 1600);
  };

  const skip = () => {
    clearTimers();
    if (phase === "back-warp" || phase === "back-stars") {
      star.set(2);
      setPhase("hero");
    } else {
      setView("globe");
      setPhase("map");
    }
  };

  const allTargets = useMemo(() => (custom ? [...targets, custom] : targets), [targets, custom]);
  const selected = allTargets.find((t) => t.id === selectedId) ?? null;
  const intro = phase !== "map";
  const stars = phase === "hero" || phase === "launch" || phase === "back-stars";
  const tunnel = phase === "warp" || phase === "back-warp";
  const outside = view === "reference";
  // the ship's stage follows the phase, but holds its last value while the journey layer fades out
  if (phase === "hero") shipOn.current = false;
  else if (phase !== "map") {
    shipOn.current = true;
    shipStage.current = phase === "launch" ? "launch" : phase === "warp" ? "warp" : "return";
  }

  return (
    <div className="app">
      {/* JOURNEY (hero, cockpit, light speed) */}
      <AnimatePresence>
        {intro && (
          <motion.div key="intro" className="intro" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 1.1 }}>
            {/* stars and tunnel cross-fade, so the jump to light speed is a blend, not a cut */}
            <AnimatePresence>
              {stars && (
                <motion.div key="stars" className="fill layer" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, scale: 1.25 }} transition={{ duration: 1.3, ease: "easeInOut" }}>
                  <Starfield speedRef={star.ref} mouseBoost={phase === "hero"} />
                </motion.div>
              )}
              {tunnel && (
                <motion.div key="tunnel" className="fill layer" initial={{ opacity: 0, scale: 1.6 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 1.6 }} transition={{ duration: 1.3, ease: "easeInOut" }}>
                  <Warp speedRef={warp.ref} />
                </motion.div>
              )}
              {tunnel && <motion.div key={`flash-${phase}`} className="flash" initial={{ opacity: 0.8 }} animate={{ opacity: 0 }} exit={{ opacity: 0 }} transition={{ duration: 1.2, ease: "easeOut" }} />}
            </AnimatePresence>
            {phase === "hero" && <div className="intro__shade" />}

            {phase === "hero" && (
              <div className="hero">
                <motion.div className="badge" custom={0} variants={fadeUp} initial="hidden" animate="visible">
                  <Rocket size={16} aria-hidden="true" />
                  <span>NASA SPHEREx · 102 infrared bands</span>
                </motion.div>
                <motion.h1 custom={1} variants={fadeUp} initial="hidden" animate="visible">
                  SPHEREx Voyage
                </motion.h1>
                <motion.p custom={2} variants={fadeUp} initial="hidden" animate="visible">
                  Travel to five objects in the infrared sky and watch them change through real observations.
                </motion.p>
                <motion.div custom={3} variants={fadeUp} initial="hidden" animate="visible">
                  <motion.button className="btn" onClick={engage} whileHover={{ scale: 1.06 }} whileTap={{ scale: 0.95 }} transition={{ type: "spring", stiffness: 300, damping: 20 }}>
                    Engage thrusters <ArrowRight size={20} aria-hidden="true" />
                  </motion.button>
                </motion.div>
              </div>
            )}

            {/* one ship for the whole journey, so it never resets between stages */}
            {shipOn.current && <Chase stage={shipStage.current} onIgnition={onIgnition} />}

            {phase === "warp" && (
              <motion.p className="warp-caption" initial={{ opacity: 0 }} animate={{ opacity: [0, 1, 1, 0] }} transition={{ duration: 4.4, times: [0, 0.2, 0.75, 1] }}>
                Destination: the infrared sky
              </motion.p>
            )}
            {phase !== "hero" && (
              <button className="skip" onClick={skip}>
                Skip <SkipForward size={14} aria-hidden="true" />
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* MAP EXPERIENCE */}
      {phase === "map" && (
        <motion.div className="stage" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1.2 }}>
          <div className="sky">
            <SkyMap targets={allTargets} selectedId={selectedId} showNames={showNames} view={view} onSelect={select} />
          </div>

          <header className="brand">
            <strong>SPHEREx VOYAGE</strong>
            <span className="mono">{outside ? "REFERENCE VIEW · THE WHOLE SKY FROM OUTSIDE" : "GLOBE VIEW · LOOKING OUT FROM EARTH"}</span>
          </header>

          <AnimatePresence>
            {outside && (
              <motion.p key="cap" className="view-caption" initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                Seen from outside, the sky is a mirror image of the view from Earth. The Milky Way band sits where it really is, but its points are generated, not a photograph. The dotted lines are decoration.
              </motion.p>
            )}
          </AnimatePresence>

          <nav className="rail" aria-label="Targets">
            <h2 className="mono">TARGETS</h2>
            <ul>
              {targets.map((t) => (
                <li key={t.id}>
                  <button className={t.id === selectedId ? "is-on" : ""} onClick={() => select(t.id)} style={{ ["--c" as string]: COPY[t.id]?.color }}>
                    <i aria-hidden="true" />
                    <span>
                      {t.name}
                      <small>{t.kind}</small>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
            <CoordForm
              onGo={(ra, dec) => {
                setCustom(makeCustom(ra, dec));
                setSelectedId("custom");
              }}
            />
            <label className="toggle">
              <input type="checkbox" checked={showNames} onChange={(e) => setShowNames(e.target.checked)} /> Show names on the sky
            </label>
            <p className="rail__hint">Drag to look around. Select a point to fly to it. The grey dust is decoration, not a star catalogue.</p>
          </nav>

          {(selected || !outside) && (
            <aside className="panel" aria-live="polite">
              {selected && (
                <button className="icon-btn panel__close" onClick={() => select(null)} aria-label="Close this target">
                  <X size={18} />
                </button>
              )}
              {error && <p className="error">{error}</p>}
              {!selected && <Overview targets={targets} seqs={seqs} />}
              {selected && selected.id === "custom" && <CustomPanel />}
              {selected && selected.id !== "custom" && <TargetPanel target={selected} seq={seqs[selected.id]} refs={refs} openDocs={() => setDocs(true)} />}
            </aside>
          )}

          <div className="bar">
            <button onClick={returnHome} title="Fly back to the start">
              <Home size={14} aria-hidden="true" /> Return to launch
            </button>
            {outside ? (
              <button className="is-primary" onClick={() => setView("globe")}>
                <Rocket size={14} aria-hidden="true" /> Launch into the sky
              </button>
            ) : (
              <button onClick={() => setView("reference")}>
                <ZoomOut size={14} aria-hidden="true" /> Step back
              </button>
            )}
            <button aria-pressed={!docs} className={!docs ? "is-on" : ""} onClick={() => setDocs(false)}>
              <Compass size={14} aria-hidden="true" /> Sky
            </button>
            <button aria-pressed={docs} className={docs ? "is-on" : ""} onClick={() => setDocs(true)}>
              <BookOpen size={14} aria-hidden="true" /> Documents
            </button>
          </div>
        </motion.div>
      )}

      <AnimatePresence>
        {docs && phase === "map" && (
          <motion.div key="docs" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 30 }} transition={{ duration: 0.4 }} className="docs-wrap">
            <Documents refs={refs} onClose={() => setDocs(false)} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function makeCustom(ra: number, dec: number): Target {
  return {
    id: "custom",
    name: "Your position",
    kind: "Pinned position",
    detector: "",
    hint: "",
    ra: ((ra % 360) + 360) % 360,
    dec: Math.max(-90, Math.min(90, dec)),
    fov: 6,
    pm_ra_cosdec: 0,
    pm_dec: 0,
    coordinate_note: "User-entered position",
    source_url: "",
  };
}

function CoordForm({ onGo }: { onGo: (ra: number, dec: number) => void }) {
  const [ra, setRa] = useState("");
  const [dec, setDec] = useState("");
  const a = parseFloat(ra);
  const d = parseFloat(dec.replace("−", "-"));
  const valid = Number.isFinite(a) && Number.isFinite(d) && d >= -90 && d <= 90;
  return (
    <form
      className="coords"
      onSubmit={(e) => {
        e.preventDefault();
        if (valid) onGo(a, d);
      }}
    >
      <h3 className="mono">PIN A SKY POSITION</h3>
      <label>
        Right ascension (degrees, 0 to 360)
        <input inputMode="decimal" value={ra} onChange={(e) => setRa(e.target.value)} placeholder="133.7951" />
      </label>
      <label>
        Declination (degrees, −90 to 90)
        <input inputMode="decimal" value={dec} onChange={(e) => setDec(e.target.value)} placeholder="-7.2451" />
      </label>
      <button className="btn btn--small" disabled={!valid}>
        Fly there
      </button>
    </form>
  );
}

function Overview({ targets, seqs }: { targets: Target[]; seqs: Record<string, Sequence> }) {
  const all = Object.values(seqs).flatMap((s) => s.frames);
  const first = all.length ? Math.min(...all.map((f) => f.mjd)) : null;
  const last = all.length ? Math.max(...all.map((f) => f.mjd)) : null;
  return (
    <>
      <p className="crumb mono">SKY / OVERVIEW</p>
      <h1>Five patches of sky, replayed.</h1>
      <p className="lede">Pick a point. Watch what SPHEREx saw there, one observation at a time.</p>
      <div className="stats">
        <div><strong>{targets.length}</strong><span>TARGETS</span></div>
        <div><strong>{all.length || "…"}</strong><span>REAL FRAMES</span></div>
        <div><strong>102</strong><span>BANDS · MISSION</span></div>
      </div>
      {first !== null && last !== null && (
        <p className="body">
          Frames here were taken between {fmtDate(mjdToDate(first))} and {fmtDate(mjdToDate(last))}. Each is an original cutout from NASA/IPAC IRSA, aligned to a shared sky grid. Moving objects shift between frames; variable stars change brightness.
        </p>
      )}
      <p className="body muted">
        Half-year motion of the fast movers is smaller than one pixel, so what you see is subtle by design. The paper in Documents explains what can and cannot be concluded.
      </p>
    </>
  );
}

function CustomPanel() {
  return (
    <>
      <p className="crumb mono">PINNED POSITION</p>
      <h1>Your position</h1>
      <p className="body">
        The pin marks the spot you entered. No images are loaded for it: this build carries observations for the five benchmark targets only. Fetching images for any position needs a live archive query, which is not built yet.
      </p>
    </>
  );
}

function TargetPanel({ target, seq, refs, openDocs }: { target: Target; seq?: Sequence; refs: ReturnType<typeof useReferences>; openDocs: () => void }) {
  const copy = COPY[target.id];
  const where = CONSTELLATION[target.id];
  const frames = seq?.frames ?? [];
  const stats = useMemo(() => {
    if (!frames.length) return null;
    const m = frames.map((f) => f.mjd);
    const w = frames.map((f) => f.wavelength_um);
    return { n: frames.length, span: Math.round(Math.max(...m) - Math.min(...m)), wmin: Math.min(...w), wmax: Math.max(...w) };
  }, [frames]);
  const cited = copy?.refs ?? [];
  return (
    <>
      <p className="crumb mono">TARGET / {target.kind.toUpperCase()}</p>
      <h1>{target.name}</h1>
      {copy && <p className="lede" style={{ color: copy.color }}>{copy.lede}</p>}
      {where && (
        <p className="where">
          <Telescope size={14} aria-hidden="true" /> In the constellation {where}
        </p>
      )}
      {stats && (
        <div className="stats">
          <div><strong>{stats.n}</strong><span>FRAMES</span></div>
          <div><strong>{stats.span}</strong><span>DAYS COVERED</span></div>
          <div><strong>{stats.wmin.toFixed(1)}–{stats.wmax.toFixed(1)}</strong><span>µM · BAND RANGE</span></div>
        </div>
      )}
      {seq ? <FramePlayer key={target.id} target={target} seq={seq} /> : <p className="muted">Loading observations…</p>}
      {copy?.body.map((p, k) => (
        <p key={k} className="body">{p}</p>
      ))}
      {copy?.context && (
        <figure className="context">
          <img src={copy.context.src} alt={copy.context.alt} loading="lazy" />
          <figcaption>{copy.context.caption}</figcaption>
        </figure>
      )}
      {copy && <p className="caution"><strong>Read with care.</strong> {copy.caution}</p>}
      {target.id in CONSTELLATION && (
        <div className="gallery">
          <h3 className="mono">MORE VIEWS OF THIS FIELD</h3>
          <figure>
            <a href={`/gallery/${target.id}/wavelengths.png`} target="_blank" rel="noreferrer">
              <img src={`/gallery/${target.id}/wavelengths.png`} alt={`${target.name} field at 1.25, 2.19 and 4.60 micrometres`} loading="lazy" />
            </a>
            <figcaption>The same field in three infrared colours (1.25, 2.19 and 4.60 µm), from the SPHEREx mosaic. A wider 15′ view, combined over time, so it has no single date.</figcaption>
          </figure>
          <figure>
            <a href={`/gallery/${target.id}/dates.png`} target="_blank" rel="noreferrer">
              <img src={`/gallery/${target.id}/dates.png`} alt={`${target.name} field on three observation dates`} loading="lazy" />
            </a>
            <figcaption>Three separate observation dates chosen at closely matched wavelengths. Select an image to open it full size. Target identification in these previews has not been validated.</figcaption>
          </figure>
        </div>
      )}
      <p className="muted small">Frames in one sequence differ in wavelength; compare like with like before reading brightness changes.</p>
      {cited.length > 0 && (
        <div className="cites">
          <h3 className="mono">REFERENCES</h3>
          <ul>
            {cited.map((id) => {
              const r = refs.find((x) => x.id === id);
              return (
                <li key={id}>
                  <button onClick={openDocs} className="link"><span className="mono">{id}</span> {r ? `${r.title} (${r.year})` : ""}</button>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </>
  );
}
