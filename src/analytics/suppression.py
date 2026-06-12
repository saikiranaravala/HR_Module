"""Small-population suppression (Specs/11 §5/§8).

n<5 cells are never rendered, and suppression is COMPLEMENTARY: if exactly one
cell in a breakdown is suppressed, the next-smallest cell is suppressed too,
so the hidden value cannot be recovered by subtracting visible cells from the
published total. The threshold is a privacy floor, deliberately not config.
"""
SUPPRESSION_THRESHOLD = 5

SUPPRESSED = None  # rendered as "—" upstream


def suppress(breakdown: dict[str, int]) -> dict[str, int | None]:
    """Apply n<5 + complementary suppression to a {group: count} breakdown."""
    result: dict[str, int | None] = {}
    below = [g for g, n in breakdown.items() if n < SUPPRESSION_THRESHOLD]
    for group, n in breakdown.items():
        result[group] = SUPPRESSED if group in below else n

    if len(below) == 1:
        # Residual-disclosure guard: hide the next-smallest visible cell too.
        visible = [(g, n) for g, n in breakdown.items() if g not in below]
        if visible:
            partner = min(visible, key=lambda item: item[1])[0]
            result[partner] = SUPPRESSED
    return result
