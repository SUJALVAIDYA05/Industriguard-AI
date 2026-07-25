import { useEffect, useState } from "react";
import { io } from "socket.io-client";
import Dashboard        from "./pages/Dashboard";
import LiveAlert        from "./components/LiveAlert";
import ImageUploadPanel from "./components/ImageUploadPanel";

const socket = io("http://localhost:5000", {
  reconnection:      true,
  reconnectionDelay: 1000
});

export default function App() {
  const [connected,    setConnected]    = useState(false);
  const [latestUpdate, setLatestUpdate] = useState(null);
  const [activeMode,   setActiveMode]   = useState("live"); // "live" | "upload"

  useEffect(() => {
    socket.on("connect", () => {
      console.log("[Socket] Connected to backend");
      setConnected(true);
    });

    socket.on("disconnect", () => {
      console.log("[Socket] Disconnected");
      setConnected(false);
    });

    socket.on("check_update", (data) => {
      console.log("[Socket] New check update:", data);
      setLatestUpdate({ ...data, _ts: Date.now() });
    });

    return () => {
      socket.off("connect");
      socket.off("disconnect");
      socket.off("check_update");
    };
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-base)" }}>

      {/* ── Top Navigation Bar ──────────────────────────────── */}
      <header
        style={{
          background:  "var(--bg-panel)",
          borderBottom: "1px solid var(--border)",
          position:    "sticky",
          top:         0,
          zIndex:      100
        }}
      >
        <div
          className="flex items-center justify-between px-6 py-3 max-w-screen-2xl mx-auto"
        >
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded flex items-center justify-center text-base"
              style={{ background: "var(--amber-glow)", border: "1px solid var(--amber-dim)" }}
            >
              🏭
            </div>
            <div>
              <h1
                className="text-lg font-bold leading-none"
                style={{ fontFamily: "var(--font-display)", color: "var(--amber)" }}
              >
                IndustriGuard AI
              </h1>
              <p
                className="text-xs leading-none mt-0.5"
                style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}
              >
                Industrial Safety Surveillance
              </p>
            </div>
          </div>

          {/* Right side — connection status + date */}
          <div className="flex items-center gap-4">
            <span
              className="text-xs"
              style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}
            >
              {new Date().toLocaleDateString("en-IN", {
                weekday: "long",
                year:    "numeric",
                month:   "long",
                day:     "numeric"
              })}
            </span>

            {/* Live / Offline badge */}
            <div
              className="flex items-center gap-2 px-3 py-1.5 rounded text-xs"
              style={{
                background: connected ? "var(--green-glow)" : "var(--red-glow)",
                border:     `1px solid ${connected ? "var(--green-dim)" : "var(--red-dim)"}`,
                color:      connected ? "var(--green)" : "var(--red)",
                fontFamily: "var(--font-mono)"
              }}
            >
              <div
                className="w-1.5 h-1.5 rounded-full"
                style={{
                  background: connected ? "var(--green)" : "var(--red)",
                  animation:  connected ? "pulse-green 2s infinite" : "none"
                }}
              />
              {connected ? "LIVE" : "OFFLINE"}
            </div>
          </div>
        </div>

        {/* ── Mode Switcher Tabs ───────────────────────────────── */}
        <div
          style={{
            borderTop:   "1px solid var(--border)",
            padding:     "0 24px",
            display:     "flex",
            gap:         "4px",
          }}
        >
          {[
            { id: "live",   label: "🎥  Live Camera Detection" },
            { id: "upload", label: "📷  Image Upload Detection" },
          ].map((tab) => (
            <button
              key={tab.id}
              id={`tab-${tab.id}`}
              onClick={() => setActiveMode(tab.id)}
              style={{
                padding:      "10px 20px",
                background:   "transparent",
                border:       "none",
                borderBottom: activeMode === tab.id ? "2px solid var(--amber)" : "2px solid transparent",
                color:        activeMode === tab.id ? "var(--amber)" : "var(--text-secondary)",
                fontFamily:   "var(--font-mono)",
                fontSize:     "12px",
                fontWeight:   activeMode === tab.id ? 700 : 400,
                letterSpacing: "0.06em",
                cursor:       "pointer",
                transition:   "all 0.2s ease",
                marginBottom: "-1px",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      {/* ── Main Content (mode-dependent) ─────────────────── */}
      <main>
        {activeMode === "live" ? (
          <Dashboard latestUpdate={latestUpdate} />
        ) : (
          <ImageUploadPanel />
        )}
      </main>

      {/* ── Live Alert Popup ────────────────────────────────── */}
      <LiveAlert update={latestUpdate} />

    </div>
  );
}