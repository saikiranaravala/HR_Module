import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { PERSONAS, type Persona } from "./data";
import { useStore } from "./store";

/* ---------- Route registry (drives nav, crumbs, palette) ---------- */
export interface RouteDef { path: string; label: string; ico: string; group: string; personas: Persona[] }
export const ROUTES: RouteDef[] = [
  { path: "/", label: "Home", ico: "⌂", group: "Workspaces", personas: ["employee", "manager", "hr"] },
  { path: "/approvals", label: "Approvals", ico: "✓", group: "Workspaces", personas: ["manager", "hr"] },
  { path: "/team", label: "My Team", ico: "👥", group: "Workspaces", personas: ["manager"] },

  { path: "/pay", label: "Payslips", ico: "💵", group: "Self Service", personas: ["employee", "manager", "hr"] },
  { path: "/time", label: "Time & Absence", ico: "🕒", group: "Self Service", personas: ["employee", "manager", "hr"] },
  { path: "/benefits", label: "Benefits", ico: "🛡", group: "Self Service", personas: ["employee", "manager", "hr"] },
  { path: "/profile", label: "Personal Details", ico: "🪪", group: "Self Service", personas: ["employee", "manager", "hr"] },
  { path: "/directory", label: "Directory", ico: "🔍", group: "Self Service", personas: ["employee", "manager", "hr"] },
  { path: "/performance", label: "Performance", ico: "🎯", group: "Self Service", personas: ["employee", "manager", "hr"] },
  { path: "/learning", label: "Learning", ico: "🎓", group: "Self Service", personas: ["employee", "manager", "hr"] },
  { path: "/help", label: "Help Center", ico: "💬", group: "Self Service", personas: ["employee", "manager", "hr"] },

  { path: "/comp-cycle", label: "Comp Cycle", ico: "📈", group: "Manager", personas: ["manager", "hr"] },
  { path: "/recruiting", label: "Recruiting", ico: "🧲", group: "Manager", personas: ["manager", "hr"] },

  { path: "/payroll-hub", label: "Payroll Hub", ico: "🏛", group: "Administration", personas: ["hr"] },
  { path: "/succession", label: "Succession", ico: "♟", group: "Administration", personas: ["hr"] },
  { path: "/analytics", label: "Workforce Analytics", ico: "📊", group: "Administration", personas: ["hr", "manager"] },
];

export function routeFor(path: string) {
  return ROUTES.find((r) => r.path === path);
}

/* ---------- Global header ---------- */
export function GlobalHeader({ onToggleNav, onOpenPalette }: { onToggleNav: () => void; onOpenPalette: () => void }) {
  const { state, dispatch } = useStore();
  const navigate = useNavigate();
  const persona = PERSONAS[state.persona];
  const pending = state.approvals.filter((a) => a.status === "pending").length;
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="gh">
      <button className="gh-icon" aria-label="Toggle navigation" onClick={onToggleNav}>☰</button>
      <Link to="/" className="gh-brand" style={{ color: "inherit" }}>
        <img src="/meridian.svg" alt="" /> Meridian
      </Link>
      <select
        className="gh-home-sel" aria-label="Homepage"
        value={state.persona}
        onChange={(e) => { dispatch({ type: "persona", persona: e.target.value as Persona }); navigate("/"); }}
      >
        {(Object.keys(PERSONAS) as Persona[]).map((p) => (
          <option key={p} value={p}>{PERSONAS[p].homepage} ▾</option>
        ))}
      </select>
      <div className="gh-spacer" />
      <button className="gh-search" onClick={onOpenPalette} aria-label="Search (Ctrl+K)">
        🔎 Search people, pages, actions… <kbd>Ctrl K</kbd>
      </button>
      <Link to={state.persona === "employee" ? "/help" : "/approvals"} className="gh-icon" aria-label="Notifications" style={{ color: "inherit", textDecoration: "none" }}>
        🔔{pending > 0 && state.persona !== "employee" && <span className="gh-badge">{pending}</span>}
      </Link>
      <div style={{ position: "relative" }}>
        <button className="gh-avatar" onClick={() => setMenuOpen((v) => !v)} aria-label="Account">
          {persona.initials}
        </button>
        {menuOpen && (
          <div style={{
            position: "absolute", right: 0, top: 38, background: "var(--surface)", color: "var(--ink)",
            borderRadius: 8, boxShadow: "var(--shadow-lift)", padding: 12, width: 230, zIndex: 70,
          }}>
            <div style={{ fontWeight: 650 }}>{persona.name}</div>
            <div className="muted small">{persona.title}</div>
            <hr style={{ border: "none", borderTop: "1px solid var(--line)", margin: "10px 0" }} />
            <div className="small muted">Demo personas</div>
            {(Object.keys(PERSONAS) as Persona[]).map((p) => (
              <button key={p} className="btn sm" style={{ margin: "4px 4px 0 0" }}
                onClick={() => { dispatch({ type: "persona", persona: p }); setMenuOpen(false); navigate("/"); }}>
                {PERSONAS[p].name.split(" ")[0]} · {PERSONAS[p].homepage}
              </button>
            ))}
          </div>
        )}
      </div>
    </header>
  );
}

