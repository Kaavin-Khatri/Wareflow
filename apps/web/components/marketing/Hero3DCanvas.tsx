"use client";

import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float } from "@react-three/drei";
import * as THREE from "three";

function FloatingCratesGroup() {
  const groupRef = useRef<THREE.Group>(null);
  const cube1Ref = useRef<THREE.Mesh>(null);
  const cube2Ref = useRef<THREE.Mesh>(null);
  const cube3Ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    const { pointer } = state;

    if (groupRef.current) {
      // Subtle mouse parallax tilt
      groupRef.current.rotation.y = THREE.MathUtils.lerp(
        groupRef.current.rotation.y,
        pointer.x * 0.4 + time * 0.15,
        0.05,
      );
      groupRef.current.rotation.x = THREE.MathUtils.lerp(
        groupRef.current.rotation.x,
        -pointer.y * 0.3,
        0.05,
      );
    }

    if (cube1Ref.current) {
      cube1Ref.current.rotation.x = time * 0.2;
      cube1Ref.current.rotation.z = time * 0.1;
    }
    if (cube2Ref.current) {
      cube2Ref.current.rotation.y = -time * 0.25;
      cube2Ref.current.position.y = 0.8 + Math.sin(time * 1.5) * 0.15;
    }
    if (cube3Ref.current) {
      cube3Ref.current.rotation.z = time * 0.18;
      cube3Ref.current.position.y = -0.9 + Math.cos(time * 1.2) * 0.15;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Central Hero Crate / Node */}
      <Float speed={2} rotationIntensity={0.5} floatIntensity={0.8}>
        <mesh ref={cube1Ref} position={[0, 0, 0]}>
          <boxGeometry args={[1.6, 1.6, 1.6]} />
          <meshPhysicalMaterial
            color="#8b5cf6"
            roughness={0.15}
            metalness={0.8}
            transmission={0.6}
            thickness={1.2}
            transparent
            opacity={0.85}
            reflectivity={0.9}
          />
          {/* Wireframe Outline for High-Tech Specular Edge */}
          <lineSegments>
            <edgesGeometry args={[new THREE.BoxGeometry(1.605, 1.605, 1.605)]} />
            <lineBasicMaterial color="#c084fc" linewidth={1.5} />
          </lineSegments>
        </mesh>
      </Float>

      {/* Satellite Top Node */}
      <mesh ref={cube2Ref} position={[1.4, 0.8, -0.4]} scale={0.65}>
        <boxGeometry args={[1.2, 1.2, 1.2]} />
        <meshStandardMaterial color="#10b981" roughness={0.3} metalness={0.7} />
        <lineSegments>
          <edgesGeometry args={[new THREE.BoxGeometry(1.205, 1.205, 1.205)]} />
          <lineBasicMaterial color="#6ee7b7" />
        </lineSegments>
      </mesh>

      {/* Satellite Bottom Node */}
      <mesh ref={cube3Ref} position={[-1.3, -0.9, 0.4]} scale={0.55}>
        <octahedronGeometry args={[1.1]} />
        <meshStandardMaterial color="#38bdf8" roughness={0.2} metalness={0.9} />
        <lineSegments>
          <edgesGeometry args={[new THREE.OctahedronGeometry(1.105)]} />
          <lineBasicMaterial color="#bae6fd" />
        </lineSegments>
      </mesh>

      {/* Grid Floor Plane */}
      <gridHelper args={[10, 16, "#7c3aed", "rgba(255,255,255,0.08)"]} position={[0, -2.2, 0]} />
    </group>
  );
}

export function Hero3DCanvas() {
  return (
    <div
      className="relative w-full h-[380px] sm:h-[480px] rounded-3xl overflow-hidden border border-[var(--glass-border)] bg-[var(--glass-bg)] backdrop-blur-2xl"
      aria-label="Interactive 3D Wholesale Inventory Model"
    >
      <Canvas
        camera={{ position: [0, 0, 5], fov: 45 }}
        dpr={[1, 1.5]}
        gl={{ powerPreference: "high-performance", antialias: true, alpha: true }}
      >
        <ambientLight intensity={0.7} />
        <directionalLight position={[5, 8, 5]} intensity={1.5} color="#ffffff" />
        <pointLight position={[-4, -3, -2]} intensity={2} color="#8b5cf6" />
        <pointLight position={[3, 4, 2]} intensity={1.2} color="#10b981" />
        <FloatingCratesGroup />
      </Canvas>
    </div>
  );
}

export default Hero3DCanvas;
