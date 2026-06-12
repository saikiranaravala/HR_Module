import { useState } from "react";
import { GridBar, PageTitle, Pill } from "../components";
import { PAYSLIPS, money, type PayslipLine } from "../data";

function LineRow({ l }: { l: PayslipLine }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <tr className="rowlink" onClick={() => l.note && setOpen((v) => !v)}>
        <td>{l.element} {l.note && <span className="muted small">ⓘ</span>}</td>
        <td className="num" style={{ color: l.current < 0 ? "var(--err)" : undefined }}>{money(l.current)}</td>
        <td className="num muted">{money(l.ytd)}</td>
        <td><Pill kind={l.kind === "earning" ? "ok" : l.kind === "tax" ? "info" : "muted"}>{l.kind}</Pill></td>
      </tr>
      {open && l.note && (
        <tr><td colSpan={4} className="small" style={{ background: "var(--info-bg)" }}>💡 {l.note}</td></tr>
      )}
    </>
  );
}

export default function Payslips() {
  const [sel, setSel] = useState(PAYSLIPS[0]);
  const [explain, setExplain] = useState(false);

  return (
    <>
      <PageTitle title="Payslips" sub="Tap any line for a plain-language explanation"
        right={<button className="btn">⬇ PDF</button>} />
      <div className="cols c2" style={{ gridTemplateColumns: "280px 1fr" }}>
        <div className="card">
          <GridBar label="Pay periods" count={PAYSLIPS.length} />
          <table className="psgrid">
            <thead><tr><th>Period</th><th className="num">Net</th></tr></thead>
            <tbody>
              {PAYSLIPS.map((p) => (
                <tr key={p.id} className="rowlink" onClick={() => { setSel(p); setExplain(false); }}
                  style={sel.id === p.id ? { outline: "2px solid var(--brand-teal)" } : undefined}>
                  <td>{p.period}<div className="small muted">paid {p.payDate}</div></td>
                  <td className="num"><b>{money(p.net)}</b></td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="small muted">Year-end docs: <a href="#" onClick={(e) => e.preventDefault()}>W-2 vault</a></p>
        </div>
        <div className="card">
          <h2>{sel.period} <span className="muted small">· paid {sel.payDate}</span></h2>
          <div className="kpis">
            <div className="kpi"><div className="v">{money(sel.gross)}</div><div className="l">Gross</div></div>
            <div className="kpi"><div className="v">{money(sel.net)}</div><div className="l">Net pay</div></div>
            <div className="kpi"><div className="v">{money(sel.gross - sel.net)}</div><div className="l">Taxes + deductions</div></div>
          </div>
          {sel.deltaNote && (
            <p>
              <button className="btn primary sm" onClick={() => setExplain((v) => !v)}>
                ✨ Explain my payslip change
              </button>
              {explain && (
                <span className="small" style={{ display: "block", marginTop: 8, background: "var(--info-bg)", padding: 10, borderRadius: 6 }}>
                  {sel.deltaNote}
                  <br /><span className="muted">Grounded in your pay elements · AI Gateway use case “payslip-explain” · drafts only, never changes pay.</span>
                </span>
              )}
            </p>
          )}
          {sel.lines.length > 0 ? (
            <table className="psgrid">
              <thead><tr><th>Element</th><th className="num">Current</th><th className="num">YTD</th><th>Type</th></tr></thead>
              <tbody>{sel.lines.map((l) => <LineRow key={l.element} l={l} />)}</tbody>
            </table>
          ) : (
            <p className="muted">Element detail loads from the immutable result snapshot for this period.</p>
          )}
        </div>
      </div>
    </>
  );
}
