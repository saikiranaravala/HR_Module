# Training 10 — Security & Compliance Officer

**Audience:** InfoSec, privacy officers, internal audit, and anyone assembling evidence for regulators or works councils. **Duration:** 2 days. **Prerequisites:** security/privacy background; Training 01 for orientation.

## Learning Objectives

Operate the sensitivity-tier model and central policy engine; verify the audit chain and read-logging; use the privacy catalog and records-of-processing; validate cross-surface access consistency; audit the AI governance controls; know the encryption and data-handling posture and its current local limits.

---

## Day 1 — Access, Audit & Privacy Architecture

### 1.1 Sensitivity tiers (the vocabulary everything else uses)

| Tier | Data | Extra control |
|---|---|---|
| T0 | Internal-public (org chart, job catalog) | — |
| T1 | Person-standard (name, contact, employment basics) | Scoped access |
| T2 | Comp, national IDs, banking | **Every read audit-logged**; field-level envelope encryption for identifiers |
| T3 | Health-adjacent, ER cases, succession | Read-logged + role-segregated (e.g., `er-investigator`, `exec-talent`; incumbent self-block on succession slates) |

### 1.2 One policy decision point (Invariant #3)

All authorization — UI, API, reports, analytics, AI tool scopes — calls the same `PolicyEngine.decide(subject, capability, resource)`:

- **Policy is versioned YAML config** (`src/platform_core/config/policy/roles.yaml`) — capabilities, roles, tier clearances, org/country scoping. Access changes are config releases with review, not code.
- **Fail-closed:** any evaluation error yields DENY. A policy outage looks like mass denial, never accidental exposure.
- **Decision log:** decisions are recorded (`policy_decision_log`) with policy version — you can answer "under what rule was this allowed on date X?"
- **ABAC scoping:** org-subtree checks use boundary-safe path matching; population/country attributes ride on the resource.

**Audit exercise 1.2** — Pick three demo capabilities and trace each: role definition in YAML → decision → log entry → (for T2) the read-audit event.

### 1.3 The hash-chained audit log

Every audit event carries a hash chained to its predecessor (UTC-canonicalized timestamps), making the log **tamper-evident**: any insertion, deletion, or edit breaks every subsequent hash. Verify anytime: `GET /v1/audit/verify` → `{"intact": true, "firstBrokenSeq": null}`. The table is DB-immutable (trigger-enforced) and deliberately excluded from data resets. A broken chain is a sev-1 with a preserve-and-escalate playbook (Training 07 §2.2).

### 1.4 Privacy by construction (Invariant #8)

- **Catalog tags at schema time:** every column carries category, purpose, lawful basis, retention class, and tier in the model definition — untagged PII cannot ship.
- **Records of processing are generated, not maintained:** `GET /v1/catalog/records-of-processing` emits the register from the live catalog — it cannot drift from the schema.
- **Retention classes** drive clocks (candidate retention, alumni retention, succession active+2y…) with real calendar-month arithmetic.
- **Erasure:** domain workflows (e.g., recruiting GDPR erasure) are scoped, logged, retention-aware; the demo includes an erased candidate to inspect.
- **Encryption:** national IDs and bank details use field-level envelope encryption. **Local limit to disclose honestly:** the local build runs a local-KEK stub (TECH-7 partial); production targets managed KMS with rotation drills — documented N/A-local, not dropped.
- **No production data below prod, ever** — demo/test data is synthetic (reserved SSN ranges, placeholder ciphertexts).

## Day 2 — Consistency, AI Governance & Evidence Packs

### 2.1 Cross-surface consistency (the control that kills side doors)

Anything denied in the UI must be denied identically via API, reports, analytics, and AI — enforced by the **policy consistency suite** (same decision point + tests comparing surfaces, e.g., API vs in-process in `test_policy.py`). Your assurance work: for each new module, confirm the suite covers its surfaces; spot-check quarterly with a low-privilege test subject across all four surfaces.

### 2.2 Analytics privacy

Small-cell suppression at n<5 with **complementary suppression** (a second cell hidden to prevent reconstruction by subtraction — `test_ANLT_complementary_suppression_no_subtraction` proves it). Admin roles do not bypass. Certified snapshots are immutable with restatement-by-version — your "what did the board see" evidence.

### 2.3 AI governance (Invariant #6) — the works-council pack

| Control | Mechanism | Evidence |
|---|---|---|
| No shadow AI | Unregistered use case → refused before any model call | `use_cases.yaml` + refusal entries in the AI ledger |
| User-scope inheritance | Agents call policy as the *calling user*; no privileged service accounts | Policy decision log entries per AI call |
| Complete ledger | Every call including refusals logged (use case, prompt version, budget state) | `ai.ai_ledger` |
| Never rates / never rejects | No code path: performance AI has no rating surface; recruiting `reject()` refuses AI actors | Named tests in modules 06/07 |
| Population-scoped retrieval | Copilot answers scoped to worker's country/union/grade | Retrieval config + ledger sources |
| Human commitment | Drafts require edit-before-submit; money/status/access changes require human commit | Workflow definitions |
| PII guard & injection heuristics | Gateway blocks third-party personal data in prompts; flags hostile embedded content | Gateway config + ledger flags |
| Prompt governance | Prompts in the versioned registry (`prompts.yaml`), never inline | Registry diff history |

### 2.4 Standing evidence packs (assemble once, refresh quarterly)

1. **Access-control pack:** roles.yaml version history + consistency-suite results + T2/T3 read-log samples.
2. **Integrity pack:** audit-verify output + immutability trigger inventory (20 triggers) + certified-snapshot restatement example.
3. **Privacy pack:** generated records-of-processing + retention class catalog + erasure walkthrough + synthetic-data attestation.
4. **AI pack:** the table above with artifacts.
5. **Known-gaps register:** local-KEK stub, deferred event layer, residency rulings pending (IN/CN — an open program gate) — honesty here is what makes the rest credible.

---

## Competency Checklist (sign-off)

- [ ] Classifies 10 sample fields into tiers and names each tier's extra controls
- [ ] Traces a capability from YAML to decision log to read-audit event
- [ ] Runs audit-chain verification and states the broken-chain response
- [ ] Generates records-of-processing and explains why it can't drift
- [ ] Demonstrates cross-surface consistency with a test subject
- [ ] Presents the AI governance pack to a skeptical audience (role-play)
- [ ] Maintains the known-gaps register accurately
