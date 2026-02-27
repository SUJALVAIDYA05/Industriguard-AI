export default function CheckHistory({ checks }) {
    const list = checks || [];
  
    return (
      <div className="panel p-5">
        <div className="mb-4">
          <h2
            className="text-base font-bold tracking-wide"
            style={{ fontFamily: "var(--font-display)", color: "var(--amber)" }}
          >
            RECENT CHECKS
          </h2>
          <p
            className="text-xs mt-0.5"
            style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}
          >
            Latest {list.length} entries
          </p>
        </div>
  
        <div className="space-y-2 overflow-y-auto" style={{ maxHeight: "320px" }}>
          {list.length === 0 ? (
            <div
              className="text-center py-10"
              style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}
            >
              No checks recorded yet
            </div>
          ) : (
            list.map((check, i) => (
              <div
                key={check.id}
                className="flex items-center justify-between px-4 py-3 rounded"
                style={{
                  background:   i === 0 ? "var(--bg-elevated)" : "transparent",
                  border:       "1px solid var(--border)",
                  borderLeft:   `3px solid ${check.status === "READY" ? "var(--green)" : "var(--red)"}`
                }}
              >
                {/* Left — employee info */}
                <div className="flex items-center gap-3">
                  <div
                    className="text-xs font-mono px-2 py-0.5 rounded"
                    style={{
                      background: "var(--bg-base)",
                      color:      "var(--amber)",
                      border:     "1px solid var(--border)"
                    }}
                  >
                    {check.employee_id}
                  </div>
                  <div>
                    <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                      {check.employee_name}
                    </p>
                    <p className="text-xs" style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>
                      {check.department}
                      {check.missing_ppe && check.missing_ppe !== "" &&
                        <span style={{ color: "var(--red)" }}> · Missing: {check.missing_ppe}</span>
                      }
                    </p>
                  </div>
                </div>
  
                {/* Right — status + time */}
                <div className="text-right">
                  <span className={check.status === "READY" ? "badge-ready" : "badge-not-ready"}>
                    {check.status}
                  </span>
                  <p
                    className="text-xs mt-1"
                    style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
                  >
                    {check.timestamp}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  }