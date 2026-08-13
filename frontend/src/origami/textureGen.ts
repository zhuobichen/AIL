import * as THREE from 'three';

let cachedTexture: THREE.CanvasTexture | null = null;

export function getPaperBumpMap(): THREE.CanvasTexture {
  if (cachedTexture) return cachedTexture;

  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  
  if (!ctx) {
    return new THREE.CanvasTexture(canvas);
  }

  // Base background
  ctx.fillStyle = '#808080';
  ctx.fillRect(0, 0, 512, 512);

  // Generate noise
  const imgData = ctx.getImageData(0, 0, 512, 512);
  const data = imgData.data;
  
  for (let i = 0; i < data.length; i += 4) {
    // Paper fibers/noise usually has high frequency but low amplitude
    const noise = Math.random() * 40 - 20; 
    const val = 128 + noise;
    data[i] = val;
    data[i+1] = val;
    data[i+2] = val;
    data[i+3] = 255;
  }
  
  ctx.putImageData(imgData, 0, 0);

  // Add some slight larger variations/fibers
  for (let i = 0; i < 1000; i++) {
    ctx.fillStyle = `rgba(${Math.random() > 0.5 ? 255 : 0}, 255, 255, ${Math.random() * 0.05})`;
    ctx.fillRect(
      Math.random() * 512, 
      Math.random() * 512, 
      Math.random() * 10 + 2, 
      Math.random() * 2 + 1
    );
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(4, 4);
  
  cachedTexture = texture;
  return texture;
}
