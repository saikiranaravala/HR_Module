/* Demo data layer. Shapes mirror the backend services (src/<module>/) so this
   file is replaceable by the REST client when the API layer lands — every id
   and field name matches the Python models. All data is synthetic. */

export type Persona = "employee" | "manager" | "hr";

export const PERSONAS: Record<Persona, { name: string; initials: string; title: string; homepage: string }> = {
  employee: { name: "Avery Quinn", initials: "AQ", title: "Senior Platform Engineer", homepage: "Employee Self Service" },
  manager: { name: "Morgan Lee", initials: "ML", title: "Director, Platform Engineering", homepage: "Manager Self Service" },
  hr: { name: "Sam Rivera", initials: "SR", title: "HR Operations Lead", homepage: "Workforce Administrator" },
};

/* ---------- Approvals (rules_workflow + ess_mss.inbox) ---------- */
export interface Approval {
  id: string; type: "time" | "absence" | "job-change" | "comp" | "requisition" | "learning";
  subject: string; detail: string; submitted: string; status: "pending" | "approved" | "rejected";
  context?: string; bulkBarred?: boolean;
}
export const APPROVALS: Approval[] = [
  { id: "ap-1", type: "absence", subject: "Jordan Patel", detail: "PTO 2026-06-22 → 06-26 (5d)", submitted: "2026-06-09", status: "pending", context: "Balance after: 11.5d · no team conflicts" },
  { id: "ap-2", type: "time", subject: "Riley Chen", detail: "Timesheet week of 06-01 · 42.5h (2.5h OT)", submitted: "2026-06-08", status: "pending", context: "OT rule: US-FLSA weekly-40 v3" },
  { id: "ap-3", type: "comp", subject: "Jordan Patel", detail: "Merit +9% → $98,100 (out of guideline)", submitted: "2026-06-08", status: "pending", context: "Compa-ratio 0.87 → 0.95 · justification: retention risk", bulkBarred: true },
  { id: "ap-4", type: "job-change", subject: "Riley Chen", detail: "Transfer to Data Platform, eff 2026-07-01", submitted: "2026-06-07", status: "pending", context: "Position 41002 · budget OK" },
  { id: "ap-5", type: "learning", subject: "Sasha Kim", detail: "External course: Advanced K8s ($1,800)", submitted: "2026-06-05", status: "pending", context: "Team budget remaining: $4,200" },
];

/* ---------- Payslips (payroll_hub) ---------- */
export interface PayslipLine { element: string; current: number; ytd: number; kind: "earning" | "deduction" | "tax" | "employer"; note?: string }
export interface Payslip { id: string; period: string; payDate: string; gross: number; net: number; deltaNote?: string; lines: PayslipLine[] }
export const PAYSLIPS: Payslip[] = [
  {
    id: "ps-2026-05B", period: "May 16–31, 2026", payDate: "2026-06-05", gross: 4262.5, net: 2748.1,
    deltaNote: "Net is $96.40 lower than last period: your benefits Open Enrollment elections (EE+FAM medical) started this cycle.",
    lines: [
      { element: "Base salary", current: 4166.67, ytd: 41666.7, kind: "earning", note: "Annual $100,000 · semi-monthly" },
      { element: "Overtime 1.5×", current: 95.83, ytd: 1437.45, kind: "earning", note: "2.5h @ $38.33 (FLSA weekly-40, rule v3)" },
      { element: "Medical EE+FAM", current: -225.0, ytd: -450.0, kind: "deduction", note: "OE election eff 2026-05-01 · employer pays 70%" },
      { element: "401(k) 6%", current: -255.75, ytd: -2557.5, kind: "deduction" },
      { element: "Federal income tax", current: -612.4, ytd: -6124.0, kind: "tax" },
      { element: "Social Security / Medicare", current: -326.1, ytd: -3261.0, kind: "tax" },
      { element: "GTL imputed income", current: 10.0, ytd: 100.0, kind: "earning", note: "Coverage $150k, age 40 — Table I" },
    ],
  },
  { id: "ps-2026-05A", period: "May 1–15, 2026", payDate: "2026-05-20", gross: 4166.67, net: 2844.5, lines: [] },
  { id: "ps-2026-04B", period: "Apr 16–30, 2026", payDate: "2026-05-05", gross: 4166.67, net: 2844.5, lines: [] },
];

