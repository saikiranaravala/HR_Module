import { GridBar, PageTitle, Pill } from "../components";
import { CERTS, REQUIREMENTS } from "../data";
import { useStore } from "../store";

export default function Learning() {
  const { dispatch } = useStore();
  return (
    <>
      <PageTitle title="Learning & Compliance" sub="Deadline-sorted · one-click launch" />
      <div className="card">
        <GridBar label="My requirements" count={REQUIREMENTS.length} />
        <table className="psgrid">
          <thead><tr><th>Requirement</th><th>Regulation</th><th>Due</th><th style={{ width: 150 }}>Progress</th><th>Status</th><th /></tr></thead>
          <tbody>
            {REQUIREMENTS.map((r) => (
              <tr key={r.id}>
                <td><b>{r.name}</b></td>
                <td className="small">{r.reg}</td>
                <td>{r.due}</td>
                <td><div className={`meter ${r.status === "overdue" ? "over" : ""}`}><span style={{ width: `${r.pct}%` }} /></div></td>
                <td>
                  <Pill kind={r.status === "overdue" ? "err" : r.status === "in-progress" ? "warn" : "muted"}>{r.status}</Pill>
                  {"consequence" in r && r.consequence && <div className="small" style={{ color: "var(--err)" }}>{String(r.consequence)}</div>}
                </td>
                <td><button className="btn primary sm"
                  onClick={() => dispatch({ type: "toast", text: `Launching "${r.name}" — resume protected: a corrupted save never costs you an attempt.` })}>
                  {r.pct > 0 ? "Resume" : "Launch"}
                </button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="small muted" style={{ marginBottom: 0 }}>On leave? Your compliance clock pauses automatically. Completions pin the exact content version for audit.</p>
      </div>
      <div className="card">
        <GridBar label="Certifications & licenses" count={CERTS.length} />
        <table className="psgrid">
          <thead><tr><th>Certification</th><th>Issuer</th><th>Expires</th><th>Alert</th></tr></thead>
          <tbody>
            {CERTS.map((c) => (
              <tr key={c.name}>
                <td><b>{c.name}</b> {"jobRequired" in c && c.jobRequired && <Pill kind="info">job-required</Pill>}</td>
                <td>{c.issuer}</td><td>{c.expires}</td>
                <td><Pill kind={c.daysLeft <= 30 ? "err" : c.daysLeft <= 60 ? "warn" : "ok"}>{c.daysLeft} days</Pill></td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="small muted" style={{ marginBottom: 0 }}>Lapsed job-required certs raise a compliance flag (and may block safety-critical assignments — policy decides).</p>
      </div>
    </>
  );
}