/* ---------- NavBar ---------- */
export function NavBar({ open }: { open: boolean }) {
  const { state } = useStore();
  const visible = ROUTES.filter((r) => r.personas.includes(state.persona));
  const groups = [...new Set(visible.map((r) => r.group))];
  return (
    <nav className={`nav ${open ? "" : "closed"}`} aria-label="Work centers">
      {groups.map((g) => (
        <div key={g}>
          <div className="nav-group">{g}</div>
          {visible.filter((r) => r.group === g).map((r) => (
            <NavLink key={r.path} to={r.path} end={r.path === "/"}
              className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
              <span className="nav-ico" aria-hidden>{r.ico}</span>{r.label}
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  );
}

/* ---------- Breadcrumbs ---------- */
export function Crumbs({ trail }: { trail?: string[] }) {
  const { state } = useStore();
  const loc = useLocation();
  const route = routeFor(loc.pathname);
  const parts = trail ?? (route && route.path !== "/" ? [PERSONAS[state.persona].homepage, route.group, route.label] : [PERSONAS[state.persona].homepage]);
  return (
    <div className="crumbs" aria-label="Breadcrumb">
      {parts.map((p, i) => (
        <span key={i} style={{ display: "flex", gap: 6, alignItems: "center" }}>
          {i > 0 && <span className="sep">›</span>}
          {i === parts.length - 1 ? <b>{p}</b> : i === 0 ? <Link to="/">{p}</Link> : <span>{p}</span>}
        </span>
      ))}
    </div>
  );
}

/* ---------- Command palette (Ctrl+K) ---------- */
interface PaletteAction { label: string; hint: string; run: () => void }
export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { state, dispatch } = useStore();
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const actions: PaletteAction[] = useMemo(() => {
    const nav = ROUTES.filter((r) => r.personas.includes(state.persona)).map((r) => ({
      label: `${r.ico}  ${r.label}`, hint: "Go to", run: () => navigate(r.path),
    }));
    const quick: PaletteAction[] = [
      { label: "🏖  Request time off", hint: "Action", run: () => navigate("/time?request=1") },
      { label: "💵  View latest payslip", hint: "Action", run: () => navigate("/pay") },
      { label: "✓  Approve all routine items", hint: "Action", run: () => dispatch({ type: "bulk-approve", ids: state.approvals.filter((a) => a.status === "pending" && !a.bulkBarred).map((a) => a.id) }) },
      { label: "🧑  Find Jordan Patel", hint: "People", run: () => navigate("/directory?q=Jordan") },
    ];
    return [...quick, ...nav];
  }, [state.persona, state.approvals, navigate, dispatch]);

  const hits = actions.filter((a) => a.label.toLowerCase().includes(q.toLowerCase()));

  useEffect(() => { if (open) { setQ(""); setSel(0); setTimeout(() => inputRef.current?.focus(), 10); } }, [open]);
  if (!open) return null;

  const fire = (a: PaletteAction) => { a.run(); onClose(); };
  return (
    <div className="palette" onClick={onClose}>
      <div className="palette-box" role="dialog" aria-label="Command palette" onClick={(e) => e.stopPropagation()}>
        <input ref={inputRef} value={q} placeholder="Search pages, people, actions…"
          onChange={(e) => { setQ(e.target.value); setSel(0); }}
          onKeyDown={(e) => {
            if (e.key === "Escape") onClose();
            if (e.key === "ArrowDown") setSel((s) => Math.min(s + 1, hits.length - 1));
            if (e.key === "ArrowUp") setSel((s) => Math.max(s - 1, 0));
            if (e.key === "Enter" && hits[sel]) fire(hits[sel]);
          }} />
        <div className="palette-list">
          {hits.map((a, i) => (
            <div key={a.label} className={`palette-item ${i === sel ? "sel" : ""}`}
              onMouseEnter={() => setSel(i)} onClick={() => fire(a)}>
              {a.label}<span className="k">{a.hint}</span>
            </div>
          ))}
          {hits.length === 0 && <div className="palette-item muted">No matches</div>}
        </div>
      </div>
    </div>
  );
}

/* ---------- Toasts ---------- */
export function Toasts() {
  const { state, dispatch } = useStore();
  useEffect(() => {
    if (!state.toasts.length) return;
    const t = setTimeout(() => dispatch({ type: "dismiss-toast", id: state.toasts[0].id }), 4200);
    return () => clearTimeout(t);
  }, [state.toasts, dispatch]);
  return (
    <div className="toasts" aria-live="polite">
      {state.toasts.map((t) => (
        <div key={t.id} className={`toast ${t.warn ? "warn" : ""}`} onClick={() => dispatch({ type: "dismiss-toast", id: t.id })}>
          {t.text}
        </div>
      ))}
    </div>
  );
}

/* ---------- Shared furniture ---------- */
export function PageTitle({ title, sub, right }: { title: string; sub?: string; right?: ReactNode }) {
  return (
    <div className="page-title">
      <h1>{title}</h1>
      {sub && <span className="sub">{sub}</span>}
      {right && <span className="right">{right}</span>}
    </div>
  );
}

export function GridBar({ label, count }: { label: string; count?: number }) {
  return (
    <div className="gridbar">
      <span>{label}{count !== undefined ? ` · ${count}` : ""}</span>
      <span className="right">
        <a href="#" onClick={(e) => e.preventDefault()}>Personalize</a>
        <a href="#" onClick={(e) => e.preventDefault()}>Find</a>
        <a href="#" onClick={(e) => e.preventDefault()}>⏷ View All</a>
      </span>
    </div>
  );
}

export function Tile({ to, ico, kpi, kpiSuffix, label, flag }: {
  to: string; ico: string; kpi: string | number; kpiSuffix?: string; label: string; flag?: ReactNode;
}) {
  return (
    <Link to={to} className="tile">
      <span className="tile-ico" aria-hidden>{ico}</span>
      {flag && <span className="tile-flag">{flag}</span>}
      <span className="tile-kpi">{kpi}{kpiSuffix && <small> {kpiSuffix}</small>}</span>
      <span className="tile-label">{label}</span>
    </Link>
  );
}

export function Modal({ title, onClose, children, foot }: {
  title: string; onClose: () => void; children: ReactNode; foot?: ReactNode;
}) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);
  return (
    <div className="scrim" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <h2>{title}</h2>
        {children}
        {foot && <div className="foot">{foot}</div>}
      </div>
    </div>
  );
}

export function Pill({ kind, children }: { kind: "ok" | "warn" | "err" | "info" | "muted"; children: ReactNode }) {
  return <span className={`pill ${kind}`}>{children}</span>;
}
