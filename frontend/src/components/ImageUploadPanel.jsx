import { useState, useEffect, useRef, useCallback } from "react";

const API = "http://localhost:5000";

// ── PPE item definition (same 5 items as live camera) ──────────────
const PPE_ITEMS = [
  { key: "has_helmet",  label: "Helmet"  },
  { key: "has_vest",    label: "Safety Vest" },
  { key: "has_gloves",  label: "Gloves"  },
  { key: "has_goggles", label: "Glasses" },
  { key: "has_boots",   label: "Boots"   },
];

export default function ImageUploadPanel() {
  const [employees,    setEmployees]    = useState([]);
  const [selectedEmp,  setSelectedEmp]  = useState("");
  const [file,         setFile]         = useState(null);
  const [preview,      setPreview]      = useState(null);
  const [dragging,     setDragging]     = useState(false);
  const [loading,      setLoading]      = useState(false);
  const [result,       setResult]       = useState(null);
  const [error,        setError]        = useState(null);
  const inputRef = useRef(null);

  // Fetch employee list on mount
  useEffect(() => {
    fetch(`${API}/api/employees/list`)
      .then((r) => r.json())
      .then((data) => {
        setEmployees(Array.isArray(data) ? data : []);
        if (data.length > 0) setSelectedEmp(data[0].id);
      })
      .catch(() => setEmployees([]));
  }, []);

  // Build preview URL when file changes
  useEffect(() => {
    if (!file) { setPreview(null); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const acceptFile = useCallback((f) => {
    if (!f) return;
    const ok = ["image/jpeg", "image/png", "image/webp", "image/jpg"];
    if (!ok.includes(f.type)) {
      setError("Unsupported format. Please upload a JPEG, PNG, or WebP image.");
      return;
    }
    setFile(f);
    setResult(null);
    setError(null);
  }, []);

  const onInputChange  = (e) => acceptFile(e.target.files?.[0]);
  const onDrop         = (e) => { e.preventDefault(); setDragging(false); acceptFile(e.dataTransfer.files?.[0]); };
  const onDragOver     = (e) => { e.preventDefault(); setDragging(true); };
  const onDragLeave    = ()  => setDragging(false);

  const handleAnalyse = async () => {
    if (!file) { setError("Please select an image first."); return; }
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const form = new FormData();
      form.append("image", file);
      form.append("employee_id", selectedEmp);

      const res  = await fetch(`${API}/api/detect-image`, { method: "POST", body: form });
      const data = await res.json();

      if (!res.ok) {
        setError(data.error || `Server error ${res.status}`);
      } else {
        setResult(data);
      }
    } catch (e) {
      setError("Could not reach the backend. Make sure it is running on http://localhost:5000.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  // ── Derived display values ──────────────────────────────────────
  const isReady      = result?.result === "READY";
  const safetyPct    = result?.safety_percentage ?? 0;
  const arcColor     = isReady ? "var(--green)" : "var(--red)";

  return (
    <div className="p-6 max-w-screen-2xl mx-auto animate-fade-in">

      {/* ── Two-column layout: Upload left, Results right ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", alignItems: "start" }}>

        {/* ══════════════════════════════════════════════════
            LEFT COLUMN — Upload controls
        ══════════════════════════════════════════════════ */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

          {/* Panel header */}
          <div
            style={{
              background:   "var(--bg-card)",
              border:       "1px solid var(--border)",
              borderRadius: "6px",
              padding:      "20px 24px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
              <span style={{ fontSize: "20px" }}>📷</span>
              <h2
                style={{
                  fontFamily: "var(--font-display)",
                  color:      "var(--amber)",
                  fontSize:   "18px",
                  fontWeight: 700,
                  letterSpacing: "0.04em",
                }}
              >
                Image Upload Detection
              </h2>
            </div>
            <p style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)", fontSize: "12px", lineHeight: 1.6 }}>
              Upload a worker photo to run PPE compliance analysis using the same detection
              pipeline as the live camera. The result is saved to the dashboard automatically.
            </p>
          </div>

          {/* Employee selector */}
          <div
            style={{
              background:   "var(--bg-card)",
              border:       "1px solid var(--border)",
              borderRadius: "6px",
              padding:      "16px 20px",
            }}
          >
            <label
              htmlFor="emp-select"
              style={{
                display:     "block",
                fontFamily:  "var(--font-mono)",
                fontSize:    "11px",
                color:       "var(--text-secondary)",
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                marginBottom: "8px",
              }}
            >
              Employee
            </label>
            <select
              id="emp-select"
              value={selectedEmp}
              onChange={(e) => setSelectedEmp(e.target.value)}
              style={{
                width:       "100%",
                background:  "var(--bg-elevated)",
                border:      "1px solid var(--border-bright)",
                color:       "var(--text-primary)",
                fontFamily:  "var(--font-ui)",
                fontSize:    "14px",
                padding:     "9px 12px",
                borderRadius: "4px",
                outline:     "none",
                cursor:      "pointer",
              }}
            >
              {employees.length === 0 ? (
                <option value="">Loading employees…</option>
              ) : (
                employees.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.id} — {e.name} ({e.department})
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Drag-and-drop upload zone */}
          <div
            id="upload-dropzone"
            onClick={() => inputRef.current?.click()}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            style={{
              background:   dragging ? "rgba(245,158,11,0.08)" : "var(--bg-card)",
              border:       `2px dashed ${dragging ? "var(--amber)" : file ? "var(--green-dim)" : "var(--border-bright)"}`,
              borderRadius: "6px",
              padding:      "32px 20px",
              textAlign:    "center",
              cursor:       "pointer",
              transition:   "all 0.2s ease",
              minHeight:    "160px",
              display:      "flex",
              flexDirection: "column",
              alignItems:   "center",
              justifyContent: "center",
              gap:          "10px",
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={onInputChange}
              style={{ display: "none" }}
              id="image-file-input"
            />

            {file ? (
              <>
                <span style={{ fontSize: "32px" }}>✅</span>
                <p style={{ fontFamily: "var(--font-mono)", color: "var(--green)", fontSize: "13px" }}>
                  {file.name}
                </p>
                <p style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)", fontSize: "11px" }}>
                  Click to change image
                </p>
              </>
            ) : (
              <>
                <span style={{ fontSize: "36px", opacity: dragging ? 1 : 0.5 }}>🖼️</span>
                <p
                  style={{
                    fontFamily: "var(--font-display)",
                    color:      dragging ? "var(--amber)" : "var(--text-secondary)",
                    fontSize:   "15px",
                    fontWeight: 600,
                  }}
                >
                  {dragging ? "Drop image here" : "Drag & Drop or Click to Upload"}
                </p>
                <p style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)", fontSize: "11px" }}>
                  JPEG · PNG · WebP
                </p>
              </>
            )}
          </div>

          {/* Action buttons */}
          <div style={{ display: "flex", gap: "10px" }}>
            <button
              id="analyse-btn"
              onClick={handleAnalyse}
              disabled={!file || loading}
              style={{
                flex:        1,
                background:  (!file || loading) ? "transparent" : "var(--amber-glow)",
                border:      `1px solid ${(!file || loading) ? "var(--border)" : "var(--amber-dim)"}`,
                color:       (!file || loading) ? "var(--text-muted)" : "var(--amber)",
                fontFamily:  "var(--font-mono)",
                fontSize:    "13px",
                fontWeight:  700,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                padding:     "11px 20px",
                borderRadius: "4px",
                cursor:      (!file || loading) ? "not-allowed" : "pointer",
                transition:  "all 0.2s ease",
              }}
            >
              {loading ? "⟳  Analysing…" : "⚡  Analyse PPE"}
            </button>

            {(file || result) && (
              <button
                id="reset-btn"
                onClick={handleReset}
                style={{
                  background:  "transparent",
                  border:      "1px solid var(--border)",
                  color:       "var(--text-secondary)",
                  fontFamily:  "var(--font-mono)",
                  fontSize:    "12px",
                  padding:     "11px 16px",
                  borderRadius: "4px",
                  cursor:      "pointer",
                  transition:  "all 0.2s ease",
                }}
              >
                Reset
              </button>
            )}
          </div>

          {/* Error message */}
          {error && (
            <div
              style={{
                background:   "var(--red-glow)",
                border:       "1px solid var(--red-dim)",
                borderRadius: "4px",
                padding:      "12px 16px",
                fontFamily:   "var(--font-mono)",
                color:        "var(--red)",
                fontSize:     "12px",
              }}
            >
              ⚠ {error}
            </div>
          )}

          {/* Image preview (before analysis) */}
          {preview && !result && (
            <div
              style={{
                background:   "var(--bg-card)",
                border:       "1px solid var(--border)",
                borderRadius: "6px",
                overflow:     "hidden",
              }}
            >
              <div
                style={{
                  padding:    "10px 14px",
                  borderBottom: "1px solid var(--border)",
                  fontFamily: "var(--font-mono)",
                  fontSize:   "11px",
                  color:      "var(--text-secondary)",
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                }}
              >
                Preview — Unanalysed
              </div>
              <img
                src={preview}
                alt="Upload preview"
                style={{ width: "100%", display: "block", maxHeight: "300px", objectFit: "contain" }}
              />
            </div>
          )}
        </div>

        {/* ══════════════════════════════════════════════════
            RIGHT COLUMN — Detection Results
        ══════════════════════════════════════════════════ */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

          {/* Loading skeleton */}
          {loading && (
            <div
              style={{
                background:   "var(--bg-card)",
                border:       "1px solid var(--border)",
                borderRadius: "6px",
                padding:      "48px 24px",
                textAlign:    "center",
              }}
            >
              <div
                style={{
                  width:        "48px",
                  height:       "48px",
                  border:       "3px solid var(--border-bright)",
                  borderTop:    "3px solid var(--amber)",
                  borderRadius: "50%",
                  animation:    "spin 0.8s linear infinite",
                  margin:       "0 auto 16px",
                }}
              />
              <p style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)", fontSize: "13px" }}>
                Running PPE detection pipeline…
              </p>
              <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
          )}

          {/* Results panel */}
          {result && !loading && (
            <>
              {/* Annotated image */}
              <div
                style={{
                  background:   "var(--bg-card)",
                  border:       `1px solid ${isReady ? "var(--green-dim)" : "var(--red-dim)"}`,
                  borderRadius: "6px",
                  overflow:     "hidden",
                  boxShadow:    `0 0 20px ${isReady ? "rgba(16,185,129,0.1)" : "rgba(239,68,68,0.1)"}`,
                }}
              >
                <div
                  style={{
                    padding:      "10px 16px",
                    borderBottom: `1px solid ${isReady ? "var(--green-dim)" : "var(--red-dim)"}`,
                    display:      "flex",
                    alignItems:   "center",
                    justifyContent: "space-between",
                  }}
                >
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-secondary)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                    Annotated Result
                  </span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)" }}>
                    {result.detection_count} object{result.detection_count !== 1 ? "s" : ""} detected
                  </span>
                </div>
                <img
                  src={`data:image/jpeg;base64,${result.annotated_image}`}
                  alt="Annotated PPE detection result"
                  style={{ width: "100%", display: "block", maxHeight: "340px", objectFit: "contain" }}
                />
              </div>

              {/* Safety score + status */}
              <div
                style={{
                  background:   "var(--bg-card)",
                  border:       "1px solid var(--border)",
                  borderRadius: "6px",
                  padding:      "20px 24px",
                  display:      "flex",
                  alignItems:   "center",
                  gap:          "24px",
                }}
              >
                {/* Circular score gauge */}
                <div style={{ position: "relative", flexShrink: 0 }}>
                  <svg width="88" height="88" viewBox="0 0 88 88">
                    {/* Track */}
                    <circle cx="44" cy="44" r="36" fill="none" stroke="var(--border-bright)" strokeWidth="7" />
                    {/* Progress arc */}
                    <circle
                      cx="44" cy="44" r="36"
                      fill="none"
                      stroke={arcColor}
                      strokeWidth="7"
                      strokeLinecap="round"
                      strokeDasharray={`${2 * Math.PI * 36}`}
                      strokeDashoffset={`${2 * Math.PI * 36 * (1 - safetyPct / 100)}`}
                      transform="rotate(-90 44 44)"
                      style={{ transition: "stroke-dashoffset 0.6s ease" }}
                    />
                  </svg>
                  <div
                    style={{
                      position:  "absolute",
                      inset:     0,
                      display:   "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexDirection: "column",
                    }}
                  >
                    <span style={{ fontFamily: "var(--font-display)", color: arcColor, fontSize: "18px", fontWeight: 800, lineHeight: 1 }}>
                      {safetyPct}%
                    </span>
                  </div>
                </div>

                {/* Employee info + verdict */}
                <div style={{ flex: 1 }}>
                  <p style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)", fontSize: "16px", fontWeight: 700, marginBottom: "3px" }}>
                    {result.employee_name}
                  </p>
                  <p style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)", fontSize: "11px", marginBottom: "12px" }}>
                    {result.employee_id} · {result.department} · {result.role}
                  </p>
                  <span className={isReady ? "badge-ready" : "badge-not-ready"}>
                    {result.result}
                  </span>
                  <p style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)", fontSize: "11px", marginTop: "8px" }}>
                    {result.message}
                  </p>
                </div>
              </div>

              {/* PPE item breakdown table */}
              <div
                style={{
                  background:   "var(--bg-card)",
                  border:       "1px solid var(--border)",
                  borderRadius: "6px",
                  overflow:     "hidden",
                }}
              >
                <div
                  style={{
                    padding:      "10px 16px",
                    borderBottom: "1px solid var(--border)",
                    fontFamily:   "var(--font-mono)",
                    fontSize:     "11px",
                    color:        "var(--text-secondary)",
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                  }}
                >
                  PPE Compliance Breakdown
                </div>
                <table className="ig-table">
                  <thead>
                    <tr>
                      <th>PPE Item</th>
                      <th>Status</th>
                      <th>Recognition</th>
                    </tr>
                  </thead>
                  <tbody>
                    {PPE_ITEMS.map(({ key, label }) => {
                      const detected = !!result[key];
                      return (
                        <tr key={key}>
                          <td style={{ fontFamily: "var(--font-ui)", fontWeight: 600 }}>{label}</td>
                          <td>
                            <span
                              style={{
                                fontFamily:   "var(--font-mono)",
                                fontSize:     "12px",
                                color:        detected ? "var(--green)" : "var(--red)",
                                background:   detected ? "var(--green-glow)" : "var(--red-glow)",
                                border:       `1px solid ${detected ? "var(--green-dim)" : "var(--red-dim)"}`,
                                padding:      "2px 9px",
                                borderRadius: "2px",
                              }}
                            >
                              {detected ? "Detected" : "Missing"}
                            </span>
                          </td>
                          <td style={{ fontFamily: "var(--font-mono)", fontSize: "18px", color: detected ? "var(--green)" : "var(--red)" }}>
                            {detected ? "✓" : "✗"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Footer: saved confirmation */}
              <div
                style={{
                  background:   "var(--green-glow)",
                  border:       "1px solid var(--green-dim)",
                  borderRadius: "4px",
                  padding:      "10px 16px",
                  display:      "flex",
                  alignItems:   "center",
                  gap:          "10px",
                }}
              >
                <span style={{ color: "var(--green)", fontSize: "14px" }}>✓</span>
                <span style={{ fontFamily: "var(--font-mono)", color: "var(--green)", fontSize: "12px" }}>
                  Result saved to dashboard · Log ID #{result.log_id} · {result.timestamp}
                </span>
              </div>
            </>
          )}

          {/* Empty state (no result yet, not loading) */}
          {!result && !loading && (
            <div
              style={{
                background:   "var(--bg-card)",
                border:       "1px solid var(--border)",
                borderRadius: "6px",
                padding:      "64px 24px",
                textAlign:    "center",
                display:      "flex",
                flexDirection: "column",
                alignItems:   "center",
                gap:          "12px",
                minHeight:    "300px",
                justifyContent: "center",
              }}
            >
              <span style={{ fontSize: "40px", opacity: 0.3 }}>🔍</span>
              <p style={{ fontFamily: "var(--font-display)", color: "var(--text-muted)", fontSize: "15px", fontWeight: 600 }}>
                No Analysis Yet
              </p>
              <p style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)", fontSize: "12px", maxWidth: "260px", lineHeight: 1.6 }}>
                Upload a worker photo and click "Analyse PPE" to run the detection pipeline.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