/* ---------- Time & absence (time_labor) ---------- */
export interface AccrualLot { plan: string; balance: number; expires?: string }
export const ACCRUALS: AccrualLot[] = [
  { plan: "PTO", balance: 16.5 },
  { plan: "PTO carryover", balance: 3.0, expires: "2026-06-30" },
  { plan: "Sick", balance: 24.0 },
];
export const TEAM_ABSENCES = [
  { who: "Riley Chen", days: [22, 23] },
  { who: "Sasha Kim", days: [25] },
];

/* ---------- Benefits ---------- */
export interface Election { plan: string; option: string; coverage: string; perPay: number; status: string }
export const ELECTIONS: Election[] = [
  { plan: "Medical — PPO Standard", option: "EE+FAM", coverage: "You + family", perPay: 225.0, status: "active" },
  { plan: "Dental", option: "EE", coverage: "You", perPay: 18.5, status: "active" },
  { plan: "Group Term Life", option: "3×", coverage: "$300,000", perPay: 12.4, status: "active" },
  { plan: "401(k)", option: "6%", coverage: "Traditional", perPay: 255.75, status: "active" },
];
export const LIFE_EVENTS = ["Marriage", "Birth / adoption", "Divorce", "Dependent aging out"];

/* ---------- Profile / job (core_hr — temporal) ---------- */
export interface JobRow { effDate: string; effSeq: number; action: string; reason: string; job: string; dept: string; fte: number }
export const JOB_HISTORY: JobRow[] = [
  { effDate: "2026-07-01", effSeq: 0, action: "Transfer", reason: "Org transfer", job: "Sr Platform Engineer", dept: "Data Platform", fte: 1.0 },
  { effDate: "2024-04-01", effSeq: 1, action: "Comp change", reason: "Merit", job: "Sr Platform Engineer", dept: "Platform Eng", fte: 1.0 },
  { effDate: "2024-04-01", effSeq: 0, action: "Promotion", reason: "Promotion", job: "Sr Platform Engineer", dept: "Platform Eng", fte: 1.0 },
  { effDate: "2021-03-15", effSeq: 0, action: "Hire", reason: "New hire", job: "Platform Engineer", dept: "Platform Eng", fte: 1.0 },
];

/* ---------- Directory ---------- */
export interface Person { id: string; name: string; title: string; dept: string; loc: string; mgr?: string }
export const PEOPLE: Person[] = [
  { id: "p1", name: "Avery Quinn", title: "Sr Platform Engineer", dept: "Platform Eng", loc: "Austin, US", mgr: "Morgan Lee" },
  { id: "p2", name: "Morgan Lee", title: "Director, Platform Eng", dept: "Platform Eng", loc: "Austin, US", mgr: "Dana Whitfield" },
  { id: "p3", name: "Jordan Patel", title: "Platform Engineer", dept: "Platform Eng", loc: "Denver, US", mgr: "Morgan Lee" },
  { id: "p4", name: "Riley Chen", title: "Platform Engineer", dept: "Platform Eng", loc: "Austin, US", mgr: "Morgan Lee" },
  { id: "p5", name: "Sasha Kim", title: "Assoc Platform Engineer", dept: "Platform Eng", loc: "Berlin, DE", mgr: "Morgan Lee" },
  { id: "p6", name: "Dana Whitfield", title: "VP Engineering", dept: "Engineering", loc: "Austin, US" },
];

/* ---------- Team (MSS) ---------- */
export const TEAM = [
  { name: "Jordan Patel", status: "PTO requested", compa: 0.87, lastIncrease: "2025-04", timesheet: "missing", rating: "exceeds" },
  { name: "Riley Chen", status: "active", compa: 1.02, lastIncrease: "2025-04", timesheet: "submitted", rating: "meets" },
  { name: "Sasha Kim", status: "new hire · day 34", compa: 0.95, lastIncrease: "—", timesheet: "submitted", rating: "—" },
];

