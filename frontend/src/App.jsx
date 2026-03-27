import { Routes, Route, useLocation } from "react-router-dom";
import Register from "./Pages/Register";
import Login from "./Pages/Login";
import Interview from "./Pages/Interview";
import ChatInterview from "./Pages/ChatInterview";
import VoiceInterview from "./Pages/VoiceInterview";
import HRDashboard from "./HRpages/HRDashboard";
import Navbar from "./components/Navbar";
import InterviewPage from "./Pages/InterviewPage";

function App() {
  const location = useLocation();
  const noNavbarPaths = ["/login", "/register", "/"];

  return (
    <>
      {!noNavbarPaths.includes(location.pathname) && <Navbar />}
      <div className={!noNavbarPaths.includes(location.pathname) ? "pt-16" : ""}>
        <Routes>
          <Route path="/" element={<Register />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route path="/interview" element={<Interview />} />
          <Route path="/chat" element={<ChatInterview />} />
          <Route path="/voice" element={<VoiceInterview />} />
          <Route path="/hr-dashboard" element={<HRDashboard />} />
          <Route path="/interview/:sessionId" element={<InterviewPage />} />
        </Routes>
      </div>
    </>
  );
}

export default App;
