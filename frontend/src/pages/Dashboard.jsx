import { useEffect, useState, useCallback } from "react";
import StatCards       from "../components/StatCards";
import EmployeeTable   from "../components/EmployeeTable";
import TrendChart      from "../components/TrendChart";
import CheckHistory    from "../components/CheckHistory";
import DepartmentChart from "../components/DepartmentChart";

const API = "http://localhost:5000";

export default function Dashboard({ latestUpdate }) {
  const [stats,       setStats]       = useState(null);
  const [employees,   setEmployees]   = useState([]);
  const [trend,       setTrend]       = useState([]);
  const [checks,      setChecks]      = useState([]);
  const [departments, setDepartments] = useState([]);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [loading,     setLoading]     = useState(true);

  const fetchAll = useCallback(async () => {
    try {
      const [statsRes, empRes, trendRes, checksRes, deptRes] = await Promise.all([
        fetch(`${API}/api/stats`),
        fetch(`${API}/api/employees/status`),
        fetch(`${API}/api/trend`),
        fetch(`${API}/api/checks?limit=30`),
        fetch(`${API}/api/departments`)
      ]);

      const [statsData, empData, trendData, checksData, deptData] = await Promise.all([
        statsRes.json(),
        empRes.json(),
        trendRes.json(),
        checksRes.json(),
        deptRes.json()
      ]);

      setStats(statsData);
      setEmployees(empData);
      setTrend(trendData);
      setChecks(checksData);
      setDepartments(deptData);
      setLastRefresh(new Date().toLocaleTimeString());
      setLoading(false);
    } catch (err) {
      console.error("Fetch error:", err);
      setLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // Refresh when WebSocket update arrives
  useEffect(() => {
    if (latestUpdate) {
      fetchAll();
    }
  }, [latestUpdate, fetchAll]);

  // Auto refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  if (loading) {
    return (
      <div
        className="flex items-center justify-center h-screen"
        style={{ fontFamily: "var(--font-mono)", color: "var(--amber)" }}
      >
        <div className="text-center">
          <div className="text-2xl mb-3 animate-blink">⬡</div>
          <p>Connecting to IndustriGuard backend...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-screen-2xl mx-auto">
      {/* Last refresh indicator */}
      {lastRefresh && (
        <p
          className="text-xs mb-4"
          style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
        >
          Last updated: {lastRefresh}
          {latestUpdate && (
            <span style={{ color: "var(--green)" }}>
              {" "}· Live update received from {latestUpdate.employee_id}
            </span>
          )}
        </p>
      )}

      {/* Stat cards */}
      <StatCards stats={stats} />

      {/* Employee status table — full width */}
      <EmployeeTable employees={employees} latestUpdate={latestUpdate} />

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <TrendChart trend={trend} />
        <DepartmentChart departments={departments} />
      </div>

      {/* Check history */}
      <CheckHistory checks={checks} />
    </div>
  );
}