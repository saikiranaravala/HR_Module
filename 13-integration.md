# Deep-Dive PRD 13 — Integration Architecture
*Project Meridian | Platform capability | Consumers: IdP, ERP, carriers, providers, partners, internal services*

## 1. Mission & Success Metrics
Every system that needs workforce data gets it through governed, observable, replayable contracts — and Meridian never becomes the bottleneck or the mystery.
- Interface incident MTTR < 30 min (tracing + replay tooling); silent failures: 0 (every interface heartbeat-monitored).
- Partner onboarding: new API consumer self-serves sandbox→prod ≤ 10 days.
- Joiner-mover-leaver identity SLA: leaver deprovision ≤ 15 min from effective time, 100% of cases.

## 2. API Platform
- REST (OpenAPI 3.1, versioned /v{n}, 18-month deprecation policy with consumer-usage telemetry before sunset) + GraphQL (read-optimized composite queries for UI/partner dashboards; persisted queries only in prod — no arbitrary query cost exposure).
- Conventions: cursor pagination, sparse fieldsets, effective-date params (`as_of`, `from/to` history ranges) on temporal entities, idempotency keys on all mutations, RFC7807 problem details, correlation-ID propagation.
- AuthZ: OAuth2.1 client-credentials for system consumers, OIDC for user-context; scopes mirror TECH-5 capabilities + data tiers (a token can be comp-blind); consumer registry with data-category contracts (each consumer's approved fields documented — privacy review artifact) and per-consumer rate tiers.
- Sandbox: synthetic 5K-worker dataset (statistically realistic, zero real PII) refreshed weekly; contract tests published (Pact-style) so consumers validate against schema changes pre-release.

## 3. Event Backbone
Kafka; CloudEvents envelope; schema registry (Avro/JSON-schema, compatibility-enforced: backward for minor); topic taxonomy per domain; ordering per worker key; retention 30 days hot + archived stream to lakehouse (infinite replay via rehydration); consumer groups registered with ownership metadata; PII-minimization pattern: events carry IDs + change-type, consumers pull details via API under their own scopes (no broad PII fan-out); replay service: targeted re-emission by worker/time-range for consumer recovery with replay-audit.

## 4. Identity & Access Integration (JML)
Meridian = authoritative source for workforce identity lifecycle. SCIM 2.0 outbound to Entra ID/Okta: create on hire (timed: account pre-staged T-3 days, enabled at start), attribute sync (name, dept, manager, location → directory/email/groups), mover updates (manager/dept changes drive group + mailbox policy), leaver: disable ≤ 15 min from termination effective timestamp (event-driven, monitored, with manual break-glass), rehire account-reconciliation rules. Contingent workers: sponsored-identity flow with end-date auto-expiry. Inbound SSO: SAML/OIDC for all surfaces; SCIM inbound NOT supported (single source of truth discipline).

## 5. ERP / Finance Integration Suite
GL journals (from 03-PAY: file or API per ERP, posting acknowledgment loop, error-repair queue); cost-center master inbound (near-real-time, validation: cannot inactivate CC with active funding splits — exception workflow); project master inbound for 02-TIME charging; headcount/position budget reconciliation (Finance plan vs. Meridian positions — variance report API); bonus/comp accrual estimates outbound (05); AP integration for tuition/benefits vendor payments where applicable.

## 6. Connector Catalog (adapter framework)
Shared adapter chassis (from 03-PAY pattern): transform + transport (API/SFTP-PGP/AS2) + ack handling + error normalization + per-connector dashboard. Launch catalog: payroll providers (per RFP), benefits carriers/EDI-834, retirement providers, background check, e-signature, assessments, LMS content, equity platforms, ITSM (onboarding tickets), badging/facilities, occupational health, works-council data interfaces, The Work Number-style verification, tax-credit screening (WOTC) optional. Each connector: runbook, SLA, contact escalation, certificate/credential rotation schedule in a managed inventory (expiry alerts — file-cert lapses are a classic silent killer).

## 7. Observability & Operations
End-to-end tracing (OpenTelemetry; correlation from UI action → API → event → adapter → external ack); interface health board (per-connector traffic, error rate, latency, last-success heartbeat with expected-cadence alerting — "the Tuesday carrier file didn't run" pages someone); message-level search (find this worker in last night's 834); replay/repair console with four-eyes on data-modifying replays; integration environment strategy (partner test endpoints mapped per connector; synthetic-data-only below prod).

## 8. Edge Cases Register
Event consumers down during mass reorg storm (backpressure + digest events for bulk operations); ERP cost center retro-inactivation with historical postings; IdP outage during termination window (queued with alert, manual runbook); duplicate-delivery tolerance (all consumers idempotent — contract requirement); schema evolution with laggard consumers (compatibility window + consumer-pinned versions); cross-region event routing under residency constraints (regional topics + filtered global aggregates).

## 9. Open Questions
iPaaS layer (MuleSoft/Boomi) vs. native adapter chassis only — recommend native chassis for core flows, iPaaS optional for long-tail internal consumers; decide month 2. AS2/EDI VAN selection for carrier connectivity.
