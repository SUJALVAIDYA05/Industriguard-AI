import {
    AreaChart, Area, XAxis, YAxis,
    CartesianGrid, Tooltip, ResponsiveContainer, Legend
  } from "recharts";
  
  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div
        className="px-4 py-3 rounded border text-sm"
        style={{
          background:  "var(--bg-elevated)",
          border:      "1px solid var(--border-bright)",
          fontFamily:  "var(--font-mono)",
          color:       "var(--text-primary)"
        }}
      >
        <p className="mb-2 font-bold" style={{ color: "var(--amber)" }}>{label}</p>
        {payload.map(p => (
          <p key={p.name} style={{ color: p.color }}>
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  };
  
  export default function TrendChart({ trend }) {
    const data = (trend || []).map(item => ({
      hour:      item.hour,
      Ready:     item.ready,
      "Not Ready": item.not_ready
    }));
  
    return (
      <div className="panel p-5">
        <div className="mb-5">
          <h2
            className="text-base font-bold tracking-wide"
            style={{ fontFamily: "var(--font-display)", color: "var(--amber)" }}
          >
            COMPLIANCE TREND
          </h2>
          <p
            className="text-xs mt-0.5"
            style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}
          >
            Last 24 hours · Hourly breakdown
          </p>
        </div>
  
        {data.length === 0 ? (
          <div
            className="flex items-center justify-center h-48"
            style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}
          >
            No trend data yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorReady" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}   />
                </linearGradient>
                <linearGradient id="colorNotReady" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}   />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--border)"
                vertical={false}
              />
              <XAxis
                dataKey="hour"
                tick={{ fill: "var(--text-secondary)", fontSize: 11, fontFamily: "var(--font-mono)" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "var(--text-secondary)", fontSize: 11, fontFamily: "var(--font-mono)" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{
                  fontFamily: "var(--font-mono)",
                  fontSize:   "12px",
                  color:      "var(--text-secondary)"
                }}
              />
              <Area
                type="monotone"
                dataKey="Ready"
                stroke="#10b981"
                strokeWidth={2}
                fill="url(#colorReady)"
                dot={false}
              />
              <Area
                type="monotone"
                dataKey="Not Ready"
                stroke="#ef4444"
                strokeWidth={2}
                fill="url(#colorNotReady)"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    );
  }