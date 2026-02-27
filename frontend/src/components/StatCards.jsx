import { useEffect, useState } from "react";

const StatCard = ({ label, value, sub, accent, icon, animatePulse }) => {
  const accents = {
    amber: {
      border: "border-amber-500/30",
      glow:   "shadow-amber-500/10",
      text:   "text-amber-400",
      dot:    "bg-amber-400",
      pulse:  "pulse-amber"
    },
    green: {
      border: "border-emerald-500/30",
      glow:   "shadow-emerald-500/10",
      text:   "text-emerald-400",
      dot:    "bg-emerald-400",
      pulse:  "pulse-green"
    },
    red: {
      border: "border-red-500/30",
      glow:   "shadow-red-500/10",
      text:   "text-red-400",
      dot:    "bg-red-400",
      pulse:  "pulse-red"
    },
    blue: {
      border: "border-blue-500/30",
      glow:   "shadow-blue-500/10",
      text:   "text-blue-400",
      dot:    "bg-blue-400",
    }
  };

  const a = accents[accent] || accents.amber;

  return (
    <div
      className={`panel scanline relative p-5 border ${a.border} shadow-lg ${a.glow}`}
      style={{ animationFillMode: "forwards" }}
    >
      {/* Top row */}
      <div className="flex items-center justify-between mb-3">
        <span
          className="text-xs font-semibold tracking-widest uppercase"
          style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}
        >
          {label}
        </span>
        <span className="text-xl">{icon}</span>
      </div>

      {/* Value */}
      <div
        className={`text-4xl font-bold ${a.text} mb-1`}
        style={{ fontFamily: "var(--font-display)", letterSpacing: "-0.02em" }}
      >
        {value ?? "—"}
      </div>

      {/* Sub text */}
      {sub && (
        <div
          className="text-xs mt-1"
          style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}
        >
          {sub}
        </div>
      )}

      {/* Live indicator */}
      {animatePulse && (
        <div className="absolute top-4 right-4 flex items-center gap-1.5">
          <div
            className={`w-2 h-2 rounded-full ${a.dot}`}
            style={{ animation: `${a.pulse} 2s infinite` }}
          />
        </div>
      )}
    </div>
  );
};

export default function StatCards({ stats }) {
  if (!stats) return null;

  const { today, current, ppe_violations } = stats;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <StatCard
        label="Checks Today"
        value={today?.total_checks ?? 0}
        sub={`Since midnight`}
        accent="amber"
        icon="📋"
        animatePulse
      />
      <StatCard
        label="Ready"
        value={current?.ready ?? 0}
        sub={`${today?.ready_percentage ?? 0}% compliance rate`}
        accent="green"
        icon="✅"
      />
      <StatCard
        label="Not Ready"
        value={current?.not_ready ?? 0}
        sub={`${ppe_violations?.no_helmet ?? 0} missing helmet · ${ppe_violations?.no_vest ?? 0} missing vest`}
        accent="red"
        icon="🚨"
        animatePulse={current?.not_ready > 0}
      />
      <StatCard
        label="Total Employees"
        value={current?.total_employees ?? 0}
        sub="Registered in system"
        accent="blue"
        icon="👷"
      />
    </div>
  );
}