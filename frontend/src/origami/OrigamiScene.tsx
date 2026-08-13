import React from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, ContactShadows } from '@react-three/drei';
import { EffectComposer, N8AO } from '@react-three/postprocessing';
import { OrigamiPaper } from './OrigamiPaper';
import { useOrigamiStore } from './useOrigamiStore';

export function OrigamiScene() {
  const { mode, snapToGrid } = useOrigamiStore();
  
  return (
    <Canvas shadows camera={{ position: [0, 8, 8], fov: 45 }}>
      <color attach="background" args={['#F9F8F6']} />
      
      <ambientLight intensity={0.6} />
      <hemisphereLight intensity={0.5} color="#ffffff" groundColor="#dddddd" />
      <directionalLight 
        position={[10, 10, 5]} 
        intensity={1.0} 
        castShadow 
        shadow-mapSize={2048}
        shadow-bias={-0.0001}
      />
      
      <OrigamiPaper />
      
      {mode === 'interact' && snapToGrid && (
        <gridHelper args={[10, 10, '#000000', '#cccccc']} position={[0, 0.001, 0]} material-opacity={0.2} material-transparent />
      )}
      
      <ContactShadows 
        position={[0, -0.05, 0]} 
        opacity={0.4} 
        scale={20} 
        blur={2} 
        far={10} 
      />
      
      <EffectComposer>
        <N8AO aoRadius={0.5} intensity={1.5} color="#000000" />
      </EffectComposer>

      <OrbitControls 
        makeDefault 
        minPolarAngle={0} 
        maxPolarAngle={Math.PI / 2 + 0.1}
        enablePan={false}
        enabled={mode === 'view'}
      />
    </Canvas>
  );
}
