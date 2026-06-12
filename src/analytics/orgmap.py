"""Org-bridge mapping (Specs/11 §8): reorgs break trend continuity unless
historical org paths are translated through bridge rows for like-for-like
comparison."""
from datetime import date

from platform_core.orgpath import normalize, within


def map_path(org_path: str, bridges: list, *, as_of: date) -> str:
    """Apply the longest-prefix bridge effective by `as_of`. One hop — chains
    are resolved by writing transitive bridges at reorg time, keeping reads
    trivial and auditable. Prefixes match on '/' boundaries only."""
    applicable = [b for b in bridges
                  if b.effective_date <= as_of and within(org_path, b.old_org_path)]
    if not applicable:
        return org_path
    best = max(applicable, key=lambda b: len(normalize(b.old_org_path)))
    old = normalize(best.old_org_path)
    return normalize(best.new_org_path) + normalize(org_path)[len(old):]
