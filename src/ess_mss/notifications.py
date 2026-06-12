"""Notification framework usage (ESS-3, Specs/10 §6).

Catalog config defines per-type channel defaults and mandatory flags; user
overrides, quiet hours, and digest mode apply on top — except mandatory types
(legal notices, bank-change alerts), which ignore preferences. Frontline
personal channels (SMS / personal email) require recorded consent.
"""
from dataclasses import dataclass
from pathlib import Path

import yaml

from ess_mss.models import NotificationPref

CONFIG_PATH = Path(__file__).resolve().parent / "config" / "notifications.yaml"

PERSONAL_CHANNELS = {"sms", "personal-email"}


@dataclass
class Resolution:
    channels: list[str]
    deferred_to_digest: bool = False
    dropped_for_consent: list[str] | None = None


def load_catalog(path: Path = CONFIG_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["notification_types"]


def resolve(
    catalog: dict, notif_type: str, *, pref: NotificationPref | None = None,
    local_hour: int | None = None,
) -> Resolution:
    spec = catalog[notif_type]
    mandatory = spec.get("mandatory", False)
    channels = list(spec["default_channels"])

    if not mandatory and pref is not None and pref.channels:
        channels = list(pref.channels)

    # Frontline personal channels need consent — even for mandatory types,
    # consentless personal channels are dropped (corporate channels remain).
    dropped = []
    if pref is None or not pref.personal_channel_consent:
        dropped = [c for c in channels if c in PERSONAL_CHANNELS]
        channels = [c for c in channels if c not in PERSONAL_CHANNELS]

    # Quiet hours defer non-mandatory notifications to the digest.
    if (not mandatory and pref is not None and local_hour is not None
            and pref.quiet_start is not None and pref.quiet_end is not None
            and _in_quiet_hours(local_hour, pref.quiet_start, pref.quiet_end)):
        return Resolution(channels=[], deferred_to_digest=True,
                          dropped_for_consent=dropped or None)

    return Resolution(channels=channels, dropped_for_consent=dropped or None)


def _in_quiet_hours(hour: int, start: int, end: int) -> bool:
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end  # crosses midnight
