import React from 'react';
import { OrigamiScene } from './components/OrigamiScene';
import { UIOverlay } from './components/UIOverlay';

function App() {
  return (
    <div className="w-screen h-screen overflow-hidden bg-[#F9F8F6]">
      <OrigamiScene />
      <UIOverlay />
    </div>
  );
}

export default App;
