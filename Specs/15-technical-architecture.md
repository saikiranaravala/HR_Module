# Deep-Dive PRD 15 — Technical Architecture, Security & Privacy
*Project Meridian | Foundation for everything | Owners: platform engineering, security, privacy*

## 1. Mission & Success Metrics
A boring-by-design, audit-ready, regionally compliant platform that runs payroll-critical workloads at 99.99% and scales to 250K workers without re-architecture.
- Availability SLOs met 12/12 months; zero data-loss incidents (RPO ≤ 5 min proven in game days).
- Audit: SOC 2 Type II clean opinion cycle 1; SOX ITGC: zero significant deficiencies.
- Security: zero P1 findings open > 7 days; 100% of high-sensitivity reads logged.

## 2. Service & Deployment Architecture
Bounded-context services (per master TECH-2) on Kubernetes (EKS, multi-AZ; Azure AKS documented alternative), GitOps (ArgoCD), Terraform IaC with policy-as-code (OPA: tagging, encryption, residency guardrails enforced at plan time); service mesh (mTLS everywhere, traffic policy); progressive delivery (canary + automated rollback on SLO burn); environment set: dev/test/staging/prod per region plane + synthetic-data sandbox; image supply chain (signed images, SBOM, base-image patching SLAs).

## 3. Data Architecture
- **PostgreSQL per service** (Aurora PostgreSQL reference): partitioning strategy for temporal tables (assignment history range-partitioned by effective-year; 100M+ row readiness), connection pooling, read replicas for heavy read models.
- **Temporal-data platform service (TECH-4 expanded):** shared library + schema conventions implementing effective_date + sequence + correction semantics, as-of query helpers (`AS OF` views), retro-change event emission, and a conformance test suite every service must pass — the non-negotiable consistency layer; PeopleSoft veterans will recognize EFFDT/EFFSEQ done right.
- Kafka (MSK) event backbone (13-INT); Redis (sessions/cache with PII-free policy); OpenSearch (directory + global search with security-trimmed indexing); S3+Iceberg lakehouse (11-ANLT); WORM object-lock buckets (payslips, audit exports, board packs).
- Backup/DR: continuous PITR per database, cross-region replication for tier-1 stores, semi-annual full-region failover game day with published RTO results; backup restoration tested monthly (untested backups don't exist).

## 4. Identity, AuthZ & the Policy Engine (TECH-5 expanded)
- Workforce SSO (OIDC/SAML to corporate IdP) + step-up (WebAuthn/biometric) for sensitive actions catalog (bank change, comp view export, succession access).
- **Central policy service:** capabilities (verbs per domain) × data-scope attributes (org subtree from supervisory or security hierarchy, country, population, sensitivity tier) evaluated per request; policy as versioned config (12-PLAT lifecycle, dual-approval); decision logs sampled to audit store; the SAME policy decision point serves UI, APIs, analytics row/field security, AI tool scopes, and report builder — one implementation, verified by a cross-surface consistency test suite (the "can never see via report what UI denies" guarantee).
- Sensitivity tiers: T0 public-internal → T1 standard person → T2 comp/IDs/bank → T3 health-adjacent/ER cases/succession; field-level enforcement at API serialization layer; tier changes are security-reviewed config.
- Privileged access: JIT elevation with approval + session recording for production data access; break-glass procedure (dual-control, time-boxed, auto-revoked, post-incident review mandatory).

## 5. Audit & Records (TECH-6 expanded)
Append-only audit pipeline: every mutation event (actor incl. on-behalf-of and system/agent identity, before/after, source channel, correlation ID) + T2/T3 read events → hash-chained store on WORM storage; auditor workspace: scoped query UI, evidence-pack exports (control-mapped: SOX key controls catalog with automated evidence collection — access reviews, change approvals, segregation-of-duties conflict reports run continuously, not at audit time); litigation hold service: hold orders freeze deletion/retention jobs across services by worker/date-range with hold registry.

## 6. Privacy Engineering (TECH-9/10/11 expanded)
- Records-of-processing register generated from the data catalog (every field tagged: category, purpose, lawful basis, retention class) — documentation that can't drift from reality because it's derived from schemas.
- DSAR tooling: access-export assembler (cross-service, human-readable), rectification routing, erasure orchestration honoring statutory carve-outs per category (payroll: retain per country statute with basis recorded; the conflict matrix is product content, reviewed by counsel per country).
- Residency: EU data plane (full stack) at minimum; assessment workstream for IN DPDP and CN PIPL (CN likely separate deployment — master §13.3); global directory holds routing-minimal attributes; cross-border flows mapped with SCC/transfer-mechanism registry; analytics aggregation rules at plane boundaries (11-ANLT).
- Retention engine: schedules per record class per country; anonymization jobs (k-anonymity validated) vs. hard purge per class; certificates of destruction logged; legal-hold precedence.

## 7. Security Operations
Threat model maintained per service (STRIDE refresh each major release); SAST/DAST/dependency scanning in CI with severity SLAs; secrets in managed vault with rotation; pen test per release cycle + annual third-party + payroll-pipeline-focused red team annually; detection: audit stream → SIEM with HR-specific detections (mass comp views, off-hours bulk exports, bank-change velocity, succession-data scraping patterns); incident response runbooks incl. payroll-week severity escalation matrix (an incident at T-24h to transmit has its own command structure); vendor security: provider/carrier assessments, DPA registry, certificate/credential inventory (13-INT).

## 8. Performance & Capacity Engineering
Load model: 25K concurrent ESS at payday/OE peaks, payroll compile 50K < 10 min, OE elections burst 5K/min — codified as continuous load tests in staging with production-shaped synthetic data; capacity headroom policy 2× projected peak; cost engineering: unit-cost dashboards (per-worker-per-month infra cost), autoscaling policies, lakehouse storage tiering.

## 9. Edge Cases / Failure Drills Register
Region failover during open enrollment (game-day scenario); Kafka consumer-lag cascade during mass reorg; clock skew vs. effective-timestamp ordering (single time authority, monotonic checks); KMS key compromise rotation drill; audit store capacity surge under read-logging of OE traffic; partial-service brownout playbooks (ESS degrades gracefully; payroll pipeline never silently degrades — it halts loudly).

## 10. Open Questions
Primary region pair + EU plane locations (legal+latency study month 1). Aurora vs. self-managed Postgres for the largest temporal stores at 250K-scale (benchmark spike). FinOps target: confirm ≤ 35% TCO-reduction trajectory model with Finance.
