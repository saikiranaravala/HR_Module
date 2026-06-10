# Deep-Dive PRD 12 — Workflow, Rules & Extensibility Platform
*Project Meridian | Used by: every module | The anti-PeopleCode strategy*

## 1. Mission & Success Metrics
All organizational logic lives in governed, versioned, testable configuration — so the system adapts for 20 years without code forks.
- Custom code forks: 0 (hard guardrail). Config-only adaptation rate: 100% of approved change requests.
- Config change lead time: routine workflow/rule change idea→prod ≤ 5 business days with full test evidence.
- Workflow engine: 99.99% availability (it gates payroll approvals); P95 step-evaluation < 200 ms.

## 2. Workflow Engine & Designer
- Model: BPMN-inspired but constrained (linear/parallel/conditional steps; no arbitrary code nodes). Step types: approval (single/quorum/any), task (checklist assignment), notification, service call (typed catalog of internal actions only), wait/timer, condition branch.
- Routing primitives: n-levels-up supervisory, position-based, role-in-scope (e.g., "HRBP for worker's department"), amount-threshold laddering, country-conditional branches, pooled queues with claim.
- Runtime guarantees: durable state, exactly-once step execution, SLA timers with escalation chains, delegation/OOO resolution at evaluation time, self-approval prevention (initiator ≠ approver enforced at engine level), audit of every evaluation (which rule resolved to which approver and why — the "explain routing" view).
- Designer: visual builder with versioning (semantic diff of two flow versions), simulation mode (run candidate flow against historical transaction set: "would have routed differently for 1,243 of last quarter's transactions" report), promotion pipeline dev→test→prod with approvals, deprecation handling for in-flight instances (finish-on-old vs. migrate policies).

## 3. Business Rules Engine
- Shared service consumed by TIME calcs, BEN eligibility, PAY validation, notification triggers, comp guidelines.
- Authoring: decision tables (primary — auditable, business-readable) + expression language (sandboxed, no I/O, total-function: guaranteed termination, deterministic) for complex math; rule sets versioned + effective-dated; dependency graph (which rules feed which) with impact analysis on change.
- Testing: unit tests stored with rules, coverage reporting, golden-dataset regression suites per domain (the TIME simulator and BEN eligibility re-eval build on this), CI gate: no promotion < 100% pass.
- Performance: rule-set compilation + caching; bulk evaluation APIs (50K-worker eligibility sweep ≤ 30 min from 04-BEN).

## 4. Configuration Lifecycle Management
All config (workflows, rules, plans, templates, notification defs, security policies) = exportable artifacts (declarative, diffable). Environment manager: compare any two environments, promote change sets with review/approval (SOX-relevant categories flagged: payroll mappings, comp guidelines, security policy — dual-approval + change-ticket linkage mandatory), rollback to prior version, config freeze windows (payroll cut-off periods auto-freeze PAY-touching config). Audit: every config change = who/what/diff/ticket, immutably logged.

## 5. Document Generation & E-Signature
Template studio: rich templates with merge fields from any entity (schema-aware picker), per-country/language variants with fallback, conditional blocks; generation API (sync single + batch); e-sign integration (DocuSign/Adobe adapter; native simple-signature for low-stakes acknowledgments); auto-filing to worker document record with doc-type retention class; statutory letter packs per country (employment verification, promotion letters, contractual change notices with works-council-sensitive content flags).

## 6. Notification Framework
Event-subscription model: notification definitions bind domain events → templates → channel strategy (email/push/SMS/Teams/Slack adapters) with per-user preference resolution, locale resolution, digest batching, quiet hours, mandatory-override class (legal/safety), delivery tracking + bounce handling, rate protection (mass-transaction event storms → digest collapse). Template versioning + preview-with-real-data (masked) testing.

## 7. Extensibility Boundaries (what we deliberately allow)
Custom fields: governed registry (typed, validated, security-tiered, analytics-propagated automatically) with proliferation guardrails (approval + annual review of usage). Custom objects (P2): lightweight related-entity builder (e.g., company-car registry) with workflow/report support — bounded: no payroll-path participation. Webhooks + API extensions per 13-INT. Explicit non-feature: no server-side scripting hooks. Pressure to add them is the PeopleCode slippery slope — escalate to architecture board instead.

## 8. Edge Cases Register
Approver chain exhaustion (top-of-tree transactions → designated fallback role); circular delegation; workflow version migration with steps already completed; rule effective-dating vs. transaction effective-dating interplay (rule version selected by transaction effective date, documented + tested); decision-table overlap/gap detection at save time.

## 9. Open Questions
Expression-language choice (FEEL/DMN-aligned vs. CEL) — architecture spike month 1. Config-as-code repo integration for IT-managed categories (recommend yes: Git-backed with UI front end).
