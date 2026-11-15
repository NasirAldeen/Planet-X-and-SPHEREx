import { useEffect, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { motion } from "framer-motion";
import * as THREE from "three";
import ShipModel from "./ShipModel";

type Stage = "launch" | "warp" | "return";

type Props = {
  /** "launch": countdown then ignition. "warp": at light speed. "return": flying home. */
  stage: Stage;
  /** Called once the launch countdown reaches ignition. */
  onIgnition?: () => void;
};

/** The ship seen from a chase camera just behind and above it. */
function Ship({ stage, ignited }: { stage: Stage; ignited: boolean }) {
  const g = useRef<THREE.Group>(null);
  const spin = useRef<THREE.Group>(null);
  const light = useRef<THREE.PointLight>(null);
  const thrust = useRef(0.35);
  const z = useRef(0);

  useFrame((s, dt) => {
    if (!g.current || !spin.current) return;
    const t = s.clock.elapsedTime;
    const burning = stage !== "launch" || ignited;
    const k = Math.min(1, dt * 2);

    // engine: idle glow before ignition, full burn after
    thrust.current += ((stage === "warp" ? 3 : burning ? 2.3 : 0.35) - thrust.current) * k;
    if (light.current) light.current.intensity = thrust.current * 14;

    // the ship surges ahead of the camera at ignition, then the camera settles in behind it
    const targetZ = stage === "warp" ? -1.6 : stage === "return" ? -1 : ignited ? -2.6 : 0;
    z.current += (targetZ - z.current) * Math.min(1, dt * 1.4);

    const rattle = burning ? 0.035 : 0.008;
    g.current.position.set(
      Math.sin(t * 0.7) * 0.25 + (Math.random() - 0.5) * rattle,
      -0.55 + Math.sin(t * 1.3) * 0.1 + (Math.random() - 0.5) * rattle,
      z.current
    );
    // nose away from the camera on the way out, toward it on the way home; bank gently with the drift
    const pitch = stage === "return" ? Math.PI / 2 : -Math.PI / 2;
    g.current.rotation.set(pitch + Math.sin(t * 0.9) * 0.04, 0, Math.cos(t * 0.7) * 0.18);
    // roll around its own long axis: slow before launch, faster at speed
    spin.current.rotation.y += dt * (stage === "warp" ? 1.6 : burning ? 0.9 : 0.25);
  });

  return (
    <group ref={g}>
      <group ref={spin}>
        <ShipModel thrust={thrust} />
      </group>
      <pointLight ref={light} position={[0, -1.6, 0]} color="#ff9a5c" distance={8} />
    </group>
  );
}

/**
 * Third-person launch view: a chase camera follows the ship while the stars (or the light-speed
 * tunnel) are drawn by whatever sits behind this layer. Keeps the countdown, the speed readout,
 * the heading and the engine shake.
 */
export default function Chase({ stage, onIgnition }: Props) {
  const [count, setCount] = useState(stage === "launch" ? 3 : 0);
  const [speed, setSpeed] = useState(0);
  const raf = useRef(0);

  // countdown 3 · 2 · 1 · ignition
  useEffect(() => {
    if (stage !== "launch") return;
    setCount(3);
    const ids = [
      window.setTimeout(() => setCount(2), 800),
      window.setTimeout(() => setCount(1), 1600),
      window.setTimeout(() => {
        setCount(0);
        onIgnition?.();
      }, 2400),
    ];
    return () => ids.forEach(clearTimeout);
  }, [stage, onIgnition]);

  // speed readout rises on the way out, falls on the way back
  useEffect(() => {
    const t0 = performance.now();
    const tick = (now: number) => {
      const t = (now - t0) / 1000;
      if (stage === "launch") setSpeed(count === 0 ? Math.min(40000, t * 16000) : 0);
      else if (stage === "warp") setSpeed(299792 * Math.min(1, t / 2.5));
      else setSpeed(299792 * Math.max(0, 1 - t / 5));
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [stage, count]);

  const ignited = stage === "launch" && count === 0;
  const shake = stage === "launch" ? (ignited ? 4 : count === 1 ? 1.5 : 0.5) : 1.2;
  const label = stage === "return" ? "RETURNING" : stage === "warp" ? "LIGHT SPEED" : count > 0 ? "PRE-LAUNCH" : "IGNITION";
  const readout = stage === "launch" ? `${Math.round(speed).toLocaleString()} km/h` : `${Math.round(speed).toLocaleString()} km/s`;

  return (
    <div className="chase" aria-hidden="true">
      <motion.div
        className="chase__view"
        animate={{ x: [0, shake, -shake, shake * 0.6, 0], y: [0, -shake * 0.6, shake, -shake * 0.4, 0] }}
        transition={{ duration: 0.18, repeat: Infinity, ease: "linear" }}
      >
        <Canvas className="fill" camera={{ position: [0, 1.5, 6.5], fov: 50 }} gl={{ alpha: true }} onCreated={({ camera }) => camera.lookAt(0, 0, -2)}>
          <ambientLight intensity={0.55} />
          <directionalLight position={[4, 6, 5]} intensity={2.4} />
          <Ship stage={stage} ignited={ignited} />
        </Canvas>
      </motion.div>

      <div className="hud">
        <div className="gauge">
          <span className="mono">{label}</span>
          <strong>{readout}</strong>
        </div>
        <div className="gauge gauge--center">
          {stage === "launch" && count > 0 ? <strong className="count">{count}</strong> : <span className="mono">SPHEREx VOYAGE</span>}
        </div>
        <div className="gauge gauge--right">
          <span className="mono">HEADING</span>
          <strong>{stage === "return" ? "EARTH" : "INFRARED SKY"}</strong>
        </div>
      </div>
    </div>
  );
}
