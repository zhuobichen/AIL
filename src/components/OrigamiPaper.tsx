import React, { useRef, useMemo } from 'react';
import { ThreeEvent, useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useOrigamiStore } from '../store/useOrigamiStore';
import { getPaperBumpMap } from '../utils/textureGen';
import { playPaperSound } from '../utils/audio';
import { useSpring } from '@react-spring/three';

export function OrigamiPaper() {
  const meshRef = useRef<THREE.Mesh>(null);
  
  const { 
    mode,
    folds, addFold, 
    paperColor,
    dragStartPoint, dragCurrentPoint,
    setDragStartPoint, setDragCurrentPoint,
    snapToGrid
  } = useOrigamiStore();

  const paperBumpMap = useMemo(() => getPaperBumpMap(), []);

  // Generate a high-res box once (thickness = 0.02)
  const baseGeometry = useMemo(() => {
    const geom = new THREE.BoxGeometry(10, 10, 0.02, 64, 64, 2);
    return geom;
  }, []);

  const basePositions = useMemo(() => {
    return baseGeometry.attributes.position.array.slice();
  }, [baseGeometry]);

  const baseNormals = useMemo(() => {
    return baseGeometry.attributes.normal.array.slice();
  }, [baseGeometry]);

  // We need to keep track of a history of folds for smooth undo
  // The store's "folds" drops the undone fold immediately, so we keep a local mirrored copy 
  // that animates back to 0 before actually disappearing, but for simplicity we'll just 
  // animate the last active fold smoothly and let undo instantly snap (or we can animate undo by adding a state in store).
  // Currently the useSpring handles changes to lastFold.angle automatically!
  // Calculate temporary drag fold
  const tempFold = useMemo(() => {
    if (!dragStartPoint || !dragCurrentPoint) return null;
    if (dragStartPoint.distanceTo(dragCurrentPoint) < 0.1) return null;

    const axisPoint = new THREE.Vector3().addVectors(dragStartPoint, dragCurrentPoint).multiplyScalar(0.5);
    
    // Perpendicular vector in the XY plane
    const dir = new THREE.Vector3().subVectors(dragCurrentPoint, dragStartPoint);
    const up = new THREE.Vector3(0, 0, 1);
    const axisDir = new THREE.Vector3().crossVectors(dir, up).normalize();
    
    // The side containing dragStartPoint should fold over
    const foldSideNormal = new THREE.Vector3().subVectors(dragStartPoint, axisPoint).normalize();
    
    // Angle interpolation based on distance
    // Let's make angle exactly 178 degrees so it fully folds to the target
    // Wait, if we want it to follow exactly, rotating by 180 degrees around the perpendicular bisector
    // maps dragStart to dragCurrent perfectly.
    return {
      id: 'temp',
      axisPoint,
      axisDir,
      foldSideNormal,
      angle: (178 * Math.PI) / 180
    };
  }, [dragStartPoint, dragCurrentPoint]);

  const lastFold = folds[folds.length - 1];
  
  // Use Spring to animate the very last fold angle smoothly
  const { springAngle } = useSpring({
    springAngle: lastFold ? lastFold.angle : 0,
    config: { mass: 1, tension: 170, friction: 26 },
  });

  // Apply folds in useFrame for continuous smooth animation
  useFrame(() => {
    if (!meshRef.current) return;
    const geom = meshRef.current.geometry as THREE.BufferGeometry;
    if (!geom) return;

    const posAttr = geom.attributes.position as THREE.BufferAttribute;
    const normAttr = geom.attributes.normal as THREE.BufferAttribute;
    
    const vOrig = new THREE.Vector3();
    const vCurr = new THREE.Vector3();
    const nOrig = new THREE.Vector3();
    const nCurr = new THREE.Vector3();
    
    // We get the interpolated angle directly from the spring
    const currentSpringAngle = springAngle.get();

    for (let i = 0; i < posAttr.count; i++) {
      vOrig.set(basePositions[i * 3], basePositions[i * 3 + 1], basePositions[i * 3 + 2]);
      nOrig.set(baseNormals[i * 3], baseNormals[i * 3 + 1], baseNormals[i * 3 + 2]);
      
      vCurr.copy(vOrig);
      nCurr.copy(nOrig);
      
      const allFolds = tempFold ? [...folds, tempFold] : folds;
      
      for (let fIdx = 0; fIdx < allFolds.length; fIdx++) {
        const fold = allFolds[fIdx];
        let currentAngle = fold.angle;
        if (!tempFold && fIdx === allFolds.length - 1) {
           currentAngle = currentSpringAngle;
        }
        
        const toVertex = new THREE.Vector3().subVectors(vCurr, fold.axisPoint);
        if (toVertex.dot(fold.foldSideNormal) > 1e-4) {
          vCurr.sub(fold.axisPoint).applyAxisAngle(fold.axisDir, currentAngle).add(fold.axisPoint);
          nCurr.applyAxisAngle(fold.axisDir, currentAngle);
          
          // Add a tiny offset along the normal to prevent Z-fighting with multiple layers
          vCurr.addScaledVector(nCurr, 0.005);
        }
      }
      
      posAttr.setXYZ(i, vCurr.x, vCurr.y, vCurr.z);
      normAttr.setXYZ(i, nCurr.x, nCurr.y, nCurr.z);
    }
    
    posAttr.needsUpdate = true;
    normAttr.needsUpdate = true;
    geom.computeBoundingSphere();
    geom.computeBoundingBox();
  });

  const getSnappedPoint = (pt: THREE.Vector3) => {
    if (!snapToGrid) return pt;
    const snapThreshold = 0.5; // Grid cells are 1x1, so snapping distance is 0.5
    const snapped = new THREE.Vector3(Math.round(pt.x), Math.round(pt.y), Math.round(pt.z));
    if (pt.distanceTo(snapped) < snapThreshold) {
      return snapped;
    }
    return pt;
  };

  const getLocalPoint = (e: ThreeEvent<PointerEvent>) => {
    if (!meshRef.current) return new THREE.Vector3();
    return meshRef.current.worldToLocal(e.point.clone());
  };

  const handlePointerDown = (e: ThreeEvent<PointerEvent>) => {
    if (mode !== 'interact') return;
    e.stopPropagation();
    
    let pt = getLocalPoint(e);
    pt = getSnappedPoint(pt);
    
    setDragStartPoint(pt);
    setDragCurrentPoint(pt);
    playPaperSound('drag');
  };

  const handlePointerMove = (e: ThreeEvent<PointerEvent>) => {
    if (mode !== 'interact' || !dragStartPoint) return;
    e.stopPropagation();

    let pt = getLocalPoint(e);
    pt = getSnappedPoint(pt);
    
    setDragCurrentPoint(pt);
  };

  const handlePointerUp = (e: ThreeEvent<PointerEvent>) => {
    if (mode !== 'interact' || !dragStartPoint) return;
    e.stopPropagation();
    
    if (tempFold) {
      addFold({ ...tempFold, id: Math.random().toString(36).substr(2, 9) });
      playPaperSound('fold');
    }
    
    setDragStartPoint(null);
    setDragCurrentPoint(null);
  };

  // Remove lineGeometry and add crease memory lines
  const creaseLines = useMemo(() => {
    return folds.map(fold => {
      // Draw a line along the fold axis, extending a bit
      const p1 = fold.axisPoint.clone().addScaledVector(fold.axisDir, 10);
      const p2 = fold.axisPoint.clone().addScaledVector(fold.axisDir, -10);
      return new THREE.BufferGeometry().setFromPoints([p1, p2]);
    });
  }, [folds]);

  return (
    <group rotation={[-Math.PI / 2, 0, 0]}>
      {/* Front Face */}
      <mesh 
        ref={meshRef} 
        geometry={baseGeometry}
        castShadow 
        receiveShadow
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      >
        <meshStandardMaterial 
          color={paperColor} 
          side={THREE.FrontSide} 
          roughness={0.9}
          bumpMap={paperBumpMap}
          bumpScale={0.002}
        />
      </mesh>
      
      {/* Back Face (White) */}
      <mesh geometry={baseGeometry} receiveShadow castShadow>
        <meshStandardMaterial 
          color="#ffffff" 
          side={THREE.BackSide} 
          roughness={0.9}
          bumpMap={paperBumpMap}
          bumpScale={0.002}
        />
      </mesh>

      {/* Crease Memory: physical lines for previous folds */}
      {creaseLines.map((geom, idx) => (
        <primitive key={idx} object={new THREE.Line(geom, new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.1, depthTest: true }))} />
      ))}
      
      {/* Visual Feedback for Drag-to-Fold points */}
      {dragStartPoint && mode === 'interact' && (
        <mesh position={[dragStartPoint.x, dragStartPoint.y, dragStartPoint.z]}>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshBasicMaterial color="#ff0055" depthTest={false} />
        </mesh>
      )}
      {dragCurrentPoint && mode === 'interact' && (
        <mesh position={[dragCurrentPoint.x, dragCurrentPoint.y, dragCurrentPoint.z]}>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshBasicMaterial color="#00aaff" depthTest={false} />
        </mesh>
      )}
    </group>
  );
}
