import { useState } from "react";
import { GridBar, PageTitle, Pill } from "../components";
import { GOALS, REVIEW } from "../data";
import { useStore } from "../store";

export default function Performance() {
  const { dispatch } = useStore();
  const [narrative, setNarrative] = useState(REVIEW.aiDraft);
  const [edited, setEdited] = useState(false);

  return (
    <>
      <PageTitle title="Performance" sub={`${REVIEW.cycle} · manager assessment due ${REVIEW.due}`} />
      <div className="cols c2">
        <div className="card">
          <GridBar label="My goals" count={GOALS.length} />
          <table className="psgrid">
            <thead><tr><th>Goal</th><th>Type</th><th className="num">Weight</th><th style={{ width: 160 }}>Progress</th><th>Aligned to</th></tr></thead>
            <tbody>
              {GOALS.map((g) => (
                <tr key={g.id}>
                  <td><b>{g.title}</b></td><td>{g.type}</td><td className="num">{g.weight}%</td>
                  <td><div className="meter"><span style={{ width: `${g.progress}%` }} /></div><span className="small muted">{g.progress}%</span></td>
                  <td className="small">{g.aligned}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="small muted" style={{ marginBottom: 0 }}>Mid-cycle revisions keep the original (version chain). Orphan goals appear on your leader's report.</p>
        </div>
        <div className="card">
          <h2>Review draft <Pill kind="info">AI draft — edit required before submit</Pill></h2>
          <div className="field">
            <textarea rows={7} value={narrative} aria-label="Review narrative"
              onChange={(e) => { setNarrative(e.target.value); setEdited(true); }} />
          </div>
          <div className="btnrow">
            <button className="btn" onClick={() => dispatch({ type: "toast", text: "Bias lint: no gendered / age-coded / personality-vs-behavior terms found." })}>
              Run bias lint
            </button>
            <button className="btn cta" disabled={!edited}
              title={edited ? "" : "AI-drafted text must be edited before submit"}
              onClick={() => dispatch({ type: "toast", text: "Assessment submitted → calibration. Rating entry is yours alone — AI never assigns or recommends one." })}>
              Submit assessment
            </button>
          </div>
          <p className="small muted">Calibration adjustments carry actor + rationale and are immutable. Released reviews amend by dual record, never edits.</p>
          <h2 style={{ marginTop: 14 }}>Check-ins</h2>
          <div className="timeline">
            <div className="tl"><b>Jun 2</b> Growth plan: event-layer ownership <span className="muted small">(shared)</span></div>
            <div className="tl"><b>May 5</b> Workload review <span className="muted small">(shared · manager's private notes are theirs alone)</span></div>
          </div>
        </div>
      </div>
    </>
  );
}
