import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { GridBar, PageTitle } from "../components";
import { PEOPLE } from "../data";

export default function Directory() {
  const [params] = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");
  const hits = PEOPLE.filter((p) =>
    (p.name + p.title + p.dept + p.loc).toLowerCase().includes(q.toLowerCase()));
  const chain = ["Dana Whitfield", "Morgan Lee", "Avery Quinn"];

  return (
    <>
      <PageTitle title="Directory & Org" />
      <div className="cols c2" style={{ gridTemplateColumns: "1fr 300px" }}>
        <div className="card">
          <div className="field" style={{ maxWidth: 360 }}>
            <label htmlFor="dq">Search people</label>
            <input id="dq" value={q} placeholder="Name, title, department, location…" onChange={(e) => setQ(e.target.value)} />
          </div>
          <GridBar label="People" count={hits.length} />
          <table className="psgrid">
            <thead><tr><th>Name</th><th>Title</th><th>Department</th><th>Location</th><th>Manager</th></tr></thead>
            <tbody>
              {hits.map((p) => (
                <tr key={p.id}>
                  <td><b>{p.name}</b></td><td>{p.title}</td><td>{p.dept}</td><td>{p.loc}</td><td>{p.mgr ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="small muted" style={{ marginBottom: 0 }}>Results are security-trimmed — you only see what your role can see.</p>
        </div>
        <div className="card">
          <h2>Org chart · your chain</h2>
          {chain.map((n, i) => (
            <div key={n} style={{
              marginLeft: i * 18, background: i === chain.length - 1 ? "#e9f4f2" : "var(--surface-2)",
              border: "1px solid var(--line)", borderRadius: 6, padding: "8px 12px", marginBottom: 8,
            }}>
              <b>{n}</b>
              <div className="small muted">{PEOPLE.find((p) => p.name === n)?.title}</div>
            </div>
          ))}
          <p className="small muted">Profile extras (pronouns, skills, about) are worker-controlled.</p>
        </div>
      </div>
    </>
  );
}
