import { GridBar, PageTitle, Pill } from "../components";
import { KEY_POSITIONS, NINEBOX } from "../data";
import { useStore } from "../store";

const PERF = ["below", "meets", "exceeds"];
const POT = ["high", "medium", "low"];

export default function Succession() {
  const { dispatch } = useStore();
  return (
    <>
      <PageTitle title="Succession" sub="Most-confidential domain — every view is read-audited"
        right={<span className="tier t3">T3 · read-logged</span>} />
      <div className="card">
        <GridBar label="Key positions" count={KEY_POSITIONS.length} />
        <table className="psgrid">
          <thead><tr><th>Position</th><th>Incumbent</th><th className="num">Criticality</th><th>Retirement band</th><th>Slate</th><th /></tr></thead>
          <tbody>
            {KEY_POSITIONS.map((k) => (
              <tr key={k.id}>
                <td><b>{k.title}</b></td><td>{k.incumbent}</td>
                <td className="num">{k.criticality}</td>
                <td>{k.band} <span className="muted small">(band, never a date)</span></td>
                <td>
                  {k.gap
                    ? <Pill kind="err">gap — no ready-now</Pill>
                    : <Pill kind="ok">{k.ready} ready-now · {k.dev} developing</Pill>}
                </td>
                <td><button className="btn sm primary"
                  onClick={() => dispatch({ type: "toast", text: `Slate opened for ${k.title} — this T3 read was just audit-logged under your id.` })}>
                  View slate
                </button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="small muted" style={{ marginBottom: 0 }}>
          Incumbents can never see their own slate — whatever roles they hold. One person on 3+ slates raises a concentration-risk flag.
        </p>
      </div>
      <div className="card">
        <h2>9-box — Platform org · session tr-FY26 <span className="muted small">(placements append-only; rationale mandatory)</span></h2>
        <div className="ninebox">
          {POT.map((pot) =>
            PERF.map((perf) => (
              <div className="cell" key={`${perf}:${pot}`}>
                <h4>{perf} × {pot}</h4>
                {(NINEBOX[`${perf}:${pot}`] ?? []).map((n) => (
                  <span className="chip" key={n}
                    onClick={() => dispatch({ type: "toast", text: `Moving ${n} requires a rationale — every adjustment is minuted with actor + reason.`, warn: true })}>
                    {n}
                  </span>
                ))}
              </div>
            )))}
        </div>
        <p className="small muted" style={{ marginBottom: 0 }}>Performance axis consumes PERF ratings as opaque values (ratings-philosophy gate). AI never assigns potential.</p>
      </div>
    </>
  );
}
