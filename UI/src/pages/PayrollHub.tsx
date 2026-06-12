import { GridBar, PageTitle, Pill } from "../components";
import { PAY_CYCLES, VARIANCES, money } from "../data";
import { useStore } from "../store";

const STATES = ["inputs-compiled", "transmitted", "results-received", "results-reconciled", "approved", "released"];

export default function PayrollHub() {
  const { dispatch } = useStore();
  return (
    <>
      <PageTitle title="Payroll Integration Hub" sub="Meridian orchestrates; certified providers calculate. The pipeline halts loudly or proceeds provably." />
      <div className="card">
        <GridBar label="Active cycles" count={PAY_CYCLES.length} />
        <table className="psgrid">
          <thead><tr><th>Country</th><th>Pay group</th><th>Period</th><th>Stage</th><th className="num">Workers</th><th className="num">Anomalies</th><th /></tr></thead>
          <tbody>
            {PAY_CYCLES.map((c) => (
              <tr key={c.group + c.period}>
                <td><b>{c.country}</b></td><td>{c.group}</td><td>{c.period}</td>
                <td>
                  <div className="small">{STATES.map((s) => (
                    <span key={s} style={{ opacity: STATES.indexOf(s) <= STATES.indexOf(c.state) ? 1 : 0.3 }}>
                      {STATES.indexOf(s) > 0 && " → "}{s === c.state ? <b>{s}</b> : s}
                    </span>
                  ))}</div>
                </td>
                <td className="num">{c.workers.toLocaleString()}</td>
                <td className="num">{c.anomalies > 0 ? <Pill kind="err">{c.anomalies}</Pill> : <Pill kind="ok">0</Pill>}</td>
                <td>
                  <button className="btn sm primary" disabled={c.anomalies > 0}
                    title={c.anomalies > 0 ? "Anomalies must be dispositioned before approval" : ""}
                    onClick={() => dispatch({ type: "toast", text: `${c.country} ${c.period}: approved — snapshot hash sealed, release scheduled.` })}>
                    Approve
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="small muted" style={{ marginBottom: 0 }}>Input snapshots are immutable and hashed; retro deltas reconcile to the identity original + delta = recalculated.</p>
      </div>
      <div className="card">
        <h2>Reconciliation — US 2026-06B (element-level, three-way)</h2>
        <table className="psgrid">
          <thead><tr><th>Worker</th><th>Element</th><th className="num">Meridian</th><th className="num">Provider</th><th>Variance class</th><th /></tr></thead>
          <tbody>
            {VARIANCES.map((v) => (
              <tr key={v.worker + v.element}>
                <td>{v.worker}</td><td>{v.element}</td>
                <td className="num">{money(v.ps)}</td><td className="num">{money(v.provider)}</td>
                <td>{v.kind
                  ? <Pill kind={v.kind === "rounding" ? "muted" : v.kind === "env-difference" ? "warn" : "err"}>{v.kind}</Pill>
                  : <Pill kind="ok">match</Pill>}</td>
                <td>{v.kind === "data-difference" && (
                  <button className="btn sm" onClick={() => dispatch({ type: "toast", text: `✨ Anomaly explainer: ${v.worker} net differs by $1.90 — provider applied the new state SUI rate one period early. Reviewer disposition required.` })}>
                    Explain
                  </button>
                )}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="small muted" style={{ marginBottom: 0 }}>Variance taxonomy keeps provider test-environment noise out of the penny-perfect gate.</p>
      </div>
    </>
  );
}
