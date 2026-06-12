"""API consumer registry (Specs/13 §2).

Every system consumer is registered with a data-category contract (which
fields it may receive — the privacy review artifact), a tier ceiling (a token
can be comp-blind), and a pinned contract version. Compatibility is enforced
at serve time: a consumer never receives a payload version it hasn't accepted.
"""
from dataclasses import dataclass, field

from platform_core.catalog import TIER_ORDER, Tier
from platform_core.policy.engine import Decision, serialize_filtered


class ContractVersionError(RuntimeError):
    pass


@dataclass
class ConsumerContract:
    consumer_key: str
    pinned_version: int            # laggard consumers stay pinned (register row)
    approved_categories: set[str]  # data-category contract
    tier_ceiling: Tier = Tier.T1   # comp-blind by default


@dataclass
class ConsumerRegistry:
    _contracts: dict[str, ConsumerContract] = field(default_factory=dict)

    def register(self, contract: ConsumerContract) -> None:
        self._contracts[contract.consumer_key] = contract

    def get(self, consumer_key: str) -> ConsumerContract:
        if consumer_key not in self._contracts:
            raise KeyError(f"consumer '{consumer_key}' not registered")
        return self._contracts[consumer_key]


def serve_payload(
    registry: ConsumerRegistry,
    consumer_key: str,
    model: type,
    data: dict,
    payload_version: int,
) -> dict:
    """Filter a payload for a consumer: version compatibility, category
    contract, and tier ceiling all enforced here."""
    contract = registry.get(consumer_key)

    if payload_version > contract.pinned_version:
        raise ContractVersionError(
            f"{consumer_key} is pinned to v{contract.pinned_version}; "
            f"cannot serve v{payload_version} (compatibility window applies)"
        )

    decision = Decision(allow=True, clearance=contract.tier_ceiling)
    tier_filtered = serialize_filtered(model, data, decision)

    columns = model.__table__.columns
    category_filtered = {}
    for key, value in tier_filtered.items():
        if key in columns:
            tag = (columns[key].info or {}).get("catalog")
            if tag is not None and tag.category not in contract.approved_categories:
                continue
        category_filtered[key] = value
    return category_filtered
