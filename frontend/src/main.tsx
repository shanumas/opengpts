import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import SignInSide from "./SignInSide.tsx";
import App from "./App.tsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <Router>
    <Routes>
        <Route path="/app" element={<App />} />
        <Route path="" element={<App />} />
        <Route path="signin" element={<SignInSide />} />
      <Route path="*" element={<App />} />
    </Routes>
  </Router>
);
