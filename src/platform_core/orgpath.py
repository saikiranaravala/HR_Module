"""Org-path subtree matching with explicit '/' boundaries.

`startswith` alone is a trap: '/corp/eng' would match '/corp/engineering'.
Every subtree check normalizes both sides to a trailing slash first.
"""


def normalize(path: str) -> str:
    return path if path.endswith("/") else path + "/"


def within(path: str, subtree: str) -> bool:
    """True if `path` is `subtree` itself or anywhere under it."""
    return normalize(path).startswith(normalize(subtree))
