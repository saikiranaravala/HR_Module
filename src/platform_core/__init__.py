"""platform_core — Meridian platform foundation (Specs/15).

Shared infrastructure every bounded context builds on:
- temporal: effective-dated data pattern + as-of queries (TECH-4)
- policy: single policy decision point, tiers T0-T3 (TECH-5)
- audit: append-only hash-chained audit pipeline (TECH-6)
- catalog: privacy-by-construction field tags (TECH-9/10)
"""
