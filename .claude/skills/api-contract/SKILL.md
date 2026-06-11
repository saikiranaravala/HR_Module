---
name: api-contract
description: Author OpenAPI 3.1 REST contracts and CloudEvents schemas following Meridian's API conventions (versioning, cursor pagination, idempotency, RFC7807, as-of queries). Use when defining or changing any service API or domain event.
---

# API & Event Contract Authoring

Contracts are designed before handlers are written, and live under `Contracts/<context>/` (`openapi.yaml` per service, `events/*.json` per event type).

## REST conventions (all mandatory)

- **OpenAPI 3.1**, one spec per bounded-context service. Path prefix `/v{n}` — breaking changes mean a new major version, never a mutated `/v1`.
- **Temporal reads:** every endpoint returning effective-dated entities accepts `as_of` (date, default today). Document it on every such operation.
- **Pagination:** cursor-based (`cursor` + `limit`), never offset. Response carries `next_cursor`.
- **Mutations:** require `Idempotency-Key` header; document replay semantics. Retro-effective mutations must state which retro event they emit.
- **Errors:** RFC 7807 `application/problem+json` with stable `type` URIs per error class.
- **Correlation:** `X-Correlation-Id` accepted and propagated; generated if absent.
- **Authorization is part of the contract:** for each operation, note the required capability and data scope, and the sensitivity tier of returned fields. The policy service decides — the contract documents what it will be asked.
- **GraphQL** (if the service exposes it): read-only, persisted queries only.

## Event conventions

- **CloudEvents 1.0 envelope**; `type` like `com.meridian.<context>.<entity>.<change>` (e.g., `com.meridian.core.employment.retro-corrected`).
- **PII-minimized payloads:** IDs + change type + effective date. Consumers pull detail through APIs under their own scopes. No names, no comp values, no national IDs in payloads.
- **Schema-registry validated;** minor changes must be backward-compatible (add optional fields only). Breaking change = new event type version.
- **Document idempotency:** every event states its dedupe key so consumers can be idempotent.

## Checklist before a contract is "done"

- [ ] Every operation traces to a requirement ID (cite it in the operation `description`).
- [ ] `as_of` present on all temporal reads; `Idempotency-Key` on all mutations.
- [ ] RFC7807 error catalog defined, including domain errors (e.g., sequence conflict on same-day change).
- [ ] Sensitivity tiers annotated; no T2/T3 field appears in list/search responses by default.
- [ ] Events PII-minimized and registered.
- [ ] Spec lints clean (e.g., `spectral lint` once tooling exists).
