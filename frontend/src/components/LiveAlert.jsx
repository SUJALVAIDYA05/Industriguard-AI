import { useEffect, useState } from "react";

export default function LiveAlert({ update }) {
  const [visible, setVisible] = useState(false);
  const [current, setCurrent] = useState(null);

  useEffect(() => {
    if (!update) return;

    setCurrent(update);
    setVisible(true);

    // Auto hide after 5 seconds
    const timer = setTimeout(() => setVisible(false), 5000);
    return () => clearTimeout(timer);
  }, [update]);

  if (!visible || !current) return null;

  const isReady   = current.status === "READY";
  const borderCol = isReady ? "var(--green)" : "var(--red)";
  const bgCol     = isReady ? "var(--green-glow)" : "var(--red-glow)";
  const textCol   = isReady ? "var(--green)" : "var(--red)";

  return (
    <div
      className="fixed bottom-6 right-6 z-50 animate-slide-in"
      style={{ width: "320px" }}
    >
      <div
        className="rounded p-4 shadow-2xl"
        style={{
          background:  "var(--bg-elevated)",
          border:      `1px solid ${borderCol}`,
          borderLeft:  `4px solid ${borderCol}`,
          boxShadow:   `0 0 30px ${bgCol}`
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <span
            className="text-xs font-bold tracking-widest uppercase"
            style={{ color: textCol, fontFamily: "var(--font-mono)" }}
          >
            {isReady ? "✓ Check Complete" : "⚠ Safety Violation"}
          </span>
          <button
            onClick={() => setVisible(false)}
            className="text-xs opacity-40 hover:opacity-100"
            style={{ color: "var(--text-secondary)" }}
          >
            ✕
          </button>
        </div>

        {/* Employee info */}
        <p
          className="font-bold text-base mb-1"
          style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}
        >
          {current.employee_name}
        </p>
        <p
          className="text-xs mb-2"
          style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}
        >
          {current.employee_id} · {current.department}
        </p>

        {/* PPE status */}
        <div className="flex gap-3 mb-2">
          <span style={{ color: current.has_helmet ? "var(--green)" : "var(--red)", fontSize: "13px" }}>
            {current.has_helmet ? "✓" : "✗"} Helmet
          </span>
          <span style={{ color: current.has_vest ? "var(--green)" : "var(--red)", fontSize: "13px" }}>
            {current.has_vest ? "✓" : "✗"} Vest
          </span>
        </div>

        {/* Status */}
        <span className={isReady ? "badge-ready" : "badge-not-ready"}>
          {current.status}
        </span>

        {/* Timestamp */}
        <p
          className="text-xs mt-2 opacity-50"
          style={{ fontFamily: "var(--font-mono)" }}
        >
          {current.timestamp}
        </p>

        {/* Progress bar — auto dismiss timer */}
        <div
          className="mt-3 h-0.5 rounded"
          style={{ background: "var(--border)" }}
        >
          <div
            style={{
              height:     "100%",
              background: borderCol,
              animation:  "progress-shrink 5s linear forwards",
              borderRadius: "2px"
            }}
          />
        </div>
      </div>

      <style>{`
        @keyframes progress-shrink {
          from { width: 100%; }
          to   { width: 0%; }
        }
      `}</style>
    </div>
  );
}