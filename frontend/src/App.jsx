import { useState, useEffect, useRef, Fragment } from "react";
import axios from "axios";
import { QRCodeSVG } from "qrcode.react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

const api = axios.create({ baseURL: API_BASE });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("abp_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

function LoadingScreen({ fadingOut }) {
  return (
    <div className={`loading-screen ${fadingOut ? "fade-out" : ""}`}>
      <div className="track-wrap">
        <svg className="train" width="70" height="34" viewBox="0 0 70 34" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="8" width="26" height="16" rx="2" fill="#E8A33D" />
          <rect x="30" y="12" width="34" height="12" rx="2" fill="#8B96A5" />
          <circle className="wheel" cx="10" cy="27" r="4" fill="#171D26" stroke="#8B96A5" strokeWidth="1.5" />
          <circle className="wheel" cx="22" cy="27" r="4" fill="#171D26" stroke="#8B96A5" strokeWidth="1.5" />
          <circle className="wheel" cx="40" cy="27" r="4" fill="#171D26" stroke="#8B96A5" strokeWidth="1.5" />
          <circle className="wheel" cx="56" cy="27" r="4" fill="#171D26" stroke="#8B96A5" strokeWidth="1.5" />
          <rect x="6" y="4" width="10" height="6" rx="1" fill="#3DBE6C" />
          <rect x="4" y="12" width="6" height="6" fill="#10141A" />
        </svg>
        <div className="rail-line"></div>
        <div className="sleepers"></div>
      </div>
      <div className="loading-text">LOADING BLOCK SCHEDULE...</div>
    </div>
  );
}

function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);
      const res = await axios.post(`${API_BASE}/auth/login`, formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      localStorage.setItem("abp_token", res.data.access_token);
      localStorage.setItem("abp_user", JSON.stringify(res.data));
      onLogin(res.data);
    } catch (err) {
      setError("Incorrect username or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-header">
          <div className="signal-dot"></div>
          <div>
            <h1>Automatic Block Planning</h1>
            <p>Sign in to continue</p>
          </div>
        </div>
        <label>
          Username
          <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {error && <div className="login-error">{error}</div>}
        <button type="submit" className="regen-btn" disabled={loading}>
          {loading ? "Signing in..." : "Sign In"}
        </button>
        <div className="login-hint">
          Try: admin / admin123 · engineer1 / pass123 · crew1 / pass123
        </div>
      </form>
    </div>
  );
}

function urgencyColor(level) {
  if (level === "Critical") return "#E5484D";
  if (level === "High") return "#E8A33D";
  if (level === "Medium") return "#8B96A5";
  return "#3DBE6C";
}

function blockTagClass(blockType) {
  if (blockType === "Integrated Block") return "block-tag tag-integrated";
  if (blockType === "Power Block") return "block-tag tag-power";
  return "block-tag tag-traffic";
}

function sectionLineColor(sectionId, weeklySchedule) {
  const blocksHere = weeklySchedule.filter((b) => b.section_id === sectionId);
  if (blocksHere.length === 0) return "#2A323D";
  if (blocksHere.some((b) => b.block_type === "Integrated Block")) return "#3DBE6C";
  if (blocksHere.some((b) => b.block_type === "Power Block")) return "#E5484D";
  return "#E8A33D";
}

const STATIONS = {
  Ludhiana: { x: 380, y: 150 },
  Jalandhar: { x: 570, y: 75 },
  Amritsar: { x: 740, y: 30 },
  Chandigarh: { x: 570, y: 225 },
  Ambala: { x: 740, y: 270 },
};

const CORRIDOR_LINES = [
  { section_id: "SEC1", from: "Ludhiana", to: "Jalandhar" },
  { section_id: "SEC2", from: "Jalandhar", to: "Amritsar" },
  { section_id: "SEC3", from: "Ludhiana", to: "Chandigarh" },
  { section_id: "SEC4", from: "Chandigarh", to: "Ambala" },
];

