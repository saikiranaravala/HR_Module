import { useState } from "react";
import { GridBar, Modal, PageTitle, Pill } from "../components";
import { ELECTIONS, LIFE_EVENTS, money } from "../data";
import { useStore } from "../store";

export default function Benefits() {
  const { dispatch } = useStore();
  const [lifeEvent, setLifeEvent] = useState<string | null>(null);
  const perPay = ELECTIONS.reduce((s, e) => s + e.perPay, 0);

  return (
    <>
      <PageTitle title="Benefits" sub="Current elections · life events · total rewards"
        right={<button className="btn cta" onClick={() => setLifeEvent("")}>Report a life event</button>} />
      <div className="kpis">
        <div className="kpi"><div className="v">{money(perPay)}</div><div className="l">Your cost per paycheck</div></div>
        <div className="kpi"><div className="v">{money(perPay * 24 * 2.4)}</div><div className="l">Employer contribution / yr (total rewards)</div></div>
        <div className="kpi"><div className="v">Nov 1–15</div><div className="l">Next Open Enrollment</div></div>
      </div>
      <div className="card">
        <GridBar label="Current elections" count={ELECTIONS.length} />
        <table className="psgrid">
          <thead><tr><th>Plan</th><th>Option</th><th>Coverage</th><th className="num">Per pay</th><th>Status</th></tr></thead>
          <tbody>
            {ELECTIONS.map((e) => (
              <tr key={e.plan}>
                <td><b>{e.plan}</b></td><td>{e.option}</td><td>{e.coverage}</td>
                <td className="num">{money(e.perPay)}</td>
                <td><Pill kind="ok">{e.status}</Pill></td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="small muted" style={{ marginBottom: 0 }}>
          New-hire rule: coverage starts the first of the month after 30 days of service. Outside a window? Only a
          qualifying life event can change elections (Section 125).
        </p>
      </div>

      {lifeEvent !== null && (
        <Modal title="Report a life event" onClose={() => setLifeEvent(null)}
          foot={
            <>
              <button className="btn" onClick={() => setLifeEvent(null)}>Cancel</button>
              <button className="btn cta" disabled={!lifeEvent}
                onClick={() => {
                  dispatch({ type: "toast", text: `Life event "${lifeEvent}" opened — allowed changes unlocked for 30–60 days. Documentation may be required.` });
                  setLifeEvent(null);
                }}>
                Start
              </button>
            </>
          }>
          <div className="field">
            <label htmlFor="le">Event type</label>
            <select id="le" value={lifeEvent} onChange={(e) => setLifeEvent(e.target.value)}>
              <option value="">Select…</option>
              {LIFE_EVENTS.map((e) => <option key={e}>{e}</option>)}
            </select>
          </div>
          <p className="small muted">
            Each event unlocks only its consistent changes (e.g. birth → add dependent / change option). Late
            divorce reports are capped at the carrier's 60-day retroactive limit.
          </p>
        </Modal>
      )}
    </>
  );
}
