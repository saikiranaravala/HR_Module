import { GridBar, PageTitle, Pill } from "../components";
import { TEAM, TEAM_ABSENCES } from "../data";
import { useStore } from "../store";

export default function Team() {
  const { dispatch } = useStore();
  const days = Array.from({ length: 28 }, (_, i) => i + 1);
  const absentBy = (d: number) => TEAM_ABSENCES.filter((a) => a.days.includes(d)).map((a) => a.who.split(" ")[0]);

  return (
    <>
      <PageTitle title="My Team" sub="Roster, time compliance, absence heat-map — June 2026" />
      <div className="cols c2">
        <div className="card">
          <GridBar label="Roster" count={TEAM.length} />
          <table className="psgrid">
            <thead><tr><th>Name</th><th>Status</th><th className="num">Compa-ratio</th><th>Last increase</th><th>Timesheet</th><th>Rating</th><th /></tr></thead>
            <tbody>
              {TEAM.map((m) => (
                <tr key={m.name}>
                  <td><b>{m.name}</b></td>
                  <td className="small">{m.status}</td>
                  <td className="num">{m.compa.toFixed(2)}</td>
                  <td className="small">{m.lastIncrease}</td>
                  <td>{m.timesheet === "missing"
                    ? <button className="btn sm cta" onClick={() => dispatch({ type: "toast", text: `Nudge sent to ${m.name} — missing timesheet` })}>Nudge</button>
                    : <Pill kind="ok">submitted</Pill>}</td>
                  <td className="small">{m.rating}</td>
                  <td className="small"><a href="#" onClick={(e) => { e.preventDefault(); dispatch({ type: "toast", text: `Guided transactions for ${m.name}: transfer · promote · comp change · termination` }); }}>Actions ▾</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card">
          <h2>Absence heat-map · June</h2>
          <div className="calendar" role="grid" aria-label="Team absences in June">
            {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => <div key={i} className="day head">{d}</div>)}
            {days.map((d) => {
              const who = absentBy(d);
              return (
                <div key={d} className={`day ${who.length ? "absent" : ""}`}>
                  <b>{d}</b>{who.length > 0 && <div>{who.join(", ")}</div>}
                </div>
              );
            })}
          </div>
          <p className="small muted">Pending: Jordan 22–26 (awaiting your approval) · Conflict check: none</p>
          <h2 style={{ marginTop: 14 }}>Headcount vs budget</h2>
          <div className="meter"><span style={{ width: "75%" }} /></div>
          <p className="small muted">3 filled of 4 budgeted · 1 open requisition (REQ-1042)</p>
        </div>
      </div>
    </>
  );
}
