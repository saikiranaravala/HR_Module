# Module 3 Design — Integration Architecture (Specs/13, shrunk)

**Spec:** [Specs/13-integration.md](../Specs/13-integration.md) · **Package:** `src/integration_hub/` · Tests: `src/test/integration_hub/`
**Scope note:** the event backbone (§3) is deferred with Invariant #7 (memory.md). This module builds what doesn't depend on Kafka: the adapter chassis, the consumer registry, and the JML identity lifecycle with a queued/mock transport.

## 1. Scope & Requirement Trace

| Spec section | Design element | Local scope |
|---|---|---|
| §6 Connector catalog / adapter chassis | `chassis.py` — Connector base (transform → transport → ack → error normalization), run log with last-success heartbeat, credential inventory with expiry alerting | **Yes** |
| §4 JML identity (SCIM outbound) | `jml.py` — hire pre-stage (T-3 days), mover sync, leaver disable; idempotent processing; outage queueing with alert | **Yes** (mock SCIM client; real Entra/Okta later) |
| §2 API platform consumer registry | `consumers.py` — consumer records with data-category contracts, pinned contract versions, tier ceilings ("comp-blind token") | **Yes** |
| §3 Event backbone, §5 ERP suite, §7 observability stack | Deferred (events / cloud) | No |

## 2. Key decisions

- **Chassis is the 03-PAY pattern**: payroll adapters in Module 03 will subclass `Connector`. Transform and transport are separate hooks; every run writes a `connector_run` row (status, error_normalized, duration) — the heartbeat data the health board needs.
- **Credential inventory**: each connector registers credentials with expiry dates; `expiring_credentials(within_days)` is the alert feed (file-cert lapse = classic silent killer, §6).
- **JML**: pure function from worker lifecycle facts → provisioning actions, executed through a SCIM-shaped client interface. Failures don't drop actions — they queue with an alert flag (IdP outage register row). All actions idempotent (duplicate-delivery register row): action identity = (worker, action_type, effective_ts).
- **Consumer registry**: consumers pin a contract version; compatibility check refuses serving a payload version the consumer hasn't accepted (laggard-consumer register row). Tier ceiling enforced via the platform policy filter.

## 3. Edge-Case Test Plan

| Register row | Test |
|---|---|
| Duplicate-delivery tolerance (idempotent consumers) | `test_INT_duplicate_delivery_idempotent` |
| IdP outage during termination window | `test_INT_idp_outage_termination_queued_with_alert` |
| Schema evolution with laggard consumers | `test_INT_laggard_consumer_pinned_version` |
| Credential/cert expiry (silent killer) | `test_INT_credential_expiry_alerting` |
| Mass reorg storm backpressure; cross-region topics | Deferred (needs event backbone) |

## Change Log

- **2026-06-10** — Initial design + implementation. Trigger: Module 3 kickoff (auto-approved cadence).
