import React from 'react';
import { useOrigamiStore, ToolMode } from './useOrigamiStore';

export function UIOverlay() {
  const { 
    mode, setMode, 
    paperColor, setPaperColor,
    undoFold, clearFolds, folds,
    snapToGrid, setSnapToGrid
  } = useOrigamiStore();

  const handleModeChange = (newMode: ToolMode) => {
    setMode(newMode);
  };

  return (
    <div className="absolute top-0 left-0 w-full h-full pointer-events-none p-6 flex flex-col justify-between font-sans">
      <div className="flex justify-between items-start">
        <div className="pointer-events-auto bg-white/80 backdrop-blur-md p-6 rounded-2xl shadow-xl border border-gray-100 w-80">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Origami Simulator</h1>
          <p className="text-sm text-gray-500 mb-6">Physical fold engine with real-world drag interactions.</p>
          
          <div className="space-y-6">
            {/* Tools */}
            <div>
              <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Interaction Mode</h2>
              <div className="flex gap-2">
                <button 
                  onClick={() => handleModeChange('interact')}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                    mode === 'interact' 
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-200' 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  Drag to Fold
                </button>
                <button 
                  onClick={() => handleModeChange('view')}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                    mode === 'view' 
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-200' 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  Inspect 3D
                </button>
              </div>
            </div>

            {/* Appearance */}
            <div>
              <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Paper Color</h2>
              <div className="flex gap-3">
                {['#ff99aa', '#99ccff', '#99ffaa', '#ffd699'].map(color => (
                  <button
                    key={color}
                    onClick={() => setPaperColor(color)}
                    className={`w-8 h-8 rounded-full border-2 transition-transform ${
                      paperColor === color ? 'border-blue-500 scale-110' : 'border-transparent hover:scale-105'
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>
            
            {/* Settings */}
            <div>
              <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Settings</h2>
              <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={snapToGrid}
                  onChange={(e) => setSnapToGrid(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                Snap to Grid
              </label>
            </div>

            {/* Actions */}
            <div className="pt-4 border-t border-gray-200 flex gap-2">
              <button 
                onClick={undoFold}
                disabled={folds.length === 0}
                className="flex-1 py-2 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed text-gray-700 rounded-lg text-sm font-medium transition-colors"
              >
                Undo
              </button>
              <button 
                onClick={clearFolds}
                disabled={folds.length === 0}
                className="flex-1 py-2 bg-red-50 hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed text-red-600 rounded-lg text-sm font-medium transition-colors"
              >
                Reset
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Help Tip */}
      <div className="pointer-events-auto bg-black/70 backdrop-blur-md text-white px-6 py-3 rounded-full self-center flex items-center gap-3 shadow-lg">
        {mode === 'interact' ? (
          <>
            <span className="text-xl">👆</span>
            <span className="text-sm font-medium">Click and drag any corner of the paper to fold it!</span>
          </>
        ) : (
          <>
            <span className="text-xl">👁️</span>
            <span className="text-sm font-medium">Left click to rotate, right click to pan, scroll to zoom.</span>
          </>
        )}
      </div>
    </div>
  );
}
