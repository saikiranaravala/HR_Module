import { GridBar, PageTitle, Pill } from "../components";
import { REQS, STAGES } from "../data";
import { useStore } from "../store";

export default function Recruiting() {
  const { state, dispatch } = useStore();

  const advance = (id: string, cur: string) => {
    const next = STAGES[STAGES.indexOf(cur) + 1];
    if (!next) return;
    dispatch({ type: "advance-candidate", id, stage: next });
    dispatch({ type: "toast", text: `Moved to ${next}.` });
  };

  return (
    <>
      <PageTitle title="Recruiting" sub="Pipeline · AI ranks and explains, you decide — it never rejects" />
      <div className="card">
        <GridBar label="Open requisitions" count={REQS.length} />
        <table className="psgrid">
          <thead><tr><th>Req</th><th>Title</th><th>Grade</th><th>Location</th><th>Posted range</th><th className="num">Applicants</th></tr></thead>
          <tbody>
            {REQS.map((r) => (
              <tr key={r.id}>
                <td><b>{r.id}</b></td><td>{r.title}</td><td>{r.grade}</td><td>{r.loc}</td>
                <td className="small">{r.range}</td><td className="num">{r.applicants}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="card">
        <h2>Pipeline — REQ-1042 Platform Engineer</h2>
        <div className="kanban">
          {STAGES.map((s) => {
            const cards = state.candidates.filter((c) => c.req === "REQ-1042" && c.stage === s);
            return (
              <div className="kcol" key={s}>
                <h3>{s.toUpperCase()} <span>{cards.length}</span></h3>
                {cards.map((c) => (
                  <div className="kcard" key={c.id}>
                    <b>{c.name}</b> {c.internal && <Pill kind="info">internal · confidential</Pill>}
                    {c.aiRank && (
                      <div className="small muted" title={c.aiWhy}>✨ AI rank #{c.aiRank} — {c.aiWhy}</div>
                    )}
                    <div className="btnrow" style={{ marginTop: 6 }}>
                      {s !== "offer" && <button className="btn sm primary" onClick={() => advance(c.id, s)}>Advance ▸</button>}
                      {s === "offer" && <button className="btn sm cta" onClick={() => dispatch({ type: "toast", text: `${c.name}: offer accepted → pre-hire record created, onboarding portal live. Zero re-keying.` })}>Mark accepted</button>}
                      <button className="btn sm" onClick={() => dispatch({ type: "toast", text: "Rejection needs an OFCCP disposition code — pick one in the dialog. (AI can never do this.)", warn: true })}>Reject…</button>
                    </div>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
        <p className="small muted" style={{ marginBottom: 0 }}>
          Internal confidential applications are invisible to the candidate's manager (data wall). Knockouts are
          objective rules, not AI. NYC LL144 audit artifacts are generated per pipeline.
        </p>
      </div>
    </>
  );
}
