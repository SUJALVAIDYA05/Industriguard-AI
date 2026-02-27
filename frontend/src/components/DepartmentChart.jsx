import {
    BarChart, Bar, XAxis, YAxis,
    CartesianGrid, Tooltip, ResponsiveContainer, Legend
  } from "recharts";
  
  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div
        className="px-4 py-3 rounded border text-sm"
        style={{
          background: "var(--bg-elevated)",
          border:     "1px solid var(--border-bright)",
          fontFamily: "var(--font-mono)",
          color:      "var(--text-primary)"
        }}
      >
        <p className="font-bold mb-1" style={{ color: "var(--amber)" }}>{label}</p>
        {payload.map(p => (
          <p key={p.name} style={{ color: p.color }}>
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  };
  
  export default function DepartmentChart({ departments }) {
    const data = (departments || []).map(d => ({
      name:       d.department,
      Ready:      d.ready,
      "Not Ready": d.not_ready
    }));
  
    return (
      <div className="panel p-5">
        <div className="mb-5">
          <h2
            className="text-base font-bold tracking-wide"
            style={{ fontFamily: "var(--font-display)", color: "var(--amber)" }}
          >
            DEPARTMENT COMPLIANCE
          </h2>
          <p
            className="text-xs mt-0.5"
            style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}
          >
            Today's safety check breakdown by department
          </p>
        </div>
  
        {data.length === 0 ? (
          <div
            className="flex items-center justify-center h-48"
            style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}
          >
            No department data yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--border)"
                vertical={false}
              />
              <XAxis
                dataKey="name"
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
                wrapperStyle={{ fontFamily: "var(--font-mono)", fontSize: "12px" }}
              />
              <Bar dataKey="Ready"     fill="#10b981" radius={[3, 3, 0, 0]} maxBarSize={40} />
              <Bar dataKey="Not Ready" fill="#ef4444" radius={[3, 3, 0, 0]} maxBarSize={40} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    );
  }