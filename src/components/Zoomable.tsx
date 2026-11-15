import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

/**
 * An image that expands inside the site instead of opening a new tab.
 * Close with the button, a click on the backdrop, or Escape.
 */
export default function Zoomable({ src, alt, caption }: { src: string; alt: string; caption?: string }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [open]);

  return (
    <>
      <button type="button" className="zoomable" onClick={() => setOpen(true)} aria-label={`Expand image: ${alt}`}>
        <img src={src} alt={alt} loading="lazy" />
      </button>
      {open &&
        createPortal(
          <div className="lightbox" role="dialog" aria-modal="true" aria-label={alt} onClick={() => setOpen(false)}>
            <button type="button" className="lightbox__close" onClick={() => setOpen(false)} autoFocus>
              <X size={18} aria-hidden="true" /> Back to the site
            </button>
            <img src={src} alt={alt} onClick={(e) => e.stopPropagation()} />
            {caption && <p onClick={(e) => e.stopPropagation()}>{caption}</p>}
          </div>,
          document.body
        )}
    </>
  );
}
