import { useRef, type MutableRefObject } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

/**
 * The ship, modelled from primitives. Its long axis is +Y (nose up).
 * `thrust` scales the exhaust flame: about 0.3 is an idle glow, 1 is cruising, 3 is full burn.
 */
export default function ShipModel({ thrust }: { thrust?: MutableRefObject<number> }) {
  const flame = useRef<THREE.Group>(null);
  useFrame((s) => {
    if (!flame.current) return;
    const k = thrust?.current ?? 1;
    const flicker = 1 + Math.sin(s.clock.elapsedTime * 40) * 0.2;
    flame.current.scale.set(0.7 + k * 0.3, k * flicker, 0.7 + k * 0.3);
  });
  return (
    <group>
      <mesh>
        <cylinderGeometry args={[0.32, 0.32, 1.6, 24]} />
        <meshStandardMaterial color="#e8ecff" metalness={0.4} roughness={0.35} />
      </mesh>
      <mesh position={[0, 1.1, 0]}>
        <coneGeometry args={[0.32, 0.7, 24]} />
        <meshStandardMaterial color="#ff7a45" metalness={0.3} roughness={0.4} />
      </mesh>
      <mesh position={[0, 0.35, 0.3]}>
        <sphereGeometry args={[0.13, 16, 16]} />
        <meshStandardMaterial color="#7fa2ff" emissive="#3b6cff" emissiveIntensity={0.9} />
      </mesh>
      {[0, 1, 2].map((i) => (
        <mesh key={i} rotation={[0, (i * Math.PI * 2) / 3, 0]} position={[0, -0.7, 0]}>
          <boxGeometry args={[0.9, 0.55, 0.06]} />
          <meshStandardMaterial color="#ff7a45" metalness={0.3} roughness={0.5} />
        </mesh>
      ))}
      <mesh position={[0, -0.9, 0]}>
        <cylinderGeometry args={[0.2, 0.28, 0.2, 16]} />
        <meshStandardMaterial color="#3a4268" />
      </mesh>
      {/* exhaust: anchored at the nozzle so it grows backwards only */}
      <group ref={flame} position={[0, -1, 0]}>
        <mesh position={[0, -0.6, 0]} rotation={[Math.PI, 0, 0]}>
          <coneGeometry args={[0.24, 1.2, 16]} />
          <meshBasicMaterial color="#ffb070" transparent opacity={0.9} />
        </mesh>
        <mesh position={[0, -0.4, 0]} rotation={[Math.PI, 0, 0]}>
          <coneGeometry args={[0.13, 0.8, 16]} />
          <meshBasicMaterial color="#ffffff" />
        </mesh>
      </group>
    </group>
  );
}
