import * as XLSX from "xlsx";

function safeSheetName(name) {
  const cleaned = String(name || "")
    .replace(/[\[\]\*\/\\\?\:]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return (cleaned || "Sheet").slice(0, 31);
}

function toYesNo(v) {
  return v ? "Yes" : "No";
}

function calcSafetyPercentage(hasHelmet, hasVest, hasGloves, hasGoggles, hasBoots) {
  const present = [!!hasHelmet, !!hasVest, !!hasGloves, !!hasGoggles, !!hasBoots].filter(Boolean).length;
  return Math.round((present / 5) * 100);
}

export function buildDashboardWorkbook({ stats, employees, trend, departments, checks }) {
  const wb = XLSX.utils.book_new();

  // Workers (requested layout: rows=workers, columns=Name/Helmet/Vest/Safety%/Status)
  const workers = (Array.isArray(employees) ? employees : [])
    .slice()
    .sort((a, b) => String(a.employee_name || "").localeCompare(String(b.employee_name || "")))
    .map((e) => ({
      name: e.employee_name ?? "",
      helmet: toYesNo(e.has_helmet),
      vest: toYesNo(e.has_vest),
      gloves: toYesNo(e.has_gloves),
      goggles: toYesNo(e.has_goggles),
      boots: toYesNo(e.has_boots),
      safety_percentage: calcSafetyPercentage(e.has_helmet, e.has_vest, e.has_gloves, e.has_goggles, e.has_boots),
      status: e.status ?? "",
    }));

  const workersWs = XLSX.utils.json_to_sheet(workers, {
    header: ["name", "helmet", "vest", "gloves", "goggles", "boots", "safety_percentage", "status"],
  });
  XLSX.utils.book_append_sheet(wb, workersWs, safeSheetName("Workers"));

  // Stats (flatten into two columns for readability)
  const statsRows = [];
  if (stats?.today) {
    statsRows.push(["Today", ""]);
    statsRows.push(["total_checks", stats.today.total_checks ?? ""]);
    statsRows.push(["ready", stats.today.ready ?? ""]);
    statsRows.push(["not_ready", stats.today.not_ready ?? ""]);
    statsRows.push(["ready_percentage", stats.today.ready_percentage ?? ""]);
    statsRows.push(["", ""]);
  }
  if (stats?.current) {
    statsRows.push(["Current", ""]);
    statsRows.push(["total_employees", stats.current.total_employees ?? ""]);
    statsRows.push(["ready", stats.current.ready ?? ""]);
    statsRows.push(["not_ready", stats.current.not_ready ?? ""]);
    statsRows.push(["", ""]);
  }
  if (stats?.ppe_violations) {
    statsRows.push(["PPE violations (today)", ""]);
    statsRows.push(["no_helmet", stats.ppe_violations.no_helmet ?? ""]);
    statsRows.push(["no_vest", stats.ppe_violations.no_vest ?? ""]);
    statsRows.push(["no_gloves", stats.ppe_violations.no_gloves ?? ""]);
    statsRows.push(["no_goggles", stats.ppe_violations.no_goggles ?? ""]);
    statsRows.push(["no_boots", stats.ppe_violations.no_boots ?? ""]);
  }
  const statsWs = XLSX.utils.aoa_to_sheet(
    statsRows.length ? statsRows : [["No stats available", ""]]
  );
  XLSX.utils.book_append_sheet(wb, statsWs, safeSheetName("Stats"));

  // Trend
  const trendWs = XLSX.utils.json_to_sheet(Array.isArray(trend) ? trend : [], {
    header: ["hour", "ready", "not_ready"],
  });
  XLSX.utils.book_append_sheet(wb, trendWs, safeSheetName("Trend (24h)"));

  // Departments
  const departmentsWs = XLSX.utils.json_to_sheet(
    Array.isArray(departments) ? departments : [],
    { header: ["department", "ready", "not_ready"] }
  );
  XLSX.utils.book_append_sheet(wb, departmentsWs, safeSheetName("Departments"));

  // Recent checks
  const checksWs = XLSX.utils.json_to_sheet(Array.isArray(checks) ? checks : [], {
    header: [
      "id",
      "timestamp",
      "employee_id",
      "employee_name",
      "department",
      "role",
      "has_helmet",
      "has_vest",
      "has_gloves",
      "has_goggles",
      "has_boots",
      "missing_ppe",
      "status",
      "camera_id",
    ],
  });
  XLSX.utils.book_append_sheet(wb, checksWs, safeSheetName("Recent checks"));

  return wb;
}

export function workbookToBlob(workbook) {
  const out = XLSX.write(workbook, { bookType: "xlsx", type: "array" });
  return new Blob([out], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
}

export function formatDashboardExportFilename(date = new Date()) {
  const pad = (n) => String(n).padStart(2, "0");
  const yyyy = date.getFullYear();
  const mm = pad(date.getMonth() + 1);
  const dd = pad(date.getDate());
  const hh = pad(date.getHours());
  const min = pad(date.getMinutes());
  return `IndustriGuard_Dashboard_${yyyy}-${mm}-${dd}_${hh}${min}.xlsx`;
}

export function createAndClickDownload(url, filename) {
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || "dashboard.xlsx";
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  a.remove();
}
