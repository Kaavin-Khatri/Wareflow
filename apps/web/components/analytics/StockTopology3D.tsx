"use client";

import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float } from "@react-three/drei";
import * as THREE from "three";

interface WarehouseNodeData {
  name: string;
  value: number;
  color: string;
  position: [number, number, number];
}

const DEFAULT_NODES: WarehouseNodeData[] = [
  { name: "Central Hub", value: 1250000, color: "#8b5cf6", position: [0, 0.2, 0] },
  { name: "North Depo", value: 450000, color: "#38bdf8", position: [-1.8, -0.6, 0.4] },
  { name: "South Port", value: 380000, color: "#10b981", position: [1.8, -0.5, -0.3] },
  { name: "West Depot", value: 210000, color: "#f59e0b", position: [0.8, 1.2, 0.6] },
];

function HolographicNodesGroup() {
  const groupRef = useRef<THREE.Group>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  const coreRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    const { pointer } = state;

    if (groupRef.current) {
      // Dynamic cursor parallax rotation
      groupRef.current.rotation.y = THREE.MathUtils.lerp(
        groupRef.current.rotation.y,
        pointer.x * 0.5 + time * 0.1,
        0.05,
      );
      groupRef.current.rotation.x = THREE.MathUtils.lerp(
        groupRef.current.rotation.x,
        -pointer.y * 0.4,
        0.05,
      );
    }

    if (ringRef.current) {
      ringRef.current.rotation.z = time * 0.15;
      ringRef.current.rotation.x = 1.1 + Math.sin(time * 0.5) * 0.1;
    }

    if (coreRef.current) {
      coreRef.current.rotation.y = -time * 0.3;
      coreRef.current.rotation.x = time * 0.2;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Central Valuation Core */}
      <Float speed={2} rotationIntensity={0.6} floatIntensity={0.8}>
        <mesh ref={coreRef} position={[0, 0, 0]}>
          <icosahedronGeometry args={[1.1, 1]} />
          <meshPhysicalMaterial
            color="#8b5cf6"
            roughness={0.1}
            metalness={0.8}
            transmission={0.7}
            thickness={1.5}
            transparent
            opacity={0.85}
          />
          <lineSegments>
            <edgesGeometry args={[new THREE.IcosahedronGeometry(1.105, 1)]} />
            <lineBasicMaterial color="#c084fc" linewidth={1.5} />
          </lineSegments>
        </mesh>
      </Float>

      {/* Orbital Glowing Gyro Ring */}
      <mesh ref={ringRef} position={[0, 0, 0]}>
        <torusGeometry args={[2.5, 0.02, 16, 100]} />
        <meshStandardMaterial
          color="#a855f7"
          emissive="#a855f7"
          emissiveIntensity={0.6}
          wireframe
        />
      </mesh>

      {/* Satellite Warehouse Nodes */}
      {DEFAULT_NODES.slice(1).map((node, i) => (
        <group key={node.name} position={node.position}>
          <Float speed={1.5 + i * 0.4} rotationIntensity={0.4} floatIntensity={0.6}>
            <mesh scale={0.45}>
              <boxGeometry args={[1, 1, 1]} />
              <meshStandardMaterial color={node.color} roughness={0.2} metalness={0.7} />
              <lineSegments>
                <edgesGeometry args={[new THREE.BoxGeometry(1.01, 1.01, 1.01)]} />
                <lineBasicMaterial color="#ffffff" />
              </lineSegments>
            </mesh>
          </Float>
        </group>
      ))}

      {/* Grid Reference Floor */}
      <gridHelper args={[8, 12, "#8b5cf6", "rgba(255,255,255,0.06)"]} position={[0, -1.8, 0]} />
    </group>
  );
}

export function StockTopology3D() {
  return (
    <div
      className="relative w-full h-[220px] rounded-3xl overflow-hidden border border-white/10 bg-[var(--glass-bg)] backdrop-blur-2xl"
      aria-label="3D Inventory Network Topology"
    >
      <div className="absolute top-3 left-4 z-10 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-[11px] font-mono font-bold tracking-wider uppercase text-white/70">
          3D Multi-Warehouse Topology Core
        </span>
      </div>

      <Canvas
        camera={{ position: [0, 1, 5], fov: 45 }}
        dpr={[1, 1.5]}
        gl={{ powerPreference: "high-performance", antialias: true, alpha: true }}
      >
        <ambientLight intensity={0.8} />
        <directionalLight position={[4, 6, 4]} intensity={1.5} color="#ffffff" />
        <pointLight position={[-3, -2, -2]} intensity={2} color="#8b5cf6" />
        <pointLight position={[3, 3, 2]} intensity={1.5} color="#38bdf8" />
        <HolographicNodesGroup />
      </Canvas>
    </div>
  );
}

export default StockTopology3D;
