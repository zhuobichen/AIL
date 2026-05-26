import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import Task from "@/pages/Task";
import Report from "@/pages/Report";

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-950 text-gray-100 font-sans selection:bg-cyan-500/30">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/task/:taskId" element={<Task />} />
          <Route path="/report/:taskId" element={<Report />} />
        </Routes>
      </div>
    </Router>
  );
}