/* ---------- Comp cycle (compensation) ---------- */
export interface WorksheetLine { id: string; name: string; salary: number; compa: number; quartile: number; rating: string; guideline: [number, number]; merit: number | null; justification?: string; routed?: boolean }
export const WORKSHEET: WorksheetLine[] = [
  { id: "wl-1", name: "Jordan Patel", salary: 90000, compa: 0.87, quartile: 1, rating: "exceeds", guideline: [5, 8], merit: null },
  { id: "wl-2", name: "Riley Chen", salary: 102000, compa: 1.02, quartile: 3, rating: "meets", guideline: [1, 3], merit: null },
  { id: "wl-3", name: "Sasha Kim", salary: 95000, compa: 0.95, quartile: 2, rating: "meets", guideline: [2, 4], merit: null },
  { id: "wl-4", name: "Morgan Lee", salary: 150000, compa: 1.05, quartile: 3, rating: "meets", guideline: [1, 3], merit: null, routed: true },
];
export const CYCLE = { name: "FY26 Merit", budget: 18000, currency: "USD", fxLocked: "EUR 1.10 (locked 2026-04-01)" };

/* ---------- Recruiting ---------- */
export interface Candidate { id: string; name: string; req: string; stage: string; aiRank?: number; aiWhy?: string; internal?: boolean }
export const REQS = [
  { id: "REQ-1042", title: "Platform Engineer", grade: "G7", loc: "Austin, US", status: "open", range: "$80,000–$120,000 (disclosed per US-CO)", applicants: 24 },
  { id: "REQ-1057", title: "Data Engineer", grade: "G7", loc: "Berlin, DE", status: "open", range: "€70.000–€95.000 (EU directive)", applicants: 11 },
];
export const STAGES = ["new", "screen", "interview", "offer"];
export const CANDIDATES: Candidate[] = [
  { id: "c1", name: "Taylor Brooks", req: "REQ-1042", stage: "interview", aiRank: 1, aiWhy: "8y K8s + payments scale; matches 9/10 skills" },
  { id: "c2", name: "Jamie Fox", req: "REQ-1042", stage: "screen", aiRank: 2, aiWhy: "Strong infra background; missing on-call depth" },
  { id: "c3", name: "Casey Morgan", req: "REQ-1042", stage: "new", aiRank: 3, aiWhy: "Adjacent experience (SRE)" },
  { id: "c4", name: "Alex Internal", req: "REQ-1042", stage: "screen", internal: true },
  { id: "c5", name: "Robin Stone", req: "REQ-1057", stage: "offer" },
];

/* ---------- Performance ---------- */
export const GOALS = [
  { id: "g1", title: "Ship event-layer v1", type: "OKR", weight: 40, progress: 70, aligned: "Platform reliability (org)" },
  { id: "g2", title: "Cut p99 compile latency 30%", type: "OKR", weight: 35, progress: 45, aligned: "Platform reliability (org)" },
  { id: "g3", title: "Mentor 2 associate engineers", type: "Development", weight: 25, progress: 80, aligned: "—" },
];
export const REVIEW = {
  cycle: "FY26 Annual", state: "manager-assessment", due: "2026-07-15",
  aiDraft: "[AI draft — review and edit] Avery delivered the event-layer milestone ahead of plan and reduced compile latency by 22% to date, with measurable reliability gains across three dependent teams…",
};

/* ---------- Learning ---------- */
export const REQUIREMENTS = [
  { id: "r1", name: "Harassment prevention (CA supervisor, 2h)", reg: "CA SB1343", due: "2026-06-30", status: "in-progress", pct: 60 },
  { id: "r2", name: "Code of conduct", reg: "Policy", due: "2026-12-31", status: "assigned", pct: 0 },
  { id: "r3", name: "Lockout/Tagout authorized", reg: "OSHA 1910.147", due: "2026-06-15", status: "overdue", pct: 0, consequence: "safety assignment-block flag" },
];
export const CERTS = [
  { name: "AWS Solutions Architect", issuer: "AWS", expires: "2026-09-14", daysLeft: 95 },
  { name: "Forklift license", issuer: "State of TX", expires: "2026-07-02", daysLeft: 21, jobRequired: true },
];

