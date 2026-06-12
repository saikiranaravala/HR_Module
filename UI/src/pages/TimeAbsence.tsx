import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Modal, PageTitle, Pill } from "../components";
import { ACCRUALS } from "../data";
import { useStore } from "../store";

export default function TimeAbsence() {
  const { state, dispatch } = useStore();
  const [params, setParams] = useSearchParams();
  const [open, setOpen] = useState(params.get("request") === "1");
  const [start, setStart] = useState("2026-06-22");
  const [end, setEnd] = useState("2026-06-26");

  const days = Math.max(1, Math.round((+new Date(end) - +new Date(start)) / 86400000) + 1 - 2); // rough workdays
  const balance = ACCRUALS.reduce((s, a) => s + (a.plan.startsWith("PTO") ? a.balance : 0), 0);
  const yearEnd = balance + 7.5 - days; // remaining accrual this year minus request

  const close = () => { setOpen(false); params.delete("request"); setParams(params, { replace: true }); };

  return (
    <>
      <PageTitle title="Time & Absence"
        right={<button className="btn cta" onClick={() => setOpen(true)}>Request time off</button>} />
      <div className="cols c3">
        <div className="card">
          <h2>Balances</h2>
          <table className="psgrid">
            <thead><tr><th>Plan</th><th className="num">Days</th><th /></tr></thead>
            <tbody>
              {ACCRUALS.map((a) => (
                <tr key={a.plan}>
                  <td>{a.plan}</td><td className="num"><b>{a.balance.toFixed(1)}</b></td>
                  <td>{a.expires && <Pill kind="warn">expires {a.expires}</Pill>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="small muted">FIFO consumption: expiring carryover is used first.</p>
        </div>
        <div className="card">
          <h2>Punch</h2>
          <p className="muted small">Geofenced · Austin HQ</p>
          <div className="btnrow">
            <button className="btn primary" onClick={() => dispatch({ type: "toast", text: "Punched IN at " + new Date().toLocaleTimeString() })}>Punch in</button>
            <button className="btn" onClick={() => dispatch({ type: "toast", text: "Punched OUT at " + new Date().toLocaleTimeString() })}>Punch out</button>
          </div>
          <p className="small muted" style={{ marginTop: 10 }}>This week: 32.0h regular · 0h OT<br />OT rule: US FLSA weekly-40 (v3)</p>
        </div>
        <div className="card">
          <h2>Requests</h2>
          {state.ptoRequested ? (
            <p><Pill kind="warn">pending approval</Pill> {state.ptoRequested.start} → {state.ptoRequested.end} ({state.ptoRequested.days}d) · approver: Morgan Lee</p>
          ) : (
            <p className="muted">No open requests.</p>
          )}
          <div className="timeline">
            <div className="tl"><b>Apr 3–4</b> PTO · approved</div>
            <div className="tl"><b>Feb 17</b> Sick · auto-approved</div>
          </div>
        </div>
      </div>

      {open && (
        <Modal title="Request time off" onClose={close}
          foot={
            <>
              <button className="btn" onClick={close}>Cancel</button>
              <button className="btn cta" onClick={() => { dispatch({ type: "request-pto", start, end, days }); close(); }}>
                Submit request
              </button>
            </>
          }>
          <div className="formrow">
            <div className="field"><label htmlFor="s">First day</label><input id="s" type="date" value={start} onChange={(e) => setStart(e.target.value)} /></div>
            <div className="field"><label htmlFor="e">Last day</label><input id="e" type="date" value={end} onChange={(e) => setEnd(e.target.value)} /></div>
          </div>
          <div className="card" style={{ background: "var(--info-bg)", boxShadow: "none", marginBottom: 0 }}>
            <b>{days} working days</b> · balance after approval: <b>{(balance - days).toFixed(1)}d</b>
            <div className="small muted">If you take these days, your balance on Dec 31 will be ≈ {yearEnd.toFixed(1)}d.</div>
            <div className="small muted">Team calendar: no conflicts in your team that week. ✅</div>
          </div>
        </Modal>
      )}
    </>
  );
}
