import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import Task from "@/pages/Task";
import Report from "@/pages/Report";
import OrigamiApp from "@/origami/OrigamiApp";

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-950 text-gray-100 font-sans selection:bg-cyan-500/30">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/task/:taskId" element={<Task />} />
          <Route path="/report/:taskId" element={<Report />} />
          <Route path="/origami" element={<OrigamiApp />} />
        </Routes>
      </div>
    </Router>
  );
}