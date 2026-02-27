import { useState } from "react";

const PPEIcon = ({ present, label }) => (
  <span
    title={label}
    className="inline-flex items-center gap-1 text-sm font-mono"
    style={{ color: present ? "var(--green)" : "var(--red)" }}
  >
    {present ? "✓" : "✗"}
    <span className="text-xs opacity-70">{label}</span>
  </span>
);

export default function EmployeeTable({ employees, latestUpdate }) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("ALL");

  const filtered = (employees || []).filter(emp => {
    const matchSearch =
      emp.employee_name.toLowerCase().includes(search.toLowerCase()) ||
      emp.employee_id.toLowerCase().includes(search.toLowerCase()) ||
      emp.department.toLowerCase().includes(search.toLowerCase());

    const matchFilter =
      filter === "ALL" ||
      emp.status === filter;

    return matchSearch && matchFilter;
  });

  const isNew = (timestamp) => {
    if (!timestamp || !latestUpdate) return false;
    return timestamp === latestUpdate.timestamp &&
           latestUpdate.employee_id === employees?.find(
             e => e.last_checked === timestamp
           )?.employee_id;
  };

  return (
    <div className="panel mb-6">
      {/* Header */}
      <div
        className="flex items-center justify-between px-5 py-4 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <div>
          <h2
            className="text-base font-bold tracking-wide"
            style={{ fontFamily: "var(--font-display)", color: "var(--amber)" }}
          >
            EMPLOYEE SAFETY STATUS
          </h2>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>
            Live feed · Updates in real time
          </p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <input
            type="text"
            placeholder="Search employee..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="px-3 py-1.5 text-sm rounded border outline-none"
            style={{
              background:   "var(--bg-elevated)",
              border:       "1px solid var(--border-bright)",
              color:        "var(--text-primary)",
              fontFamily:   "var(--font-mono)",
              width:        "180px"
            }}
          />
          {["ALL", "READY", "NOT READY"].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className="px-3 py-1.5 text-xs font-semibold tracking-wider uppercase rounded transition-all"
              style={{
                fontFamily:  "var(--font-mono)",
                background:  filter === f ? "var(--amber-glow)" : "transparent",
                color:       filter === f ? "var(--amber)" : "var(--text-secondary)",
                border:      `1px solid ${filter === f ? "var(--amber-dim)" : "var(--border)"}`,
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        {filtered.length === 0 ? (
          <div
            className="text-center py-16"
            style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}
          >
            {employees?.length === 0
              ? "No employees checked yet. Waiting for QR scans..."
              : "No employees match the current filter."}
          </div>
        ) : (
          <table className="ig-table">
            <thead>
              <tr>
                <th>Employee ID</th>
                <th>Name</th>
                <th>Department</th>
                <th>Role</th>
                <th>Helmet</th>
                <th>Safety Vest</th>
                <th>Status</th>
                <th>Last Checked</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((emp) => (
                <tr
                  key={emp.employee_id}
                  className={
                    latestUpdate?.employee_id === emp.employee_id
                      ? "animate-fade-in"
                      : ""
                  }
                >
                  <td>
                    <span
                      className="font-mono text-xs px-2 py-1 rounded"
                      style={{
                        background:  "var(--bg-elevated)",
                        color:       "var(--amber)",
                        border:      "1px solid var(--border)",
                      }}
                    >
                      {emp.employee_id}
                    </span>
                  </td>
                  <td className="font-semibold">{emp.employee_name}</td>
                  <td style={{ color: "var(--text-secondary)" }}>{emp.department}</td>
                  <td style={{ color: "var(--text-secondary)", fontSize: "13px" }}>{emp.role}</td>
                  <td><PPEIcon present={emp.has_helmet} label="Helmet" /></td>
                  <td><PPEIcon present={emp.has_vest}   label="Vest"   /></td>
                  <td>
                    <span className={emp.status === "READY" ? "badge-ready" : "badge-not-ready"}>
                      {emp.status}
                    </span>
                  </td>
                  <td
                    className="text-xs"
                    style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}
                  >
                    {emp.last_checked}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}