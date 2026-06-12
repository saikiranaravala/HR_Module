import { useState } from "react";
import { GridBar, PageTitle, Pill } from "../components";
import { CASES, KB_SUGGESTIONS } from "../data";
import { useStore } from "../store";

export default function Help() {
  const { dispatch } = useStore();
  const [q, setQ] = useState("");
  const [answer, setAnswer] = useState<typeof KB_SUGGESTIONS[number] | null>(null);
  const [noAnswer, setNoAnswer] = useState(false);

  const ask = () => {
    const hit = KB_SUGGESTIONS.find((s) => q.toLowerCase().split(" ").some((w) => w.length > 3 && s.q.toLowerCase().includes(w)));
    setAnswer(hit ?? null);
    setNoAnswer(!hit && q.trim().length > 0);
  };

  return (
    <>
      <PageTitle title="Help Center" sub="Ask first — answers come from your country & population's policies, with citations" />
      <div className="cols c2">
        <div className="card">
          <h2>Ask Meridian</h2>
          <div className="field">
            <label htmlFor="hq">Your question</label>
            <textarea id="hq" rows={3} value={q} placeholder="e.g. How much parental leave do I get?"
              onChange={(e) => { setQ(e.target.value); setNoAnswer(false); }} />
          </div>
          <div className="btnrow">
            <button className="btn primary" onClick={ask}>Ask</button>
            {KB_SUGGESTIONS.map((s) => (
              <button key={s.q} className="btn sm" onClick={() => { setQ(s.q); setAnswer(s); setNoAnswer(false); }}>{s.q}</button>
            ))}
          </div>
          {answer && (
            <div style={{ marginTop: 12, background: "var(--info-bg)", borderRadius: 6, padding: 12 }}>
              <b>{answer.a}</b>
              <div className="small muted" style={{ marginTop: 6 }}>📎 {answer.cite} · population-scoped retrieval — you never see another country's policy.</div>
              <div className="btnrow" style={{ marginTop: 8 }}>
                <button className="btn sm" onClick={() => dispatch({ type: "toast", text: "Thanks — answer marked helpful (deflection counted only if no case within 72h)." })}>👍 That answered it</button>
                <button className="btn sm" onClick={() => { setNoAnswer(true); setAnswer(null); }}>I still need help</button>
              </div>
            </div>
          )}
          {noAnswer && (
            <div style={{ marginTop: 12, background: "var(--warn-bg)", borderRadius: 6, padding: 12 }}>
              Low confidence — let's get a human. Your conversation transcript attaches automatically (no repeating yourself).
              <div style={{ marginTop: 8 }}>
                <button className="btn cta sm" onClick={() => { dispatch({ type: "toast", text: "Case HR-20492 created — routed to the right queue with your transcript." }); setNoAnswer(false); setQ(""); }}>
                  Create case with transcript
                </button>
              </div>
            </div>
          )}
        </div>
        <div className="card">
          <GridBar label="My cases" count={CASES.length} />
          <table className="psgrid">
            <thead><tr><th>Case</th><th>Topic</th><th>Queue</th><th>SLA</th><th>Status</th></tr></thead>
            <tbody>
              {CASES.map((c) => (
                <tr key={c.id}>
                  <td><b>{c.id}</b><div className="small muted">{c.opened}</div></td>
                  <td>{c.topic}</td><td>{c.queue}</td>
                  <td><Pill kind="warn">{c.sla}</Pill></td>
                  <td><Pill kind="info">{c.status}</Pill></td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="small muted" style={{ marginBottom: 0 }}>
            You see employee-visible notes only. ER topics route to a restricted queue.
          </p>
        </div>
      </div>
    </>
  );
}
