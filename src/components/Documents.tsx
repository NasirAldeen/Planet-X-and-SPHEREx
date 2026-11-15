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
        <span className="mono">DOCUMENTS / PROJECT REPORT</span>
        <button className="icon-btn" onClick={onClose} aria-label="Close documents">
          <X size={18} />
        </button>
      </div>

      <article className="docs__body">
        <h1>Seeing real change in SPHEREx sky images</h1>
        <p className="lede">
          The project report behind this tool: what it does, the real archive data it was tested on, and one quality check that changes what a user should conclude.
        </p>
        <p className="links">
          <a href="/docs/SPHEREx_Project_Report_Revised.pdf" target="_blank" rel="noreferrer">
            <FileText size={16} aria-hidden="true" /> Read the full report (PDF, 14 pages)
          </a>
        </p>

        <h2>What the report shows, and what it does not</h2>
        <ul className="plain">
          <li>We verified 20 original SPHEREx files for the five targets: five 102-channel mosaics and 15 dated cutouts, three per target.</li>
          <li>One fixed quality rule accepts the pixel at the requested coordinate in 7 of the 15 dated images and rejects it in 8.</li>
          <li>Every image of the R Draconis and RW Aurigae fields is rejected at its centre. Read without the flags, the RW Aurigae centre pixel would appear to brighten by about 90 percent between two dates. That is not a measurement.</li>
          <li>A wavelength channel is not an observing date. The mosaics show colour and only the dated cutouts show time.</li>
          <li>The five objects have not been identified in the images. No motion, brightness change or discovery is claimed.</li>
        </ul>

        <h2>Image credits</h2>
        <p>
          The sky frames in the player are original SPHEREx observations (NASA/JPL-Caltech), served by the NASA/IPAC Infrared Science Archive. They are a separate set from the 20 files analysed in the report. The image figures below are rendered from the report's SPHEREx files, and the last figure is a chart drawn from published measurements. The rocket, the light-speed tunnel, the Milky Way band and the grey dust on the map are graphics, not telescope data.
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
