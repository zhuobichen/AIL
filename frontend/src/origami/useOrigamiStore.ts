import { create } from 'zustand';
import * as THREE from 'three';

export type ToolMode = 'interact' | 'view';

export interface Fold {
  id: string;
  axisPoint: THREE.Vector3;
  axisDir: THREE.Vector3;
  foldSideNormal: THREE.Vector3;
  angle: number;
}

interface OrigamiState {
  mode: ToolMode;
  setMode: (mode: ToolMode) => void;
  
  paperColor: string;
  setPaperColor: (color: string) => void;
  
  paperTexture: string;
  setPaperTexture: (texture: string) => void;
  
  snapToGrid: boolean;
  setSnapToGrid: (snap: boolean) => void;
  
  // Drag-to-fold state
  dragStartPoint: THREE.Vector3 | null;
  dragCurrentPoint: THREE.Vector3 | null;
  setDragStartPoint: (pt: THREE.Vector3 | null) => void;
  setDragCurrentPoint: (pt: THREE.Vector3 | null) => void;
  
  // Active folds
  folds: Fold[];
  addFold: (fold: Fold) => void;
  undoFold: () => void;
  clearFolds: () => void;
}

export const useOrigamiStore = create<OrigamiState>((set) => ({
  mode: 'interact',
  setMode: (mode) => set({ mode }),
  
  paperColor: '#ff99aa',
  setPaperColor: (paperColor) => set({ paperColor }),
  
  paperTexture: 'smooth',
  setPaperTexture: (paperTexture) => set({ paperTexture }),
  
  snapToGrid: false,
  setSnapToGrid: (snapToGrid) => set({ snapToGrid }),
  
  dragStartPoint: null,
  dragCurrentPoint: null,
  setDragStartPoint: (pt) => set({ dragStartPoint: pt }),
  setDragCurrentPoint: (pt) => set({ dragCurrentPoint: pt }),
  
  folds: [],
  addFold: (fold) => set((state) => ({ folds: [...state.folds, fold] })),
  undoFold: () => set((state) => {
    if (state.folds.length === 0) return state;
    return { folds: state.folds.slice(0, -1) };
  }),
  clearFolds: () => set({ folds: [] }),
}));
