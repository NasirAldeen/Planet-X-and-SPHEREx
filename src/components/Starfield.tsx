import { useEffect, useRef } from "react";
import { useReducedMotion } from "framer-motion";

const STAR_COUNT = 800;

type Props = { speedRef: { current: number }; mouseBoost?: boolean };

/** Stars flying toward the viewer. Speed is read from a ref so callers can ramp it without re-rendering. */
export default function Starfield({ speedRef, mouseBoost = true }: Props) {
  const ref = useRef<HTMLCanvasElement>(null);
  const reduce = useReducedMotion();
  const boostOn = useRef(mouseBoost);
  boostOn.current = mouseBoost;

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    let raf = 0;
    let boost = 0;

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    type Star = { x: number; y: number; z: number; pz: number };
    const spawn = (s: Star, z?: number) => {
      s.x = Math.random() * canvas.width - canvas.width / 2;
      s.y = Math.random() * canvas.height - canvas.height / 2;
      s.z = z ?? Math.random() * canvas.width;
      s.pz = s.z;
      return s;
    };
    resize();
    const stars: Star[] = Array.from({ length: STAR_COUNT }, () => spawn({ x: 0, y: 0, z: 0, pz: 0 }));

    const frame = () => {
      const w = canvas.width,
        h = canvas.height;
      ctx.fillStyle = "rgba(6, 8, 16, 0.22)";
      ctx.fillRect(0, 0, w, h);
      const speed = reduce ? 1 : speedRef.current + (boostOn.current ? boost : 0);
      for (const s of stars) {
        s.z -= speed;
        if (s.z < 1) spawn(s, w);
        else if (s.z > w) spawn(s, 1 + Math.random() * w * 0.15); // moving backwards: re-enter near the viewer
        const sx = (s.x / s.z) * (w / 2) + w / 2;
        const sy = (s.y / s.z) * (h / 2) + h / 2;
        const px = (s.x / s.pz) * (w / 2) + w / 2;
        const py = (s.y / s.pz) * (h / 2) + h / 2;
        s.pz = s.z;
        ctx.beginPath();
        ctx.moveTo(px, py);
        ctx.lineTo(sx, sy);
        ctx.lineWidth = Math.max(0.1, (1 - s.z / w) * 2.5) * 2;
        ctx.strokeStyle = `rgba(232, 236, 255, ${1 - s.z / w})`;
        ctx.stroke();
      }
    };
    const loop = () => {
      frame();
      raf = requestAnimationFrame(loop);
    };
    const onMove = (e: MouseEvent) => {
      const half = window.innerWidth / 2;
      boost = (1 - Math.abs(e.clientX - half) / half) * 14;
    };
    window.addEventListener("resize", resize);
    window.addEventListener("mousemove", onMove);
    if (reduce) for (let i = 0; i < 30; i++) frame();
    else loop();
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
    };
  }, [reduce, speedRef]);

  return <canvas ref={ref} className="fill" aria-hidden="true" />;
}