/* ---------- Succession (T3) ---------- */
export const KEY_POSITIONS = [
  { id: "kp1", title: "VP Finance EMEA", incumbent: "L. Moreau", criticality: 26, band: "3-5y", ready: 1, dev: 2 },
  { id: "kp2", title: "Director, Payroll Ops", incumbent: "T. Okafor", criticality: 22, band: ">5y", ready: 0, dev: 1, gap: true },
];
export const NINEBOX: Record<string, string[]> = {
  "exceeds:high": ["J. Patel"], "exceeds:medium": ["T. Brooks"], "meets:high": ["R. Chen"],
  "meets:medium": ["S. Kim", "A. Internal"], "meets:low": [], "below:high": [],
  "exceeds:low": [], "below:medium": [], "below:low": [],
};

/* ---------- Analytics ---------- */
export const METRICS = [
  { metric: "Headcount", value: "12,847", delta: "+1.2% MoM", dir: "up", def: "Active workers at the as-of date (PIT on SCD2 validity)." },
  { metric: "Turnover (annualized)", value: "9.4%", delta: "−0.6pt", dir: "up", def: "Annualized exits over average active population." },
  { metric: "Regrettable share", value: "31%", delta: "+2pt", dir: "down", def: "Share of exits tagged regrettable." },
  { metric: "Span of control", value: "6.8", delta: "—", dir: "flat", def: "Average direct reports per org node." },
  { metric: "Time-to-fill", value: "38d", delta: "−4d", dir: "up", def: "Req open → offer accept, median." },
];
export const DEI_BREAKDOWN = [
  { group: "US", n: 8200 }, { group: "DE", n: 2100 }, { group: "UK", n: 1450 },
  { group: "FR", n: 1050 }, { group: "SG", n: null }, { group: "BR", n: null }, // complementary suppression
];

/* ---------- Cases / help ---------- */
export const KB_SUGGESTIONS = [
  { q: "How much parental leave do I get?", a: "US workers: FMLA provides up to 12 weeks unpaid, job-protected leave.", cite: "us-fmla-handbook v3 · as of 2026-06-01" },
  { q: "When does my medical coverage start?", a: "Coverage begins the first of the month after completing 30 days of service.", cite: "benefits-handbook v2 · as of 2026-05-01" },
];
export interface HelpCase { id: string; topic: string; queue: string; sla: string; status: string; opened: string }
export const CASES: HelpCase[] = [
  { id: "HR-20451", topic: "payslip", queue: "payroll", sla: "due in 5h", status: "open", opened: "2026-06-11 08:12" },
  { id: "HR-20438", topic: "enrollment", queue: "benefits", sla: "due in 19h", status: "open", opened: "2026-06-10 16:40" },
];

/* ---------- Payroll hub (HR persona) ---------- */
export const PAY_CYCLES = [
  { country: "US", group: "US-SEMI", period: "2026-06B", state: "inputs-compiled", workers: 8200, anomalies: 14 },
  { country: "DE", group: "DE-MON", period: "2026-06", state: "transmitted", workers: 2100, anomalies: 3 },
  { country: "UK", group: "UK-MON", period: "2026-06", state: "results-reconciled", workers: 1450, anomalies: 0 },
];
export const VARIANCES = [
  { worker: "W-58213", element: "OT 1.5×", ps: 142.1, provider: 142.1, kind: null },
  { worker: "W-61077", element: "Net pay", ps: 2748.1, provider: 2746.2, kind: "data-difference" },
  { worker: "W-44520", element: "Pension", ps: 88.0, provider: 87.99, kind: "rounding" },
];

export const money = (n: number, c = "USD") =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: c }).format(n);
