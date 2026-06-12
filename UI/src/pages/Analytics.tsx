import { useState } from "react";
import { GridBar, PageTitle, Pill } from "../components";
import { DEI_BREAKDOWN, METRICS } from "../data";

export default function Analytics() {
  const [def, setDef] = useState<string | null>(null);
  return (
    <>
      <PageTitle title="Workforce Analytics" sub="Certified metrics — one definition, enterprise-wide" />
      <div className="kpis">
        {METRICS.map((m) => (
          <div className="kpi rowlink" key={m.metric} onClick={() => setDef(def === m.metric ? null : m.metric)}>
            <div className="v">{m.value}</div>
            <div className="l">{m.metric} <span title="Certified metric">✅</span></div>
            <div className={`d ${m.dir}`}>{m.delta}</div>
            {def === m.metric && <div className="small" style={{ marginTop: 6, color: "var(--info)" }}>{m.def}</div>}
          </div>
        ))}
      </div>
      <div className="cols c2">
        <div className="card">
          <GridBar label="Headcount by country (as of 2026-06-11)" />
          <table className="psgrid">
            <thead><tr><th>Country</th><th className="num">Headcount</th></tr></thead>
            <tbody>
              {DEI_BREAKDOWN.map((r) => (
                <tr key={r.group}>
                  <td>{r.group}</td>
                  <td className="num">{r.n !== null ? r.n.toLocaleString() : <span className="suppressed" title="Below n=5, or suppressed so the hidden value can't be recovered by subtraction">— suppressed</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="small muted" style={{ marginBottom: 0 }}>
            n&lt;5 cells never render — and suppression is complementary: a single hidden cell can't be derived by subtracting the rest from the total.
          </p>
        </div>
        <div className="card">
          <h2>Certified snapshots</h2>
          <table className="psgrid">
            <thead><tr><th>As of</th><th>Metric</th><th className="num">Value</th><th>Version</th></tr></thead>
            <tbody>
              <tr><td>2026-06-01</td><td>headcount</td><td className="num">12,802</td><td><Pill kind="warn">v2 · restated</Pill><div className="small muted">retro exit corrected — v1 remains readable</div></td></tr>
              <tr><td>2026-05-01</td><td>headcount</td><td className="num">12,691</td><td><Pill kind="ok">v1</Pill></td></tr>
              <tr><td>2026-06-01</td><td>turnover</td><td className="num">9.4%</td><td><Pill kind="ok">v1</Pill></td></tr>
            </tbody>
          </table>
          <p className="small muted" style={{ marginBottom: 0 }}>
            Snapshots are immutable: corrections create annotated versions. Reports inherit your row/field security —
            a report can never reveal what the UI denies.
          </p>
        </div>
      </div>
    </>
  );
}
