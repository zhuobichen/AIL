import { OrigamiScene } from './OrigamiScene';
import { UIOverlay } from './UIOverlay';

export default function OrigamiApp() {
  return (
    <div className="relative w-screen h-screen overflow-hidden bg-[#F9F8F6]">
      <OrigamiScene />
      <UIOverlay />
    </div>
  );
}
