import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import SignInSide from "./SignInSide.tsx";
import App from "./App.tsx";
import "./index.css";

const userCookie = document.cookie.split('; ').find(cookie => cookie.startsWith('opengpts_user_id='));
const isUserSignedIn = userCookie && userCookie.split('=')[1] === '46708943293';

ReactDOM.createRoot(document.getElementById("root")!).render(
  <Router>
    <Routes>
      {isUserSignedIn ? (
        <Route path="/app" element={<App />} />
      ) : (
        <Route path="/signin" element={<SignInSide />} />
      )}
        <Route path="/app" element={<App />} />
      <Route path="/signin" element={<SignInSide />} />
      <Route path="*" element={<Navigate to="/signin" />} />
    </Routes>
  </Router>
);
