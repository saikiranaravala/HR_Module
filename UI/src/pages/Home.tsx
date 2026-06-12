import { Link } from "react-router-dom";
import { ACCRUALS, CASES, KEY_POSITIONS, PAYSLIPS, PAY_CYCLES, PERSONAS, REQS, REQUIREMENTS, money } from "../data";
import { Pill, Tile } from "../components";
import { useStore } from "../store";

export default function Home() {
  const { state } = useStore();
  const persona = PERSONAS[state.persona];
  const pending = state.approvals.filter((a) => a.status === "pending");
  const pto = ACCRUALS.reduce((s, a) => s + (a.plan.startsWith("PTO") ? a.balance : 0), 0);
  const latest = PAYSLIPS[0];
  const overdue = REQUIREMENTS.filter((r) => r.status === "overdue").length;

  return (
    <>
      <div className="page-title">
        <h1>{persona.homepage}</h1>
        <span className="sub">Good morning, {persona.name.split(" ")[0]} — {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}</span>
      </div>

      {/* Attention strip: the minimum-clicks front door */}
      <div className="card" style={{ borderLeft: "4px solid var(--brand-amber)" }}>
        <h2>Needs your attention</h2>
        <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.9 }}>
          {state.persona !== "employee" && pending.length > 0 && (
            <li><Link to="/approvals"><b>{pending.length} approvals waiting</b></Link> — oldest from {pending[0].submitted} <Pill kind="warn">SLA</Pill></li>
          )}
          {state.persona === "employee" && (
            <li>Harassment-prevention training due <b>Jun 30</b> — <Link to="/learning">resume (60% done)</Link></li>
          )}
          {state.persona === "employee" && ACCRUALS.some((a) => a.expires) && (
            <li><b>3.0 PTO carryover days expire Jun 30</b> — <Link to="/time?request=1">request time off</Link></li>
          )}
          {state.persona === "hr" && (
            <li><Link to="/payroll-hub"><b>US 2026-06B: 14 anomalies</b></Link> need disposition before approval <Pill kind="err">payroll gate</Pill></li>
          )}
          {state.persona === "hr" && (
            <li><Link to="/succession"><b>Slate gap:</b> Director, Payroll Ops has no ready-now successor</Link></li>
          )}
          {state.persona === "manager" && (
            <li>Jordan Patel's timesheet is missing for last week — <Link to="/team">one-tap nudge</Link></li>
          )}
        </ul>
      </div>

      <div className="tilegrid">
        {/* shared ESS tiles */}
        <Tile to="/pay" ico="💵" kpi={money(latest.net)} label={`Payday Jun 20 — net last cycle`} />
        <Tile to="/time" ico="🕒" kpi={pto.toFixed(1)} kpiSuffix="days" label="PTO balance · request in 2 clicks"
          flag={ACCRUALS.some((a) => a.expires) ? <Pill kind="warn">expiring</Pill> : undefined} />
        <Tile to="/benefits" ico="🛡" kpi="4" kpiSuffix="plans" label="Benefits elections" />
        <Tile to="/performance" ico="🎯" kpi="65%" label="Goal progress · FY26 review open" />
        <Tile to="/learning" ico="🎓" kpi={REQUIREMENTS.length} kpiSuffix="due" label="Learning & compliance"
          flag={overdue ? <Pill kind="err">{overdue} overdue</Pill> : undefined} />
        <Tile to="/help" ico="💬" kpi={CASES.length} kpiSuffix="open" label="Help Center · ask the copilot" />
        <Tile to="/directory" ico="🔍" kpi="12.8k" label="Company directory & org chart" />

        {state.persona !== "employee" && (
          <>
            <Tile to="/approvals" ico="✓" kpi={pending.length} kpiSuffix="pending" label="Unified approvals inbox"
              flag={<Pill kind="warn">act</Pill>} />
            <Tile to="/team" ico="👥" kpi="3" kpiSuffix="reports" label="Team hub · time compliance" />
            <Tile to="/comp-cycle" ico="📈" kpi="FY26" label="Merit cycle · budget live" />
            <Tile to="/recruiting" ico="🧲" kpi={REQS.length} kpiSuffix="open reqs" label="Recruiting pipeline" />
          </>
        )}
        {state.persona === "hr" && (
          <>
            <Tile to="/payroll-hub" ico="🏛" kpi={PAY_CYCLES.length} kpiSuffix="cycles" label="Payroll Integration Hub"
              flag={<Pill kind="err">14 anomalies</Pill>} />
            <Tile to="/succession" ico="♟" kpi={KEY_POSITIONS.length} kpiSuffix="key roles" label="Succession slates (T3)"
              flag={<span className="tier t3">T3</span>} />
            <Tile to="/analytics" ico="📊" kpi="12,847" label="Workforce analytics · certified metrics" />
          </>
        )}
      </div>
    </>
  );
}
