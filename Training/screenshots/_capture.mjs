/* Regenerates every screenshot in Training/screenshots/ from the live demo UI.
   Prereqs (run from UI/):
     npm install --no-save playwright && npx playwright install chromium
     npm run dev          (keep running on :5173)
     node ..\Training\screenshots\_capture.mjs
   Note: navigation after a persona switch MUST use left-nav clicks —
   page.goto() reloads the app and resets the persona to employee. */
import { chromium } from "playwright";
import { mkdirSync } from "fs";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";

const BASE = "http://localhost:5173";
const OUT = dirname(fileURLToPath(import.meta.url));
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

async function shot(name, fullPage = true) {
  await page.waitForTimeout(350);
  await page.screenshot({ path: resolve(OUT, `${name}.png`), fullPage });
  console.log(`  ${name}.png`);
}
async function go(path) { await page.goto(BASE + path); await page.waitForTimeout(400); }
async function nav(label) {
  await page.locator(".nav a.nav-item", { hasText: label }).click();
  await page.waitForTimeout(400);
}
async function persona(p) {
  await go("/");
  await page.selectOption(".gh-home-sel", p);
  await page.waitForTimeout(500);
}

/* ============ EMPLOYEE — Avery Quinn (default persona; goto is safe) ============ */
console.log("EMPLOYEE scenarios");
await persona("employee");
await shot("emp-01-1-home");
await page.keyboard.press("Control+KeyK");
await page.waitForTimeout(300);
await page.keyboard.type("pay");
await shot("emp-01-2-palette", false);
await page.keyboard.press("Escape");

await go("/pay");
await shot("emp-02-1-payslips");
await page.getByRole("button", { name: /Explain my payslip change/ }).click();
await shot("emp-02-2-explain");
await page.getByText("Overtime 1.5×").click();
await shot("emp-02-3-line-note");

await go("/time");
await shot("emp-03-1-time");
await page.getByRole("button", { name: "Request time off" }).click();
await page.waitForTimeout(300);
await shot("emp-03-2-request-modal", false);
await page.getByRole("button", { name: "Submit request" }).click();
await shot("emp-03-3-submitted");

await go("/benefits");
await shot("emp-04-1-benefits");

await go("/profile");
await shot("emp-05-1-profile");
await page.locator('input[aria-label="As-of date"]').fill("2023-01-01");
await shot("emp-05-2-asof-2023");
await page.locator('input[aria-label="As-of date"]').fill("2026-07-02");
await shot("emp-05-3-asof-future");
await page.getByRole("button", { name: "Direct deposit" }).click();
await shot("emp-05-4-bank-interlock");

await go("/directory?q=Jordan");
await shot("emp-06-1-directory");
await go("/performance");
await shot("emp-07-1-performance");
await go("/learning");
await shot("emp-08-1-learning");

await go("/help");
await shot("emp-09-1-help");
await page.locator(".btnrow .btn.sm").first().click();
await shot("emp-09-2-answer");
await page.getByRole("button", { name: "I still need help" }).click();
await shot("emp-09-3-escalate");
await page.getByRole("button", { name: "Create case with transcript" }).click();
await shot("emp-09-4-case-created");

/* ============ MANAGER — Morgan Lee (nav-click navigation only) ============ */
console.log("MANAGER scenarios");
await persona("manager");
await shot("mgr-01-1-home");

await nav("Approvals");
await shot("mgr-02-1-inbox");
const checkAll = async () => {
  const boxes = page.locator('input[type="checkbox"]');
  const n = await boxes.count();
  for (let i = 0; i < n; i++) await boxes.nth(i).check();
};
await checkAll();
await shot("mgr-02-2-all-selected");
await page.getByRole("button", { name: /Bulk approve/ }).click(); // refused: comp included; selection clears
await shot("mgr-02-3-bulk-refused");
await checkAll();
await page.locator("tr", { hasText: "Merit +9%" }).locator('input[type="checkbox"]').uncheck();
await page.getByRole("button", { name: /Bulk approve/ }).click();
await shot("mgr-02-4-bulk-done");
await page.locator("tr", { hasText: "Merit +9%" }).getByRole("button", { name: "Approve" }).click();
await shot("mgr-02-5-comp-approved");

await nav("My Team");
await shot("mgr-03-1-team");
await page.getByRole("button", { name: "Nudge" }).first().click();
await shot("mgr-03-2-nudge");

await nav("Comp Cycle");
await shot("mgr-04-1-worksheet");
await page.getByRole("button", { name: "Recommend" }).first().click();
await page.waitForTimeout(300);
await shot("mgr-04-2-recommend-modal", false);
await page.locator("#mp").fill("12");
await page.waitForTimeout(200);
await shot("mgr-04-3-out-of-guideline", false);
await page.locator("#jt").fill("Retention risk — competing offer; critical platform knowledge.");
await page.getByRole("button", { name: "Save" }).click();
await shot("mgr-04-4-saved");
await page.getByRole("button", { name: "Recommend" }).first().click();
await page.locator("#mp").fill("4");
await page.getByRole("button", { name: "Save" }).click();
await shot("mgr-04-5-budget-live");

await nav("Recruiting");
await shot("mgr-05-1-pipeline");
await page.getByRole("button", { name: "Advance ▸" }).first().click();
await shot("mgr-05-2-advanced");
await page.getByRole("button", { name: "Reject…" }).first().click();
await shot("mgr-05-3-reject-guard");

/* ============ HR ADMIN — Sam Rivera ============ */
console.log("HR ADMIN scenarios");
await persona("hr");
await shot("hr-01-1-home");

await nav("Payroll Hub");
await shot("hr-02-1-cycles");
await page.getByRole("button", { name: "Explain" }).first().click();
await shot("hr-02-2-anomaly-explain");
await page.locator("button:not([disabled])", { hasText: "Approve" }).first().click();
await shot("hr-02-3-cycle-approved");

await nav("Succession");
await shot("hr-03-1-succession");
await page.getByRole("button", { name: "View slate" }).first().click();
await shot("hr-03-2-t3-read-logged");
await page.locator(".ninebox .chip").first().click();
await shot("hr-03-3-ninebox-rationale");

await nav("Workforce Analytics");
await shot("hr-04-1-analytics");
await page.locator(".kpi").first().click();
await shot("hr-04-2-metric-definition");

await browser.close();
console.log("Done");
