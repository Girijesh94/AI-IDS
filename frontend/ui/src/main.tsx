import React, {
  Component,
  lazy,
  Suspense,
  useEffect,
  useRef,
  useState,
} from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  ArrowDownLeft,
  ArrowRight,
  ArrowUpRight,
  Boxes,
  Check,
  ChevronRight,
  CircleHelp,
  Database,
  Eye,
  FileText,
  Fingerprint,
  Layers,
  LockKeyhole,
  Network,
  Pause,
  Play,
  Radio,
  RefreshCw,
  Search,
  Shield,
  Terminal,
  X,
} from "lucide-react";
import "@fontsource/dm-sans/latin-400.css";
import "@fontsource/dm-sans/latin-500.css";
import "@fontsource/dm-sans/latin-600.css";
import "@fontsource/dm-sans/latin-700.css";
import "@fontsource/ibm-plex-mono/latin-400.css";
import "./style.css";
import { useWebGLSupport } from "./graphics";

const Scene = lazy(() => import("./Scene"));
const LiquidLogo = lazy(() => import("./LiquidLogo"));
type Row = Record<string, any>;
type Snapshot = {
  health: Row;
  network: Row;
  incidents: Row[];
  benchmarks: Row[];
  progress: Row;
  model: Row;
  flows: Row[];
  commands: Row[];
  logs: Row[];
};
const endpoints = [
  "health",
  "network-status",
  "incidents?limit=100",
  "benchmarks",
  "data-progress",
  "canonical-model",
  "network-flows?limit=100",
  "cmd-detections?limit=100",
  "system-logs?limit=100",
];
const count = (v: number | undefined) => (v == null ? "—" : v.toLocaleString());
const percent = (v: number | undefined, digits = 2) =>
  v == null ? "—" : `${(v * 100).toFixed(digits)}%`;
