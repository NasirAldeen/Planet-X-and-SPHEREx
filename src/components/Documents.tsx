import { useEffect, useState } from "react";
import { ExternalLink, FileText, X } from "lucide-react";
import { FIGURES } from "../lib/content";

export type Reference = {
  id: string;
  origin: string;
  title: string;
  authors: string;
  year: number;
  venue: string;
  doi: string | null;
  url: string;
  summary: string;
  use: string;
  limits: string;
};

export function useReferences() {
  const [refs, setRefs] = useState<Reference[]>([]);
  useEffect(() => {
    fetch("/data/references.json")
      .then((r) => r.json())
      .then(setRefs)
      .catch(() => setRefs([]));
  }, []);
  return refs;
}

export default function Documents({ refs, onClose }: { refs: Reference[]; onClose: () => void }) {
  return (
    <div className="docs" role="dialog" aria-modal="true" aria-label="Documents and references">
      <div className="docs__bar">
        <span className="mono">DOCUMENTS / RESEARCH PAPER</span>
        <button className="icon-btn" onClick={onClose} aria-label="Close documents">
          <X size={18} />
        </button>
      </div>

      <article className="docs__body">
        <h1>How we read changes in SPHEREx images</h1>
        <p className="lede">
          A methods paper behind this tool: five benchmark objects, thirteen numbered equations, and what can and cannot be concluded from a handful of infrared frames.
        </p>
        <p className="links">
          <a href="/docs/SPHEREx_Research_Paper.pdf" target="_blank" rel="noreferrer">
            <FileText size={16} aria-hidden="true" /> Read the full paper (PDF, 16 pages)
          </a>
        </p>

        <h2>What the paper claims, and what it does not</h2>
        <ul className="plain">
          <li>Half-year motion of the three moving benchmarks is under one SPHEREx pixel, so alignment matters more than raw image quality.</li>
          <li>The two original R Draconis cutouts have flagged central pixels. They demonstrate data handling, not a brightness measurement.</li>
          <li>No new planet, no new pulsation period and no calibrated SPHEREx light curve is claimed.</li>
          <li>A frame shown here is always an original archive observation. Anything else is labelled as a projection.</li>
        </ul>

        <h2>Image credits</h2>
        <p>
          The sky frames in the player are original SPHEREx observations (NASA/JPL-Caltech), served by the NASA/IPAC Infrared Science Archive. Figure 6 below is rendered from two of those files. The other figures are charts drawn for the paper from published measurements. The rocket, the light-speed tunnel, the Milky Way band and the grey dust on the map are graphics, not telescope data.
        </p>

        <h2>Figures</h2>
        <div className="figs">
          {FIGURES.map((f) => (
            <figure key={f.file}>
              <img src={`/docs/figures/${f.file}`} alt={f.title} loading="lazy" />
              <figcaption>{f.title}</figcaption>
            </figure>
          ))}
        </div>

        <h2>References</h2>
        <ol className="refs">
          {refs.map((r) => (
            <li key={r.id} id={`ref-${r.id}`}>
              <span className="mono ref-id">{r.id}</span>
              <div>
                <strong>{r.title}</strong>
                <div className="muted">
                  {r.authors} · {r.year} · {r.venue}
                </div>
                <p>{r.summary}</p>
                <p className="muted">
                  <em>Limits.</em> {r.limits}
                </p>
                <a href={r.doi ? `https://doi.org/${r.doi}` : r.url} target="_blank" rel="noreferrer">
                  Open source <ExternalLink size={13} aria-hidden="true" />
                </a>
              </div>
            </li>
          ))}
        </ol>
      </article>
    </div>
  );
}
