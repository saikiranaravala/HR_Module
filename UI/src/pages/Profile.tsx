import { useState } from "react";
import { GridBar, PageTitle, Pill } from "../components";
import { JOB_HISTORY } from "../data";
import { useStore } from "../store";

export default function Profile() {
  const { dispatch } = useStore();
  const [asOf, setAsOf] = useState("2026-06-11");
  const inForce = JOB_HISTORY.filter((r) => r.effDate <= asOf)
    .sort((a, b) => (a.effDate + a.effSeq < b.effDate + b.effSeq ? 1 : -1))[0];

  return (
    <>
      <PageTitle title="Personal Details" sub="Avery Quinn · Worker W-61077" />
      <div className="cols c2">
        <div className="card">
          <h2>Contact & personal</h2>
          {[
            ["Preferred name", "Avery Quinn"],
            ["Work email", "avery.quinn@meridian.example"],
            ["Phone", "+1 512 555 0182"],
            ["Home address", "2204 Juniper Ln, Austin TX 78704"],
            ["Emergency contact", "Dana Quinn · +1 512 555 0440"],
          ].map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--line)" }}>
              <span className="muted">{k}</span><b>{v}</b>
            </div>
          ))}
          <div className="btnrow" style={{ marginTop: 10 }}>
            <button className="btn primary" onClick={() => dispatch({ type: "toast", text: "Address change opened — country-specific validation + approval where statutory." })}>Edit</button>
            <button className="btn" onClick={() => dispatch({ type: "toast", text: "Bank changes need out-of-band confirmation and are frozen 3 days before payday (fraud interlock).", warn: true })}>
              Direct deposit
            </button>
          </div>
          <p className="small muted">National ID & banking are encrypted (T2) — reads are audit-logged.</p>
        </div>
        <div className="card">
          <h2>Job — as of
            <input type="date" value={asOf} onChange={(e) => setAsOf(e.target.value)}
              style={{ marginLeft: 8, fontFamily: "var(--font)", fontSize: 12.5, padding: "3px 6px", border: "1px solid var(--line)", borderRadius: 4 }}
              aria-label="As-of date" />
          </h2>
          {inForce ? (
            <p>
              <b>{inForce.job}</b> · {inForce.dept} · FTE {inForce.fte.toFixed(1)}<br />
              <span className="small muted">In force from {inForce.effDate} (seq {inForce.effSeq}) — {inForce.action} / {inForce.reason}</span>
            </p>
          ) : <p className="muted">No record in force on {asOf}.</p>}
          <GridBar label="Job history (effective-dated)" count={JOB_HISTORY.length} />
          <table className="psgrid">
            <thead><tr><th>Eff date</th><th>Seq</th><th>Action</th><th>Job</th><th>Dept</th></tr></thead>
            <tbody>
              {JOB_HISTORY.map((r) => (
                <tr key={r.effDate + r.effSeq} style={r === inForce ? { outline: "2px solid var(--brand-teal)" } : undefined}>
                  <td>{r.effDate}{r.effDate > asOf && <Pill kind="info">future</Pill>}</td>
                  <td>{r.effSeq}</td><td>{r.action} <span className="muted small">({r.reason})</span></td>
                  <td>{r.job}</td><td>{r.dept}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="small muted" style={{ marginBottom: 0 }}>History is immutable — corrections add rows, retro changes emit retro events.</p>
        </div>
      </div>
    </>
  );
}