const time = (v: number) =>
  v
    ? new Date(v * 1000).toLocaleString([], {
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : "—";
const human = (v: string | undefined) =>
  (v || "unavailable").replaceAll("_", " ");
async function api(path: string, options?: RequestInit) {
  const response = await fetch("/api/" + path, {
    signal: AbortSignal.timeout(10000),
    ...options,
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}
class GraphicsBoundary extends Component<
  { children: React.ReactNode; fallback: React.ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}
function StaticLogo() {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <path
        d="M32 5 54 17v27L32 59 10 44V17Zm0 10L19 23v16l13 9 13-9V23Z"
        fill="currentColor"
      />
      <path d="m32 24 8 5v9l-8 5-8-5v-9Z" fill="currentColor" />
    </svg>
  );
}
function Pill({
  children,
  tone = "",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return (
    <span className={"pill " + tone}>
      <i />
      {children}
    </span>
  );
}
function Empty({ children }: { children: React.ReactNode }) {
  return (
    <div className="empty">
      <Fingerprint size={28} />
      <p>{children}</p>
    </div>
  );
}
function Table({
  heads,
  children,
}: {
  heads: string[];
  children: React.ReactNode;
}) {
  return (
    <div
      className="table-scroll"
      tabIndex={0}
      aria-label="Scrollable data table"
    >
      <table>
        <thead>
          <tr>
            {heads.map((h) => (
              <th key={h} scope="col">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
function HoverText({ text }: { text: string }) {
  return (
    <span className="hover-text" aria-label={text}>
      {Array.from(text).map((c, i) => (
        <span
          aria-hidden="true"
          key={i}
          style={{ "--i": i } as React.CSSProperties}
        >
          {c === " " ? "\u00a0" : c}
        </span>
      ))}
    </span>
  );
}
function Magnet({
  children,
  className = "",
  onClick,
  href,
}: {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  href?: string;
}) {
  const ref = useRef<HTMLAnchorElement & HTMLButtonElement>(null);
  const props = {
    className: "magnet " + className,
    onPointerMove: (e: React.PointerEvent) => {
      if (
        matchMedia("(prefers-reduced-motion: reduce)").matches ||
        document.documentElement.dataset.motion === "off" ||
        e.pointerType !== "mouse"
      )
        return;
      const r = e.currentTarget.getBoundingClientRect();
      ref.current?.style.setProperty(
        "--mx",
        `${(e.clientX - r.left - r.width / 2) * 0.13}px`,
      );
      ref.current?.style.setProperty(
        "--my",
        `${(e.clientY - r.top - r.height / 2) * 0.13}px`,
      );
    },
    onPointerLeave: () => {
      ref.current?.style.setProperty("--mx", "0px");
      ref.current?.style.setProperty("--my", "0px");
    },
    onClick,
  };
  return href ? (
    <a ref={ref} href={href} {...props}>
      {children}
    </a>
  ) : (
    <button ref={ref} {...props}>
      {children}
    </button>
  );
}
function Sensor({ animated }: { animated: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const webgl = useWebGLSupport();
  const [xray, setXray] = useState(false);
  const [pinned, setPinned] = useState(false);
  const pointer = useRef({
    x: 0,
    y: 0,
    inside: false,
    ripple: 0,
    rx: 0,
    ry: 0,
  });
  const [ripple, setRipple] = useState(0);
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([e]) => setVisible(e.isIntersecting),
      { threshold: 0.1 },
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  const fallback = (
    <div className="static-sensor">
      <div />
      <div />
      <Shield size={82} strokeWidth={0.7} />
    </div>
  );
  return (
    <div
      className="sensor"
      ref={ref}
      data-xray={xray || pinned}
      onPointerMove={(e) => {
        if (!animated || e.pointerType !== "mouse") return;
        const r = e.currentTarget.getBoundingClientRect();
        pointer.current.x = ((e.clientX - r.left) / r.width) * 2 - 1;
        pointer.current.y = -(((e.clientY - r.top) / r.height) * 2 - 1);
        pointer.current.inside = true;
        e.currentTarget.style.setProperty(
          "--px",
          `${((e.clientX - r.left) / r.width) * 100}%`,
        );
        e.currentTarget.style.setProperty(
          "--py",
          `${((e.clientY - r.top) / r.height) * 100}%`,
        );
      }}
      onPointerEnter={(e) => {
        if (e.pointerType === "mouse") setXray(true);
      }}
      onPointerLeave={() => {
        setXray(false);
        pointer.current.inside = false;
      }}
      onClick={(e) => {
        if (!animated || (e.target as HTMLElement).closest("button")) return;
        const bounds = e.currentTarget.getBoundingClientRect();
        const x = (e.clientX - bounds.left) / bounds.width;
        const y = (e.clientY - bounds.top) / bounds.height;
        e.currentTarget.style.setProperty("--px", `${x * 100}%`);
        e.currentTarget.style.setProperty("--py", `${y * 100}%`);
        pointer.current.ripple = performance.now() / 1000;
        pointer.current.rx = (x * 2 - 1) * 3;
        pointer.current.ry = -(y * 2 - 1) * 2;
        setRipple((v) => v + 1);
      }}
    >
      <div className="sensor-grid" />
      <div className="sensor-label mono">
        <span className="cross">+</span> SENSOR FIELD <span>01 / LOCAL</span>
      </div>
      {webgl && visible ? (
        <GraphicsBoundary fallback={fallback}>
          <Suspense fallback={fallback}>
            <Scene
              pointer={pointer}
              xray={xray || pinned}
              animated={animated}
            />
          </Suspense>
        </GraphicsBoundary>
      ) : (
        fallback
      )}
      {animated && ripple > 0 && <span key={ripple} className="click-ripple" />}
      <div className="sensor-coordinates mono">
        X / OBSERVE
        <br />Y / INVESTIGATE
        <br />Z / UNDERSTAND
      </div>
      <div className="sensor-bottom">
        <span className="mono">ABSTRACT SENSOR · NOT A TOPOLOGY MAP</span>
        <button
          className={"xray-button " + (pinned ? "selected" : "")}
          aria-pressed={pinned}
          onClick={() => setPinned((v) => !v)}
        >
          <Eye size={14} /> X-ray
        </button>
      </div>
    </div>
  );
}
function App() {
  const path = window.location.pathname;
  const view = /network[-_]flows/.test(path)
    ? "traffic"
    : /cmd[-_](history)|\/history/.test(path)
      ? "commands"
      : /system[-_]logs/.test(path)
        ? "logs"
        : "operations";
  const [tab, setTab] = useState(
    location.hash === "#model"
      ? "model"
      : location.hash === "#review"
        ? "review"
        : "overview",
  );
  const [data, setData] = useState<Snapshot | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [updated, setUpdated] = useState<Date>();
  const [message, setMessage] = useState("");
  const [motion, setMotion] = useState(
    !matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  const [foreground, setForeground] = useState(!document.hidden);
  const [token, setToken] = useState("");
  const [analyst, setAnalyst] = useState("local-operator");
  const [auth, setAuth] = useState(false);
  const priorFocus = useRef<HTMLElement | null>(null);
  useEffect(() => {
    if (!auth) priorFocus.current?.focus();
  }, [auth]);
  function openAuthorization() {
    priorFocus.current = document.activeElement as HTMLElement;
    setAuth(true);
  }
  const [eventId, setEventId] = useState(() => {
    const id = sessionStorage.getItem("ids-review-event") || "";
    sessionStorage.removeItem("ids-review-event");
    return id;
  });
  const [note, setNote] = useState("");
  const [outcome, setOutcome] = useState("0");
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const requestActive = useRef(false);
  const fetched = useRef<(Row | undefined)[]>([]);
  const reviewRef = useRef<HTMLElement>(null);
  async function refresh() {
    if (requestActive.current) return;
    requestActive.current = true;
    setBusy(true);
    const results = await Promise.allSettled(endpoints.map((e) => api(e)));
    const failures: string[] = [];
    results.forEach((r, i) => {
      if (r.status === "fulfilled") fetched.current[i] = r.value;
      else failures.push(`${endpoints[i].split("?")[0]}: ${r.reason.message}`);
    });
    const v = fetched.current;
    setData({
      health: v[0] || {},
      network: v[1] || {},
      incidents: v[2]?.incidents || [],
      benchmarks: v[3]?.reports || [],
      progress: v[4] || {},
      model: v[5] || {},
      flows: v[6]?.flows || [],
      commands: v[7]?.detections || [],
      logs: v[8]?.logs || [],
    });
    setErrors(failures);
    if (!failures.length) setUpdated(new Date());
    requestActive.current = false;
    setBusy(false);
  }
  useEffect(() => {
    refresh();
    const timer = window.setInterval(() => {
      if (!document.hidden) refresh();
    }, 15000);
    const onVisibility = () => {
      setForeground(!document.hidden);
      if (!document.hidden) refresh();
    };
    const onHash = () =>
      setTab(
        location.hash === "#model"
          ? "model"
          : location.hash === "#review"
            ? "review"
            : "overview",
      );
    const media = matchMedia("(prefers-reduced-motion: reduce)");
    const onMotion = () => setMotion(!media.matches);
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("hashchange", onHash);
    media.addEventListener("change", onMotion);
    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("hashchange", onHash);
      media.removeEventListener("change", onMotion);
    };
  }, []);
  useEffect(() => {
    document.documentElement.dataset.motion = motion ? "on" : "off";
  }, [motion]);
  const health = data?.health || {},
    network = data?.network || {};
  const active = network.capture === "running";
  const open = data?.incidents.filter((i) =>
    ["new", "investigating"].includes(i.state),
  ).length;
  async function write(endpoint: string, method: string, body: Row) {
    if (!token.trim()) {
      openAuthorization();
      throw Error("Enter your local API token to save changes.");
    }
    await api(endpoint, {
      method,
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token.trim(),
      },
      body: JSON.stringify({ ...body, analyst }),
    });
  }
  function review(id: string) {
    setEventId(id);
    location.hash = "review";
    setTab("review");
    requestAnimationFrame(() =>
      reviewRef.current?.scrollIntoView({
        behavior: motion ? "smooth" : "auto",
      }),
    );
  }
  const nav = [
    {
      key: "operations",
      href: "/operations",
      label: "Operations",
      icon: Boxes,
    },
    {
      key: "traffic",
      href: "/network-flows",
      label: "Network traffic",
      icon: Network,
    },
    {
      key: "commands",
      href: "/cmd-history",
      label: "Commands",
      icon: Terminal,
    },
    { key: "logs", href: "/system-logs", label: "System logs", icon: FileText },
  ];
  const title = nav.find((n) => n.key === view)?.label;
  function incidents() {
    return (
      <section className="panel incident-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">INVESTIGATE</span>
            <h2>
              Incident queue{" "}
              <span className="small-count">
                {count(data?.incidents.length)}
              </span>
            </h2>
          </div>
          <Pill tone={open ? "amber" : ""}>{count(open)} open</Pill>
        </div>
        <p className="panel-intro">
          Detections need investigation. An unflagged event is not proof of
          safety.
        </p>
        {!data ? (
          <Empty>Loading incidents…</Empty>
        ) : !data.incidents.length ? (
          <Empty>
            No incidents recorded. Incoming detections will appear here.
          </Empty>
        ) : (
          <Table
            heads={[
              "Evidence / last observed",
              "Severity",
              "Events",
              "Status",
              "Review",
            ]}
          >
            {data.incidents.map((i) => (
              <tr key={i.id}>
                <td className="evidence">
                  <strong>{i.reason}</strong>
                  <small>
                    {time(i.last_seen)} · {i.mode}
                  </small>
                </td>
                <td>
                  <Pill tone={i.severity === "critical" ? "red" : "amber"}>
                    {i.severity}
                  </Pill>
                </td>
                <td className="mono">{count(i.count)}</td>
                <td>
                  <select
                    aria-label={"State of incident " + i.id}
                    value={i.state}
                    disabled={saving}
                    onChange={async (e) => {
                      setSaving(true);
                      try {
                        await write("incidents/" + i.id, "PATCH", {
                          state: e.target.value,
                        });
                        setMessage("Incident updated.");
                        await refresh();
                      } catch (err) {
                        setMessage((err as Error).message);
                      } finally {
                        setSaving(false);
                      }
                    }}
                  >
                    {["new", "investigating", "resolved", "false_positive"].map(
                      (s) => (
                        <option key={s} value={s}>
                          {human(s)}
                        </option>
                      ),
                    )}
                  </select>
                </td>
                <td>
                  <button
                    className="icon-button"
                    aria-label={"Review event for incident " + i.id}
                    onClick={() => review(i.last_event_id)}
                  >
                    <ArrowUpRight size={18} />
                  </button>
                </td>
              </tr>
            ))}
          </Table>
        )}
        <div className="panel-footer">
          <span className="mono">
            LATEST {data?.incidents.length || 0} INCIDENTS
          </span>
          <button className="text-button" onClick={openAuthorization}>
            <LockKeyhole size={13} />
            Authorize updates <ArrowRight size={13} />
          </button>
        </div>
      </section>
    );
  }
  return (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <aside className="sidebar" inert={auth}>
        <a href="/operations" className="brand" aria-label="AI IDS home">
          <span className="brand-mark">
            <StaticLogo />
            {foreground && (
              <GraphicsBoundary fallback={null}>
                <Suspense fallback={null}>
                  <LiquidLogo animated={motion} />
                </Suspense>
              </GraphicsBoundary>
            )}
          </span>
          <span>
            AI / IDS<small>SECURITY OPERATIONS</small>
          </span>
        </a>
        <div className="sidebar-label mono">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {nav.map((n) => (
            <a
              key={n.key}
              className={view === n.key ? "current" : ""}
              aria-current={view === n.key ? "page" : undefined}
              href={n.href}
            >
              <n.icon size={18} />
              <span>{n.label}</span>
              {view === n.key && <i />}
            </a>
          ))}
        </nav>
        <div className="sidebar-label mono second-label">INTELLIGENCE</div>
        <nav aria-label="Intelligence">
          <a href="/operations#model">
            <Layers size={18} />
            Model & data
            <ArrowUpRight className="nav-arrow" size={13} />
          </a>
          <a href="/operations#review">
            <Fingerprint size={18} />
            Event review
          </a>
        </nav>
        <div className="sidebar-bottom">
          <div className="local-node">
            <span className={"node-light " + (active ? "on" : "")} />
            <div>
              Local sensor<small>{human(health.mode)} environment</small>
            </div>
            <Radio size={18} />
          </div>
          <div className="side-foot mono">
            <span>AI IDS / SOC</span>
            <span>V2.0</span>
          </div>
        </div>
      </aside>
      <div className="workspace" inert={auth}>
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={13} />
            <strong>{title}</strong>
          </div>
          <div className="top-actions">
            <span className="local-only mono">
              <LockKeyhole size={12} /> LOCAL ONLY
            </span>
            <button
              className="icon-button motion-button"
              onClick={() => setMotion((v) => !v)}
              aria-label={
                motion ? "Pause visual motion" : "Enable visual motion"
              }
              aria-pressed={!motion}
            >
              {motion ? <Pause size={15} /> : <Play size={15} />}
            </button>
            <button
              className="operator"
              aria-label="Analyst authorization"
              onClick={openAuthorization}
            >
              LO
            </button>
          </div>
        </header>
        <main id="main">
          <div className="page-heading">
            <div>
              <span className="eyebrow">
                {view === "operations"
                  ? "YOUR NETWORK, IN FOCUS"
                  : "OBSERVE / " + view.toUpperCase()}
              </span>
              <h1>
                {title}
                <span className="heading-dot">.</span>
              </h1>
            </div>
            <div className="refresh-area">
              <span className="mono">
                {errors.length
                  ? "CONNECTION ISSUE"
                  : updated
                    ? "SYNCED " +
                      updated.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })
                    : "CONNECTING…"}
              </span>
              <button
                className="refresh-button"
                disabled={busy}
                onClick={refresh}
              >
                <RefreshCw size={14} className={busy ? "spin" : ""} />
                <span>Refresh</span>
              </button>
            </div>
          </div>
          {errors.length > 0 && (
            <div className="notice error" role="alert">
              Some data could not refresh. Previous values may be out of date.
              <details>
                <summary>Connection details</summary>
                {errors.map((e) => (
                  <p key={e}>{e}</p>
                ))}
              </details>
            </div>
          )}
          {message && (
            <div className="notice" role="status">
              {message}
              <button
                aria-label="Dismiss message"
                onClick={() => setMessage("")}
              >
                <X size={16} />
              </button>
            </div>
          )}
          {view === "operations" ? (
            <>
              <div
                className="tabs"
                role="navigation"
                aria-label="Operations sections"
              >
                {[
                  ["overview", "Overview"],
                  ["model", "Model & data"],
                  ["review", "Event review"],
                ].map(([id, label]) => (
                  <a
                    href={"#" + id}
                    key={id}
                    className={tab === id ? "selected" : ""}
                    aria-current={tab === id ? "location" : undefined}
                  >
                    {label}
                  </a>
                ))}
                <span className="mono">
                  {health.model_shadow
                    ? "MODEL IN SHADOW"
                    : health.ml_mode
                      ? human(health.ml_mode).toUpperCase()
                      : "AWAITING STATUS"}
                  <i />
                </span>
              </div>
              {tab === "overview" && (
                <>
                  <section className="hero">
                    <div className="hero-copy">
                      <div className="hero-kicker mono">
                        <span
                          className={active ? "node-light on" : "node-light"}
                        />{" "}
                        {active
                          ? "CAPTURE IS LIVE"
                          : data
                            ? "CAPTURE / " +
                              human(network.capture).toUpperCase()
                            : "CONNECTING TO SENSOR"}
                      </div>
                      <h2 aria-label="See beyond the surface.">
                        <HoverText text="See beyond" />
                        <br />
                        <span className="muted-heading">
                          <HoverText text="the surface." />
                        </span>
                      </h2>
                      <p>
                        A clearer view of your network.
                        <br />
                        Observe the signals. Investigate the evidence.
                      </p>
                      <Magnet className="primary-button" href="#queue">
                        Explore incidents <ArrowUpRight size={17} />
                      </Magnet>
                      <div className="hero-caption mono">
                        <span>01 — OBSERVE</span>
                        <span className="caption-line" />{" "}
                        <span>02 — UNDERSTAND</span>
                      </div>
                    </div>
                    <Sensor animated={motion && foreground} />
                  </section>
                  <div className="metrics">
                    <Metric
                      icon={<ArrowDownLeft size={17} />}
                      label="Packets observed"
                      value={count(network.packet_count)}
                      sub="Current capture session"
                    />
                    <Metric
                      icon={<Activity size={17} />}
                      label="Flow windows"
                      value={count(network.flows_received)}
                      sub={`${count(network.active_flows)} active connections`}
                    />
                    <Metric
                      icon={<Shield size={17} />}
                      label="Open incidents"
                      value={count(open)}
                      sub="Awaiting an analyst decision"
                      accent={!!open}
                    />
                    <Metric
                      icon={<Database size={17} />}
                      label="Dropped events"
                      value={
                        network.queue_drops == null
                          ? "—"
                          : count(
                              network.queue_drops +
                                (network.capacity_drops || 0),
                            )
                      }
                      sub={`${count(network.queue_depth)} events in queue`}
                      accent={!!(network.queue_drops || network.capacity_drops)}
                    />
                  </div>
                  <div className="overview-grid">
                    <div id="queue">{incidents()}</div>
                    <section className="panel collector-panel">
                      <div className="panel-heading">
                        <div>
                          <span className="eyebrow">SENSOR HEALTH</span>
                          <h2>Collection status</h2>
                        </div>
                        <Radio size={18} />
                      </div>
                      <Status
                        label="Network capture"
                        value={human(network.capture)}
                        good={active}
                      />
                      <Status
                        label="Endpoint collector"
                        value={
                          network.endpoint === "limited_wmi"
                            ? "Limited · WMI"
                            : human(network.endpoint)
                        }
                        good={network.endpoint === "running"}
                      />
                      <Status
                        label="Traffic model"
                        value={
                          health.model_shadow
                            ? "Shadow mode"
                            : health.model_ready
                              ? "Active"
                              : "Not loaded"
                        }
                        good={!!health.model_ready}
                      />
                      <Status
                        label="Event storage"
                        value={human(health.database)}
                        good={health.database === "ready"}
                      />
                      <div className="collector-note">
                        <CircleHelp size={16} />
                        <p>
                          {health.model_shadow
                            ? "The model records predictions for review. Rules raise incidents."
                            : "Collector state reflects this local session."}
                        </p>
                      </div>
                      {(network.endpoint_error ||
                        network.capture_error ||
                        health.model_error) && (
                        <details className="collector-details">
                          <summary>Collection limitations</summary>
                          <p>
                            {[
                              network.endpoint_error,
                              network.capture_error,
                              health.model_error,
                            ]
                              .filter(Boolean)
                              .join(" · ")}
                          </p>
                        </details>
                      )}
                      <div className="panel-footer mono">
                        {count(network.processing_errors)} PROCESSING ERRORS
                      </div>
                    </section>
                  </div>
                </>
              )}
              {tab === "model" && <ModelView data={data} />}
              {tab === "review" && (
                <>
                  <section className="panel review-panel" ref={reviewRef}>
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">HUMAN IN THE LOOP</span>
                        <h2>Review an event</h2>
                      </div>
                      <Fingerprint size={24} />
                    </div>
                    <p>
                      Record a conclusion with supporting evidence. Reviewed
                      labels are stored separately from model predictions.
                    </p>
                    <form
                      onSubmit={async (e) => {
                        e.preventDefault();
                        setSaving(true);
                        try {
                          await write("labels", "POST", {
                            event_id: eventId,
                            label: Number(outcome),
                            note,
                          });
                          setMessage(
                            "Reviewed label saved separately from the prediction.",
                          );
                          setNote("");
                        } catch (err) {
                          setMessage((err as Error).message);
                        } finally {
                          setSaving(false);
                        }
                      }}
                    >
                      <label>
                        Event ID
                        <input
                          value={eventId}
                          onChange={(e) => setEventId(e.target.value)}
                          required
                          maxLength={200}
                          placeholder="Select an incident or paste an event ID"
                        />
                      </label>
                      <div className="form-columns">
                        <label>
                          Reviewed outcome
                          <select
                            value={outcome}
                            onChange={(e) => setOutcome(e.target.value)}
                          >
                            <option value="0">Benign</option>
                            <option value="1">Malicious</option>
                          </select>
                        </label>
                        <label>
                          Analyst name
                          <input
                            value={analyst}
                            onChange={(e) => setAnalyst(e.target.value)}
                            required
                            maxLength={100}
                          />
                        </label>
                      </div>
                      <label>
                        Evidence and review note
                        <textarea
                          required
                          maxLength={4000}
                          rows={5}
                          value={note}
                          onChange={(e) => setNote(e.target.value)}
                          placeholder="What did you observe? Include evidence for your conclusion."
                        />
                      </label>
                      <div className="form-footer">
                        <button className="primary-button" disabled={saving}>
                          {saving ? "Saving…" : "Save reviewed label"}
                          <ArrowRight size={16} />
                        </button>
                        <button
                          type="button"
                          className="text-button"
                          onClick={openAuthorization}
                        >
                          <LockKeyhole size={14} />
                          {token ? "Token entered" : "Authorize changes"}
                        </button>
                      </div>
                    </form>
                  </section>
                  {incidents()}
                </>
              )}
            </>
          ) : (
            <section className="panel records-panel">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">LOCAL TELEMETRY</span>
                  <h2>
                    {view === "traffic"
                      ? "Captured connections"
                      : view === "commands"
                        ? "Command observations"
                        : "Collector log"}
                  </h2>
                </div>
                <Pill>{health.mode || "Connecting"}</Pill>
              </div>
              <p className="panel-intro">
                {view === "traffic"
                  ? "Most recent flow windows. Shadow predictions are evidence for review, not active alerts."
                  : view === "commands"
                    ? "Observed process commands, evaluated by detection rules. Collection may miss short-lived processes."
                    : "Recent collector messages and operational events."}
              </p>
              <div className="record-tools">
                <label className="search">
                  <Search size={16} />
                  <input
                    aria-label="Search observations"
                    placeholder="Search observations…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </label>
                <select
                  aria-label="Filter observations"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                >
                  <option value="all">All observations</option>
                  <option value="flagged">
                    {view === "logs" ? "Warnings & errors" : "Flagged only"}
                  </option>
                </select>
                <span className="mono">LATEST 100</span>
              </div>
              <Records
                data={data}
                view={view}
                search={search}
                filter={filter}
              />
            </section>
          )}
          <footer className="footer">
            <span>
              <span className="footer-symbol">✳</span> Intelligence with
              evidence.
            </span>
            <span className="mono">LOCAL-FIRST / AI IDS SOC</span>
          </footer>
        </main>
      </div>
      {auth && (
        <div
          className="modal-backdrop"
          onClick={(e) => {
            if (e.target === e.currentTarget) setAuth(false);
          }}
        >
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="authTitle"
            onKeyDown={(e) => {
              if (e.key === "Escape") setAuth(false);
              if (e.key === "Tab") {
                const controls = Array.from(
                  e.currentTarget.querySelectorAll<HTMLElement>("button,input"),
                );
                const first = controls[0],
                  last = controls.at(-1);
                if (e.shiftKey && document.activeElement === first) {
                  e.preventDefault();
                  last?.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                  e.preventDefault();
                  first?.focus();
                }
              }
            }}
          >
            <button
              className="modal-close icon-button"
              aria-label="Close authorization"
              onClick={() => setAuth(false)}
            >
              <X size={20} />
            </button>
            <LockKeyhole size={28} className="lime" />
            <span className="eyebrow">ANALYST ACCESS</span>
            <h2 id="authTitle">Authorize changes</h2>
            <p>
              Use the local API token from <code>data/local-token.txt</code>.
              The token stays in this page’s memory and is cleared when you
              leave.
            </p>
            <label>
              Local API token
              <input
                autoFocus
                type="password"
                autoComplete="off"
                value={token}
                onChange={(e) => setToken(e.target.value)}
              />
            </label>
            <label>
              Analyst name
              <input
                value={analyst}
                maxLength={100}
                onChange={(e) => setAnalyst(e.target.value)}
              />
            </label>
            <button className="primary-button" onClick={() => setAuth(false)}>
              Continue
              <ArrowRight size={16} />
            </button>
            <small>Changes are authorized by the server when you save.</small>
          </div>
        </div>
      )}
    </>
  );
}
function Metric({
  icon,
  label,
  value,
  sub,
  accent = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub: string;
  accent?: boolean;
}) {
  return (
    <article className="metric">
      <div>
        <span>{label}</span>
        {icon}
      </div>
      <strong className={accent ? "amber-text" : ""}>{value}</strong>
      <small>{sub}</small>
    </article>
  );
}
function Status({
  label,
  value,
  good,
}: {
  label: string;
  value: string;
  good: boolean;
}) {
  return (
    <div className="status-row">
      <span>{label}</span>
      <span>
        <i className={good ? "good" : ""} />
        {value}
      </span>
    </div>
  );
}
function Families({ report }: { report: Row }) {
  return (
    <details className="report-details">
      <summary>
        Attack-family results & limitations <ChevronRight size={14} />
      </summary>
      <Table
        heads={[
          "Attack family",
          "Test windows",
          "Flagged",
          "Recall / flag rate",
        ]}
      >
        {Object.entries(report.test?.families || {}).map(([family, val]) => {
          const v = val as Row;
          return (
            <tr key={family}>
              <td>{family.replaceAll("\u0096", "–")}</td>
              <td className="mono">{count(v.samples)}</td>
              <td className="mono">{count(v.flagged)}</td>
              <td className="mono">{percent(v.flag_rate)}</td>
            </tr>
          );
        })}
      </Table>
      {(report.limitations || []).map((l: string) => (
        <p key={l}>{l}</p>
      ))}
    </details>
  );
}
function ModelView({ data }: { data: Snapshot | null }) {
  const r = data?.model.report;
  return (
    <>
      <section className="panel model-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">TRAFFIC INTELLIGENCE</span>
            <h2>Canonical traffic model</h2>
          </div>
          <Pill tone="amber">{data?.model.status || "Loading"}</Pill>
        </div>
        <p>
          Grouped session and feature holdout within CICIDS2017. Captures are
          shared across partitions. Independent live accuracy has not been
          measured.
        </p>
        {r ? (
          <>
            <div className="model-metrics">
              <Metric
                icon={<Check size={16} />}
                label="Precision"
                value={percent(r.test.precision)}
                sub="Of flagged test windows"
              />
              <Metric
                icon={<Eye size={16} />}
                label="Attack recall"
                value={percent(r.test.recall)}
                sub="Of labeled attack windows"
              />
              <Metric
                icon={<Activity size={16} />}
                label="False-positive rate"
                value={percent(r.test.fpr, 4)}
                sub="Of benign test windows"
              />
              <Metric
                icon={<Database size={16} />}
                label="Held-out windows"
                value={count(r.test.samples)}
                sub="CICIDS2017 test partition"
              />
            </div>
            <Families report={r} />
          </>
        ) : (
          <Empty>
            {data
              ? "No completed compatible model report."
              : "Loading model report…"}
          </Empty>
        )}
      </section>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">RESEARCH / DATASET-SPECIFIC</span>
            <h2>Offline evaluations</h2>
          </div>
          <Layers size={20} />
        </div>
        <p className="panel-intro">
          CSV benchmarks use dataset-specific features. These results do not
          measure live detection performance.
        </p>
        {data?.benchmarks.length ? (
          data.benchmarks.map((b, i) => (
            <article className="benchmark" key={i}>
              <h3>
                {b.dataset} — {b.model_type}
              </h3>
              <p>{b.split_policy}</p>
              <Table
                heads={[
                  "Held-out rows",
                  "Precision",
                  "Attack recall",
                  "False-positive rate",
                  "Threshold",
                ]}
              >
                <tr>
                  <td>{count(b.test.samples)}</td>
                  <td>{percent(b.test.precision)}</td>
                  <td>{percent(b.test.recall)}</td>
                  <td>{percent(b.test.fpr, 4)}</td>
                  <td>{b.threshold?.toFixed(4)}</td>
                </tr>
              </Table>
              <Families report={b} />
            </article>
          ))
        ) : (
          <Empty>No completed CSV benchmark reports available.</Empty>
        )}
      </section>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">TRAINING INPUTS</span>
            <h2>Dataset preparation</h2>
          </div>
          <Pill>{human(data?.progress.pipeline?.stage)}</Pill>
        </div>
        {data?.progress.pipeline?.error && (
          <p className="amber-text">{data.progress.pipeline.error}</p>
        )}
        {data?.progress.pipeline?.days?.length > 0 && (
          <Table
            heads={[
              "Capture",
              "Windows checked",
              "Labels matched",
              "Training rows",
            ]}
          >
            {data?.progress.pipeline.days.map((d: Row) => (
              <tr key={d.day}>
                <td>{d.day}</td>
                <td>{count(d.counts.windows)}</td>
                <td>{count(d.counts.matched)}</td>
                <td>{count(d.counts.written)}</td>
              </tr>
            ))}
          </Table>
        )}
        <Table heads={["Source file", "State", "Downloaded / total"]}>
          {(data?.progress.downloads || []).map((d: Row) => (
            <tr key={d.path}>
              <td className="file-path">{d.path}</td>
              <td>
                <Pill>{human(d.state)}</Pill>
              </td>
              <td className="mono">
                {(d.bytes / 1073741824).toFixed(2)} /{" "}
                {(d.size / 1073741824).toFixed(2)} GiB
              </td>
            </tr>
          ))}
        </Table>
      </section>
    </>
  );
}
function Records({
  data,
  view,
  search,
  filter,
}: {
  data: Snapshot | null;
  view: string;
  search: string;
  filter: string;
}) {
  const rows =
    (view === "traffic"
      ? data?.flows
      : view === "commands"
        ? data?.commands
        : data?.logs) || [];
  const filtered = rows.filter(
    (r) =>
      (!search ||
        JSON.stringify(r).toLowerCase().includes(search.toLowerCase())) &&
      (filter === "all" ||
        (view === "logs"
          ? ["warning", "error", "critical"].includes(r.level?.toLowerCase())
          : r.is_anomaly)),
  );
  if (!data) return <Empty>Loading observations…</Empty>;
  if (!filtered.length)
    return (
      <Empty>
        {rows.length
          ? "No observations match your filters."
          : "No observations recorded yet."}
      </Empty>
    );
  return view === "traffic" ? (
    <Table
      heads={[
        "Observed",
        "Source → destination",
        "Protocol",
        "Packets",
        "Detection",
        "Review",
      ]}
    >
      {filtered.map((r) => (
        <tr key={r.event_id}>
          <td className="mono">{time(r.timestamp)}</td>
          <td className="mono connection">
            {r.src_ip}:{r.src_port}
            <span>
              <ArrowRight size={12} />
              {r.dst_ip}:{r.dst_port}
            </span>
          </td>
          <td className="mono">
            {({ 6: "TCP", 17: "UDP", 1: "ICMP" } as Row)[r.proto] || r.proto}
          </td>
          <td className="mono">
            {count((r.src2dst_pkts || 0) + (r.dst2src_pkts || 0))}
          </td>
          <td>
            <Pill tone={r.is_anomaly ? "amber" : ""}>
              {r.is_anomaly
                ? "Rule / alert"
                : r.prediction_status === "shadow"
                  ? "Shadow / no rule"
                  : "No rule triggered"}
            </Pill>
            <small>
              {r.model_results?.random_forest
                ? `Model score ${percent(r.model_results.random_forest.score)}`
                : ""}
            </small>
          </td>
          <td>
            <a
              className="icon-button"
              href={"/operations#review"}
              onClick={() =>
                sessionStorage.setItem("ids-review-event", r.event_id)
              }
              aria-label={"Review " + r.event_id}
            >
              <ArrowUpRight size={17} />
            </a>
          </td>
        </tr>
      ))}
    </Table>
  ) : view === "commands" ? (
    <Table
      heads={["Observed", "Command / evidence", "Severity", "Mode", "Review"]}
    >
      {filtered.map((r) => (
        <tr key={r.event_id}>
          <td className="mono">{time(r.timestamp)}</td>
          <td className="command-evidence">
            <code>{r.command}</code>
            <small>{r.reason}</small>
          </td>
          <td>
            <Pill tone={r.is_anomaly ? "amber" : ""}>{r.severity}</Pill>
          </td>
          <td className="mono">{r.mode}</td>
          <td>
            <a
              className="icon-button"
              href="/operations#review"
              onClick={() =>
                sessionStorage.setItem("ids-review-event", r.event_id)
              }
              aria-label={"Review " + r.event_id}
            >
              <ArrowUpRight size={17} />
            </a>
          </td>
        </tr>
      ))}
    </Table>
  ) : (
    <Table heads={["Observed", "Level", "Component", "Message"]}>
      {filtered.map((r) => (
        <tr key={r.id}>
          <td className="mono">{time(r.timestamp)}</td>
          <td>
            <Pill
              tone={
                ["warning", "error", "critical"].includes(
                  r.level?.toLowerCase(),
                )
                  ? "amber"
                  : ""
              }
            >
              {r.level}
            </Pill>
          </td>
          <td className="mono">{r.component}</td>
          <td className="log-message">{r.message}</td>
        </tr>
      ))}
    </Table>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