function CorridorMap({ weeklySchedule }) {
  return (
    <svg viewBox="0 0 820 300" width="100%" style={{ maxWidth: 820 }}>
      {CORRIDOR_LINES.map((line) => {
        const from = STATIONS[line.from];
        const to = STATIONS[line.to];
        const color = sectionLineColor(line.section_id, weeklySchedule);
        const midX = (from.x + to.x) / 2;
        const midY = (from.y + to.y) / 2;
        const blockCount = weeklySchedule.filter((b) => b.section_id === line.section_id).length;
        return (
          <g key={line.section_id}>
            <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke={color} strokeWidth="5" strokeLinecap="round" />
            <text x={midX} y={midY - 14} textAnchor="middle" fill={color} fontSize="12" fontFamily="JetBrains Mono, monospace" fontWeight="600">
              {line.section_id} {blockCount > 0 ? `(${blockCount})` : ""}
            </text>
          </g>
        );
      })}
      {Object.entries(STATIONS).map(([name, pos]) => (
        <g key={name}>
          <circle cx={pos.x} cy={pos.y} r="9" fill="#171D26" stroke="#8B96A5" strokeWidth="2" />
          <text x={pos.x} y={pos.y - 16} textAnchor="middle" fill="#E8ECF1" fontSize="13" fontFamily="Barlow Condensed, sans-serif" fontWeight="600">
            {name}
          </text>
        </g>
      ))}
    </svg>
  );
}

const URGENCIES = ["Low", "Medium", "High", "Critical"];
const SECTION_IDS = ["SEC1", "SEC2", "SEC3", "SEC4"];
const ALL_DEPARTMENTS = ["Engineering (P.Way)", "Signal & Telecommunication (S&T)", "Traction Distribution (TRD)"];

