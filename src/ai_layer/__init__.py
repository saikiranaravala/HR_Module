"""ai_layer — governed AI platform (Specs/14): gateway, retrieval, agents.

Invariant #6: all model calls route through the gateway; agents inherit the
calling user's scope; humans commit anything touching money, employment
status, or access; retrieval is population-scoped.
"""
