import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";
import App from "./App";
import { initApiUrl } from "./api/client";
import { applyInitialTheme } from "./hooks/useTheme";
import "./assets/styles.css";

// Apply theme before first paint to prevent flash
applyInitialTheme();

initApiUrl().then(() => {
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <HashRouter>
        <App />
      </HashRouter>
    </React.StrictMode>,
  );
});