function App() {
  const [phase, setPhase] = useState("loading");
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("abp_user");
    return saved ? JSON.parse(saved) : null;
  });

  const [tasks, setTasks] = useState([]);
  const [completedTasks, setCompletedTasks] = useState([]);
  const [weeklySchedule, setWeeklySchedule] = useState([]);
  const [monthlySchedule, setMonthlySchedule] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [auditLog, setAuditLog] = useState([]);
  const [activeTab, setActiveTab] = useState("Weekly");
  const [showAddForm, setShowAddForm] = useState(false);
  const [uploadingTaskId, setUploadingTaskId] = useState(null);
  const [expandedTaskId, setExpandedTaskId] = useState(null);
  const [expandedBlockId, setExpandedBlockId] = useState(null);
  const [showAudit, setShowAudit] = useState(false);
  const [qrTaskId, setQrTaskId] = useState(null);
  const taskRowRefs = useRef({});

  const [newTask, setNewTask] = useState({
    department: user?.role === "department" ? user.department : ALL_DEPARTMENTS[0],
    section_id: SECTION_IDS[0],
    defect_type: "",
    urgency: "Medium",
    overdue_days: 0,
    estimated_duration_hours: 2,
  });

  const fetchData = async () => {
    try {
      const [tasksRes, completedRes, weeklyRes, monthlyRes, metricsRes] = await Promise.all([
        api.get("/tasks"),
        api.get("/tasks/completed"),
        api.get("/schedule/weekly"),
        api.get("/schedule/monthly"),
        api.get("/metrics"),
      ]);
      setTasks(tasksRes.data);
      setCompletedTasks(completedRes.data);
      setWeeklySchedule(weeklyRes.data);
      setMonthlySchedule(monthlyRes.data);
      setMetrics(metricsRes.data);

      if (user?.role === "admin") {
        const auditRes = await api.get("/audit");
        setAuditLog(auditRes.data);
      }
    } catch (err) {
      if (err.response?.status === 401) handleLogout();
    }
  };

  useEffect(() => {
    if (!user) return;
    fetchData();
    const fadeTimer = setTimeout(() => setPhase("fading"), 4400);
    const swapTimer = setTimeout(() => setPhase("dashboard"), 5000);
    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(swapTimer);
    };
  }, [user]);

  // Handle a QR-code scan landing: ?task=TASK001 in the URL auto-expands and scrolls to that task
  useEffect(() => {
    if (phase !== "dashboard") return;
    const params = new URLSearchParams(window.location.search);
    const taskParam = params.get("task");
    if (taskParam) {
      setExpandedTaskId(taskParam);
      setTimeout(() => {
        taskRowRefs.current[taskParam]?.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 300);
    }
  }, [phase, tasks]);

  const handleLogin = (userData) => {
    setUser(userData);
    setPhase("loading");
  };

  const handleLogout = () => {
    localStorage.removeItem("abp_token");
    localStorage.removeItem("abp_user");
    setUser(null);
  };

  const handleRegenerate = async () => {
    await api.post("/schedule/regenerate");
    fetchData();
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    const payload = {
      ...newTask,
      overdue_days: Number(newTask.overdue_days),
      estimated_duration_hours: Number(newTask.estimated_duration_hours),
    };
    await api.post("/tasks/add", payload);
    setShowAddForm(false);
    setNewTask({ ...newTask, defect_type: "" });
    fetchData();
  };

  const getLocation = () =>
    new Promise((resolve) => {
      if (!navigator.geolocation) return resolve({});
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
        () => resolve({}),
        { timeout: 4000 }
      );
    });

  const handlePhotoUpload = async (taskId, file) => {
    if (!file) return;
    setUploadingTaskId(taskId);
    try {
      const { lat, lon } = await getLocation();
      const formData = new FormData();
      formData.append("photo", file);
      if (lat) formData.append("lat", lat);
      if (lon) formData.append("lon", lon);
      await api.post(`/tasks/${taskId}/complete`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      fetchData();
    } finally {
      setUploadingTaskId(null);
    }
  };

  if (!user) return <LoginScreen onLogin={handleLogin} />;
  if (phase !== "dashboard") return <LoadingScreen fadingOut={phase === "fading"} />;

  const activeSchedule = activeTab === "Weekly" ? weeklySchedule : monthlySchedule;
  const canAddTask = user.role === "admin" || user.role === "department";
  const canUpload = user.role === "admin" || user.role === "field_crew";
  const canRegenerate = user.role === "admin";
  const canSeeAudit = user.role === "admin";
  const qrUrl = qrTaskId ? `${window.location.origin}${window.location.pathname}?task=${qrTaskId}` : "";

  return (
    <div className="dashboard dashboard-enter">
      <div className="header">
        <div className="header-title-block">
          <div className="signal-dot"></div>
          <div>
            <h1>Automatic Block Planning</h1>
            <p>Engineering (P.Way) · Signal &amp; Telecommunication (S&amp;T) · Traction Distribution (TRD)</p>
          </div>
        </div>
        <div className="header-actions">
          <div className="user-badge">
            <div className="user-name">{user.full_name || user.username}</div>
            <div className="user-role">{user.role.replace("_", " ")}{user.department ? ` · ${user.department}` : ""}</div>
          </div>
          {canSeeAudit && (
            <button className="secondary-btn" onClick={() => setShowAudit(!showAudit)}>
              {showAudit ? "Hide Audit Log" : "Audit Log"}
            </button>
          )}
          {canAddTask && (
            <button className="secondary-btn" onClick={() => setShowAddForm(!showAddForm)}>
              {showAddForm ? "Cancel" : "+ Add Task"}
            </button>
          )}
          {canRegenerate && (
            <button className="regen-btn" onClick={handleRegenerate}>Regenerate Schedule</button>
          )}
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </div>

      {showAddForm && canAddTask && (
        <form className="add-task-panel" onSubmit={handleAddTask}>
          <div className="form-row">
            <label>
              Department
              <select
                value={newTask.department}
                disabled={user.role === "department"}
                onChange={(e) => setNewTask({ ...newTask, department: e.target.value })}
              >
                {(user.role === "department" ? [user.department] : ALL_DEPARTMENTS).map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </label>
            <label>
              Section
              <select value={newTask.section_id} onChange={(e) => setNewTask({ ...newTask, section_id: e.target.value })}>
                {SECTION_IDS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
            <label>
              Urgency
              <select value={newTask.urgency} onChange={(e) => setNewTask({ ...newTask, urgency: e.target.value })}>
                {URGENCIES.map((u) => <option key={u} value={u}>{u}</option>)}
              </select>
            </label>
          </div>
          <div className="form-row">
            <label className="grow">
              Defect description
              <input type="text" required value={newTask.defect_type} onChange={(e) => setNewTask({ ...newTask, defect_type: e.target.value })} placeholder="e.g. Rail fracture near KM marker 42" />
            </label>
            <label>
              Overdue (days)
              <input type="number" min="0" value={newTask.overdue_days} onChange={(e) => setNewTask({ ...newTask, overdue_days: e.target.value })} />
            </label>
            <label>
              Duration (hrs)
              <input type="number" min="0.5" step="0.5" value={newTask.estimated_duration_hours} onChange={(e) => setNewTask({ ...newTask, estimated_duration_hours: e.target.value })} />
            </label>
            <button type="submit" className="regen-btn">Submit Task</button>
          </div>
        </form>
      )}

      {showAudit && canSeeAudit && (
        <div className="section audit-section">
          <h2>Audit Log</h2>
          <div className="audit-list">
            {auditLog.map((ev) => (
              <div className="audit-row" key={ev.event_id}>
                <span className="audit-action">{ev.action}</span>
                <span className="audit-detail">{ev.detail}</span>
                <span className="audit-meta">{ev.actor} · {new Date(ev.timestamp).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {metrics && (
        <div className="kpi-strip">
          <div className="kpi-card"><div className="kpi-value">{metrics.pending_tasks}</div><div className="kpi-label">PENDING TASKS</div></div>
          <div className="kpi-card"><div className="kpi-value" style={{ color: "var(--red)" }}>{metrics.critical_pending}</div><div className="kpi-label">CRITICAL PENDING</div></div>
          <div className="kpi-card"><div className="kpi-value" style={{ color: "var(--green)" }}>{metrics.integrated_blocks}</div><div className="kpi-label">INTEGRATED BLOCKS</div></div>
          <div className="kpi-card"><div className="kpi-value">{metrics.completed_tasks}</div><div className="kpi-label">COMPLETED</div></div>
          <div className="kpi-card"><div className="kpi-value">{metrics.avg_priority_score}</div><div className="kpi-label">AVG PRIORITY SCORE</div></div>
        </div>
      )}

      <div className="section">
        <h2>Corridor Overview</h2>
        <p className="section-hint">Line color shows this week's block status per section — grey means no block scheduled.</p>
        <div className="corridor-map-wrap">
          <CorridorMap weeklySchedule={weeklySchedule} />
          <div className="corridor-legend">
            <span><i style={{ background: "#2A323D" }}></i> No block</span>
            <span><i style={{ background: "#E8A33D" }}></i> Traffic Block</span>
            <span><i style={{ background: "#E5484D" }}></i> Power Block</span>
            <span><i style={{ background: "#3DBE6C" }}></i> Integrated Block</span>
          </div>
        </div>
      </div>

      <div className="section">
        <h2>Unified Maintenance Task Queue</h2>
        <p className="section-hint">Click a row to see why the scheduler ranked it that way. Use the QR button for field-crew scan-to-complete.</p>
        <table className="data-table">
          <thead>
            <tr>
              <th>Task ID</th><th>Department</th><th>Defect</th><th>Urgency</th><th>Overdue</th><th>Score</th>
              {canUpload && <th>Proof of Work</th>}
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <>
                <tr
                  key={t.task_id}
                  ref={(el) => (taskRowRefs.current[t.task_id] = el)}
                  className="clickable-row"
                  onClick={() => setExpandedTaskId(expandedTaskId === t.task_id ? null : t.task_id)}
                >
                  <td>{t.task_id}</td>
                  <td>{t.department}</td>
                  <td>{t.defect_type}</td>
                  <td><span className="urgency-dot" style={{ background: urgencyColor(t.urgency) }}></span>{t.urgency}</td>
                  <td>{t.overdue_days}</td>
                  <td className="score">{t.priority_score} <span className="expand-caret">{expandedTaskId === t.task_id ? "▲" : "▼"}</span></td>
                  {canUpload && (
                    <td onClick={(e) => e.stopPropagation()}>
                      <div className="proof-cell">
                        <label className="upload-btn">
                          {uploadingTaskId === t.task_id ? "Uploading..." : "Upload & Mark Done"}
                          <input type="file" accept="image/*" hidden onChange={(e) => handlePhotoUpload(t.task_id, e.target.files[0])} />
                        </label>
                        <button className="qr-btn" onClick={() => setQrTaskId(t.task_id)} title="Show QR code for field crew scan">QR</button>
                      </div>
                    </td>
                  )}
                </tr>
                {expandedTaskId === t.task_id && (
                  <tr className="reasoning-row">
                    <td colSpan={canUpload ? 7 : 6}>
                      <div className="reasoning-box"><strong>Why this score:</strong> {t.reasoning}</div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      <div className="section">
        <div className="section-header-row">
          <h2>Block Schedule</h2>
          <div className="tabs">
            <button className={activeTab === "Weekly" ? "tab active" : "tab"} onClick={() => setActiveTab("Weekly")}>Weekly</button>
            <button className={activeTab === "Monthly" ? "tab active" : "tab"} onClick={() => setActiveTab("Monthly")}>Monthly</button>
          </div>
        </div>
        <p className="section-hint">Click a block to see why it was scheduled and merged this way.</p>
        <table className="data-table">
          <thead>
            <tr><th>Block ID</th><th>Section</th><th>Type</th><th>Start</th><th>Tasks Covered</th></tr>
          </thead>
          <tbody>
            {activeSchedule.map((b) => (
              <>
                <tr key={b.block_id} className="clickable-row" onClick={() => setExpandedBlockId(expandedBlockId === b.block_id ? null : b.block_id)}>
                  <td>{b.block_id}</td>
                  <td>{b.section_id}</td>
                  <td><span className={blockTagClass(b.block_type)}>{b.block_type}</span></td>
                  <td>{new Date(b.start_time).toLocaleString()}</td>
                  <td>{b.tasks_covered.join(", ")} <span className="expand-caret">{expandedBlockId === b.block_id ? "▲" : "▼"}</span></td>
                </tr>
                {expandedBlockId === b.block_id && (
                  <tr className="reasoning-row">
                    <td colSpan={5}>
                      <div className="reasoning-box"><strong>Why this block:</strong> {b.reasoning}</div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {completedTasks.length > 0 && (
        <div className="section">
          <h2>Completed Work Log</h2>
          <div className="completed-grid">
            {completedTasks.map((t) => (
              <div className="completed-card" key={t.task_id}>
                <img src={`${API_BASE}${t.completion_photo}`} alt={t.task_id} />
                <div className="completed-card-body">
                  <div className="completed-card-id">{t.task_id}</div>
                  <div className="completed-card-dept">{t.department}</div>
                  <div className="completed-card-time">
                    {t.completed_at ? new Date(t.completed_at).toLocaleString() : ""}
                    {t.completion_lat && t.completion_lon ? ` · ${t.completion_lat.toFixed(4)}, ${t.completion_lon.toFixed(4)}` : ""}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {qrTaskId && (
        <div className="qr-modal-backdrop" onClick={() => setQrTaskId(null)}>
          <div className="qr-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Scan to Complete {qrTaskId}</h3>
            <div className="qr-code-box">
              <QRCodeSVG value={qrUrl} size={220} bgColor="#FFFFFF" fgColor="#10141A" />
            </div>
            <p className="qr-hint">Field crew scans this on their phone to jump straight to the upload screen for this task.</p>
            <button className="secondary-btn" onClick={() => setQrTaskId(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;