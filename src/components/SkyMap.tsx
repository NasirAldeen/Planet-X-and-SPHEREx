import { useEffect, useMemo, useRef, type MutableRefObject } from "react";
import { Canvas, useFrame, useThree, type ThreeEvent } from "@react-three/fiber";
import { Html, Line } from "@react-three/drei";
import * as THREE from "three";
import { radecToVec3, type Target } from "../lib/sky";
import { COPY } from "../lib/content";
import ShipModel from "./ShipModel";

export type View = "globe" | "reference";

type Props = {
  targets: Target[];
  selectedId: string | null;
  showNames: boolean;
  view: View;
  onSelect: (id: string | null) => void;
};

const DEG = Math.PI / 180;
const REF_DIST = 30; // camera distance from the centre in reference (outside) view

/**
 * One rig for both views. The camera always looks along (yaw, pitch); in globe view it sits at the
 * centre, in reference view it is pulled straight back along its own line of sight so the whole
 * sphere is in front of it. Stepping back and diving in are the same move in opposite directions.
 */
function Rig({
  selected,
  view,
  dragPx,
  dist,
}: {
  selected: Target | null;
  view: View;
  dragPx: MutableRefObject<number>;
  dist: MutableRefObject<number>;
}) {
  const { camera, gl } = useThree();
  const yaw = useRef(0);
  const pitch = useRef(0.1);
  const drag = useRef<{ x: number; y: number } | null>(null);
  const idle = useRef(0);
  const gliding = useRef(false);
  const fwd = useRef(new THREE.Vector3());

  // start a glide whenever the selection or the view changes; a drag cancels it
  useEffect(() => {
    gliding.current = !!selected;
  }, [selected?.id, view]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const el = gl.domElement;
    const down = (e: PointerEvent) => {
      drag.current = { x: e.clientX, y: e.clientY };
      dragPx.current = 0;
      gliding.current = false;
    };
    const move = (e: PointerEvent) => {
      if (!drag.current) return;
      const k = 0.0045;
      dragPx.current += Math.abs(e.clientX - drag.current.x) + Math.abs(e.clientY - drag.current.y);
      yaw.current += (e.clientX - drag.current.x) * k;
      pitch.current = THREE.MathUtils.clamp(pitch.current + (e.clientY - drag.current.y) * k, -1.35, 1.35);
      drag.current = { x: e.clientX, y: e.clientY };
      idle.current = 0;
    };
    const up = () => {
      drag.current = null;
    };
    el.addEventListener("pointerdown", down);
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
    return () => {
      el.removeEventListener("pointerdown", down);
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
  }, [gl, dragPx]);

  useFrame((_, dt) => {
    idle.current += dt;
    const outside = view === "reference";
    if (selected && gliding.current && !drag.current) {
      // inside: look straight at the target. outside: stand on the target's side of the sphere.
      const ty = selected.ra * DEG + (outside ? Math.PI : 0);
      const tp = selected.dec * DEG * (outside ? -1 : 1);
      let d = ((ty - yaw.current + Math.PI) % (Math.PI * 2)) - Math.PI;
      if (d < -Math.PI) d += Math.PI * 2;
      const k = Math.min(1, dt * 2.5);
      yaw.current += d * k;
      pitch.current += (tp - pitch.current) * k;
      if (Math.abs(d) < 0.002 && Math.abs(tp - pitch.current) < 0.002) gliding.current = false;
    } else if (!selected && !drag.current && idle.current > 1.5) {
      yaw.current += dt * (outside ? 0.06 : 0.035); // slow spin
    }
    dist.current += ((outside ? REF_DIST : 0) - dist.current) * Math.min(1, dt * 2.2);
    camera.rotation.set(pitch.current, yaw.current, 0, "YXZ");
    camera.getWorldDirection(fwd.current);
    camera.position.copy(fwd.current).multiplyScalar(-dist.current);
  });
  return null;
}

function Grid() {
  const lines = useMemo(() => {
    const out: THREE.Vector3[][] = [];
    for (const dec of [-60, -30, 0, 30, 60]) {
      const pts: THREE.Vector3[] = [];
      for (let ra = 0; ra <= 360; ra += 6) pts.push(radecToVec3(ra, dec, 9.8));
      out.push(pts);
    }
    for (let ra = 0; ra < 360; ra += 30) {
      const pts: THREE.Vector3[] = [];
      for (let dec = -85; dec <= 85; dec += 5) pts.push(radecToVec3(ra, dec, 9.8));
      out.push(pts);
    }
    return out;
  }, []);
  return (
    <>
      {lines.map((pts, i) => (
        <Line key={i} points={pts} color="#2a3566" lineWidth={1} transparent opacity={0.5} />
      ))}
    </>
  );
}

