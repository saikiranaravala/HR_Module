import { useState } from "react";
import { GridBar, PageTitle, Pill } from "../components";
import { useStore } from "../store";

const TYPE_LABEL: Record<string, string> = {
  time: "Time", absence: "Absence", "job-change": "Job Change", comp: "Compensation",
  requisition: "Requisition", learning: "Learning",
};

export default function Approvals() {
  const { state, dispatch } = useStore();
  const [filter, setFilter] = useState<string>("all");
  const [checked, setChecked] = useState<Set<string>>(new Set());

  const items = state.approvals.filter((a) => filter === "all" || a.type === filter);
  const pending = items.filter((a) => a.status === "pending");

  const toggle = (id: string) =>
    setChecked((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });

  return (
    <>
      <PageTitle title="Approvals" sub="One queue for every type — full context at the point of decision"
        right={
          <>
            <select className="btn" value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filter by type">
              <option value="all">All types</option>
              {Object.entries(TYPE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
            <button className="btn cta" disabled={checked.size === 0}
              onClick={() => { dispatch({ type: "bulk-approve", ids: [...checked] }); setChecked(new Set()); }}>
              Bulk approve ({checked.size})
            </button>
          </>
        } />
      <div className="card">
        <GridBar label="Pending approvals" count={pending.length} />
        <table className="psgrid">
          <thead>
            <tr>
              <th style={{ width: 28 }}><span className="muted">☑</span></th>
              <th>Type</th><th>Who</th><th>Request</th><th>Decision context</th><th>Submitted</th><th>Action</th>
            </tr>
          </thead>
          <tbody>
            {items.map((a) => (
              <tr key={a.id}>
                <td>
                  {a.status === "pending" && (
                    <input type="checkbox" aria-label={`Select ${a.subject}`} checked={checked.has(a.id)}
                      onChange={() => toggle(a.id)} />
                  )}
                </td>
                <td>
                  {TYPE_LABEL[a.type]}{" "}
                  {a.bulkBarred && <Pill kind="warn">individual review</Pill>}
                </td>
                <td><b>{a.subject}</b></td>
                <td>{a.detail}</td>
                <td className="small muted">{a.context}</td>
                <td className="small">{a.submitted}</td>
                <td>
                  {a.status === "pending" ? (
                    <span className="btnrow">
                      <button className="btn primary sm" onClick={() => dispatch({ type: "approve", id: a.id, approve: true })}>Approve</button>
                      <button className="btn sm" onClick={() => dispatch({ type: "approve", id: a.id, approve: false })}>Reject</button>
                    </span>
                  ) : (
                    <Pill kind={a.status === "approved" ? "ok" : "err"}>{a.status}</Pill>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="small muted" style={{ marginBottom: 0 }}>
          Delegation active: none · Out-of-office auto-route: off · Comp items are never bulk-approvable (guardrail).
        </p>
      </div>
    </>
  );
}
