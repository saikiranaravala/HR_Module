import { useState } from "react";
import { GridBar, Modal, PageTitle, Pill } from "../components";
import { CYCLE, money } from "../data";
import { useStore } from "../store";

export default function CompCycle() {
  const { state, dispatch } = useStore();
  const [editing, setEditing] = useState<string | null>(null);
  const [pct, setPct] = useState("3");
  const [just, setJust] = useState("");

  const committed = state.worksheet.reduce((s, l) => s + (l.merit ? (l.salary * l.merit) / 100 : 0), 0);
  const pctUsed = Math.min(100, (committed / CYCLE.budget) * 100);
  const line = state.worksheet.find((l) => l.id === editing);
  const out = line ? +pct < line.guideline[0] || +pct > line.guideline[1] : false;

  return (
    <>
      <PageTitle title={`Comp Cycle — ${CYCLE.name}`} sub={`FX ${CYCLE.fxLocked} · population frozen at cycle open`} />
      <div className="card">
        <h2>Budget</h2>
        <div className={`meter ${pctUsed > 85 ? "warn" : ""} ${pctUsed >= 100 ? "over" : ""}`}><span style={{ width: `${pctUsed}%` }} /></div>
        <p className="small muted">{money(committed)} committed of {money(CYCLE.budget)} pool ({pctUsed.toFixed(0)}%) — live as you type.</p>
        <GridBar label="Worksheet" count={state.worksheet.length} />
        <table className="psgrid">
          <thead>
            <tr><th>Worker</th><th className="num">Salary</th><th className="num">Compa</th><th>Rating</th><th>Guideline</th><th className="num">Merit %</th><th className="num">New salary</th><th /></tr>
          </thead>
          <tbody>
            {state.worksheet.map((l) => (
              <tr key={l.id}>
                <td><b>{l.name}</b>{l.routed && <div><Pill kind="info">routed to skip-level</Pill></div>}</td>
                <td className="num">{money(l.salary)}</td>
                <td className="num">{l.compa.toFixed(2)} <span className="muted small">Q{l.quartile}</span></td>
                <td>{l.rating}</td>
                <td className="small">{l.guideline[0]}–{l.guideline[1]}%</td>
                <td className="num">
                  {l.merit != null ? <b>{l.merit}%</b> : <span className="muted">—</span>}
                  {l.justification && <div className="small muted" title={l.justification}>⚑ justified</div>}
                </td>
                <td className="num">{l.merit != null ? money(l.salary * (1 + l.merit / 100)) : "—"}</td>
                <td>
                  {l.routed
                    ? <span className="small muted">your record — your manager decides</span>
                    : <button className="btn sm primary" onClick={() => { setEditing(l.id); setPct(String(l.merit ?? l.guideline[0])); setJust(l.justification ?? ""); }}>Recommend</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="small muted" style={{ marginBottom: 0 }}>
          Guideline matrix: rating × compa-quartile (config — ratingless-ready). Out-of-guideline needs justification and routes for approval.
        </p>
      </div>

      {line && (
        <Modal title={`Recommend — ${line.name}`} onClose={() => setEditing(null)}
          foot={
            <>
              <button className="btn" onClick={() => setEditing(null)}>Cancel</button>
              <button className="btn cta"
                onClick={() => { dispatch({ type: "merit", id: line.id, pct: +pct, justification: just || undefined }); setEditing(null); }}>
                Save
              </button>
            </>
          }>
          <div className="formrow">
            <div className="field"><label htmlFor="mp">Merit %</label>
              <input id="mp" type="number" step="0.5" min="0" max="20" value={pct} onChange={(e) => setPct(e.target.value)} /></div>
            <div className="field"><label>Guideline ({line.rating} × Q{line.quartile})</label>
              <input value={`${line.guideline[0]}–${line.guideline[1]}%`} disabled /></div>
          </div>
          {out && (
            <div className="field">
              <label htmlFor="jt">Out-of-guideline justification (mandatory)</label>
              <textarea id="jt" rows={2} value={just} onChange={(e) => setJust(e.target.value)} placeholder="e.g. retention risk, critical skill…" />
            </div>
          )}
          <p className="small muted">New salary: <b>{money(line.salary * (1 + +pct / 100))}</b> · budget impact {money((line.salary * +pct) / 100)}</p>
        </Modal>
      )}
    </>
  );
}