/** Decorative dust only. These points are random and are NOT a star catalogue. */
function Dust() {
  const geo = useMemo(() => {
    const n = 700;
    const pos = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const v = new THREE.Vector3().randomDirection().multiplyScalar(11);
      pos.set([v.x, v.y, v.z], i * 3);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    return g;
  }, []);
  return (
    <points geometry={geo}>
      <pointsMaterial color="#aab3d9" size={0.035} sizeAttenuation transparent opacity={0.4} />
    </points>
  );
}

function gauss() {
  return Math.sqrt(-2 * Math.log(1 - Math.random())) * Math.cos(2 * Math.PI * Math.random());
}

/**
 * The Milky Way as a band of generated points. Its PLACEMENT is real: the band follows the galactic
 * plane (north galactic pole RA 192.859°, Dec +27.128°; centre RA 266.405°, Dec −28.936°, J2000) and
 * thickens toward the galactic centre. The individual points are random, not catalogue stars.
 */
function MilkyWay() {
  const geo = useMemo(() => {
    const eq = (ra: number, dec: number) =>
      new THREE.Vector3(Math.cos(dec * DEG) * Math.cos(ra * DEG), Math.cos(dec * DEG) * Math.sin(ra * DEG), Math.sin(dec * DEG));
    const z = eq(192.85948, 27.12825);
    const x = eq(266.40499, -28.93617);
    const y = new THREE.Vector3().crossVectors(z, x);
    const n = 9000;
    const pos = new Float32Array(n * 3);
    const col = new Float32Array(n * 3);
    const warm = new THREE.Color("#ffd9a8");
    const cool = new THREE.Color("#b9c6ff");
    const c = new THREE.Color();
    for (let i = 0; i < n; i++) {
      const l = Math.random() < 0.4 ? gauss() * 28 : Math.random() * 360 - 180; // degrees from the centre
      const core = Math.exp(-((l / 30) ** 2));
      const b = gauss() * (3.5 + 9 * core);
      const cl = Math.cos(l * DEG),
        sl = Math.sin(l * DEG),
        cb = Math.cos(b * DEG),
        sb = Math.sin(b * DEG);
      const e = new THREE.Vector3()
        .addScaledVector(x, cb * cl)
        .addScaledVector(y, cb * sl)
        .addScaledVector(z, sb);
      // equatorial (X, Y, Z) → scene axes used by radecToVec3: (−Y, Z, −X)
      const r = 10.4 + Math.random() * 0.5;
      pos.set([-e.y * r, e.z * r, -e.x * r], i * 3);
      c.copy(cool).lerp(warm, core).multiplyScalar(0.35 + Math.random() * 0.65);
      col.set([c.r, c.g, c.b], i * 3);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    g.setAttribute("color", new THREE.BufferAttribute(col, 3));
    return g;
  }, []);
  return (
    <points geometry={geo}>
      <pointsMaterial vertexColors size={0.06} sizeAttenuation transparent opacity={0.55} blending={THREE.AdditiveBlending} depthWrite={false} />
    </points>
  );
}

/** Decorative dotted links between the points, drifting slowly. They carry no meaning. */
function Links({ targets }: { targets: Target[] }) {
  // drei's <Line> is a Line2; only its material's dashOffset is touched here
  const refs = useRef<({ material: { dashOffset: number } } | null)[]>([]);
  const pairs = useMemo(() => {
    const pts = targets.map((t) => radecToVec3(t.ra, t.dec, 10));
    return pts.length < 2 ? [] : pts.map((p, i) => [p, pts[(i + 1) % pts.length]] as [THREE.Vector3, THREE.Vector3]);
  }, [targets]);
  useFrame((_, dt) => {
    for (const l of refs.current) if (l) l.material.dashOffset -= dt * 0.35;
  });
  return (
    <>
      {pairs.map((p, i) => (
        <Line
          key={i}
          ref={(l) => {
            refs.current[i] = l as unknown as { material: { dashOffset: number } } | null;
          }}
          points={p}
          color="#7fa2ff"
          lineWidth={1.5}
          dashed
          dashSize={0.25}
          gapSize={0.35}
          transparent
          opacity={0.7}
        />
      ))}
    </>
  );
}

/** The ship idling at the centre of the sphere, waiting to be launched back into the sky. */
function WaitingShip({ dist }: { dist: MutableRefObject<number> }) {
  const g = useRef<THREE.Group>(null);
  useFrame((s, dt) => {
    if (!g.current) return;
    g.current.visible = dist.current > 6; // hidden while the camera is inside it
    g.current.rotation.y += dt * 0.6;
    g.current.rotation.z = 0.4 + Math.sin(s.clock.elapsedTime * 0.5) * 0.12;
  });
  return (
    <group ref={g} scale={1.7} visible={false}>
      <ShipModel />
    </group>
  );
}

function Dot({
  target,
  selected,
  showName,
  big,
  onPick,
}: {
  target: Target;
  selected: boolean;
  showName: boolean;
  big: boolean;
  onPick: (id: string) => void;
}) {
  const color = COPY[target.id]?.color ?? "#ffffff";
  const pos = useMemo(() => radecToVec3(target.ra, target.dec, 10), [target]);
  const ring = useRef<THREE.Mesh>(null);
  const hover = useRef(false);

  useFrame((s) => {
    if (!ring.current) return;
    const pulse = 1 + Math.sin(s.clock.elapsedTime * 2.2 + target.ra) * 0.12;
    ring.current.scale.setScalar((selected ? 1.9 : hover.current ? 1.6 : 1.25) * pulse);
    ring.current.quaternion.copy(s.camera.quaternion); // always face the viewer
  });

  return (
    <group position={pos} scale={big ? 2.4 : 1}>
      <mesh>
        <sphereGeometry args={[0.2, 20, 20]} />
        <meshBasicMaterial color={color} />
      </mesh>
      <mesh ref={ring}>
        <ringGeometry args={[0.3, 0.34, 40]} />
        <meshBasicMaterial color={color} transparent opacity={0.8} side={THREE.DoubleSide} />
      </mesh>
      {/* the only clickable part: a generous invisible sphere. Clicking always selects, never toggles. */}
      <mesh
        onClick={(e: ThreeEvent<MouseEvent>) => {
          e.stopPropagation();
          if (e.delta > 6) return; // that was a drag
          onPick(target.id);
        }}
        onPointerOver={() => {
          hover.current = true;
          document.body.style.cursor = "pointer";
        }}
        onPointerOut={() => {
          hover.current = false;
          document.body.style.cursor = "";
        }}
      >
        <sphereGeometry args={[0.7, 8, 8]} />
        <meshBasicMaterial transparent opacity={0} depthWrite={false} />
      </mesh>
      {(showName || selected) && (
        <Html center position={[0, -0.75, 0]} style={{ pointerEvents: "none" }}>
          <span className={`dot-label${selected ? " is-selected" : ""}`}>{target.name}</span>
        </Html>
      )}
    </group>
  );
}

export default function SkyMap({ targets, selectedId, showNames, view, onSelect }: Props) {
  const dragPx = useRef(0);
  const dist = useRef(0);
  const lastPick = useRef(0);
  const selected = targets.find((t) => t.id === selectedId) ?? null;
  const pick = (id: string) => {
    lastPick.current = performance.now();
    onSelect(id);
  };
  return (
    <Canvas
      className="fill"
      camera={{ position: [0, 0, 0], fov: 62, near: 0.1, far: 120 }}
      onPointerMissed={() => {
        // empty sky closes the selection, but never as a side effect of a drag or of picking a point
        if (dragPx.current < 6 && performance.now() - lastPick.current > 400) onSelect(null);
      }}
      gl={{ antialias: true }}
    >
      <color attach="background" args={["#060810"]} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[6, 8, 5]} intensity={2.2} />
      <Rig selected={selected} view={view} dragPx={dragPx} dist={dist} />
      <Grid />
      <Dust />
      <MilkyWay />
      {view === "reference" && <Links targets={targets} />}
      <WaitingShip dist={dist} />
      {targets.map((t) => (
        <Dot key={t.id} target={t} selected={t.id === selectedId} showName={showNames} big={view === "reference"} onPick={pick} />
      ))}
    </Canvas>
  );
}
