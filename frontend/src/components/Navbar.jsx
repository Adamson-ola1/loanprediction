import { useEffect, useState } from "react";
import { getHealth } from "../api/client";

export default function Navbar() {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    let cancelled = false;
    getHealth()
      .then((res) => {
        if (!cancelled) setStatus(res.model_loaded ? "online" : "offline");
      })
      .catch(() => {
        if (!cancelled) setStatus("offline");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const statusLabel = {
    checking: "Checking model…",
    online: "Model live",
    offline: "Model unavailable",
  }[status];

  return (
    <header className="navbar">
      <span className="navbar__title">Loan Default Risk Desk</span>
      <div className="navbar__status">
        <span className={`status-dot ${status === "checking" ? "" : status}`} />
        {statusLabel}
      </div>
    </header>
  );
}
