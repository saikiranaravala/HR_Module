"""Data catalog — privacy by construction (TECH-9/10, Invariant #8).

Every column on a registered model must carry a FieldTag (category, purpose,
lawful basis, retention class, sensitivity tier, residency class). The
records-of-processing register is generated from these tags, so documentation
cannot drift from the schemas it describes.
"""
from dataclasses import dataclass
from enum import Enum


class Tier(str, Enum):
    T0 = "T0"  # public-internal
    T1 = "T1"  # standard person data
    T2 = "T2"  # comp / national IDs / banking
    T3 = "T3"  # health-adjacent / ER cases / succession


TIER_ORDER = {Tier.T0: 0, Tier.T1: 1, Tier.T2: 2, Tier.T3: 3}


@dataclass(frozen=True)
class FieldTag:
    category: str
    purpose: str
    lawful_basis: str
    retention_class: str
    tier: Tier = Tier.T1
    residency_class: str = "global"


def tag(**kwargs) -> dict:
    """Build a SQLAlchemy column ``info`` dict carrying a catalog tag."""
    return {"catalog": FieldTag(**kwargs)}


# Standard tags for the bookkeeping columns every table carries.
RECORD_KEEPING_TAG = tag(
    category="record-keeping",
    purpose="audit-and-integrity",
    lawful_basis="legal-obligation",
    retention_class="audit-7y",
    tier=Tier.T0,
)

_registered_models: list[type] = []


def register_model(model: type) -> type:
    """Class decorator: enrolls a model in catalog validation and the RoP register."""
    if model not in _registered_models:
        _registered_models.append(model)
    return model


def registered_models() -> list[type]:
    return list(_registered_models)


def missing_tags(model: type) -> list[str]:
    return [
        column.name
        for column in model.__table__.columns
        if "catalog" not in (column.info or {})
    ]


def validate_registry() -> dict[str, list[str]]:
    """Return {model name: [untagged columns]} — empty dict means compliant."""
    problems = {}
    for model in _registered_models:
        missing = missing_tags(model)
        if missing:
            problems[model.__name__] = missing
    return problems


def field_tier(model: type, field_name: str) -> Tier:
    column = model.__table__.columns[field_name]
    field_tag: FieldTag = column.info["catalog"]
    return field_tag.tier


def max_model_tier(model: type) -> Tier:
    tiers = [
        column.info["catalog"].tier
        for column in model.__table__.columns
        if "catalog" in (column.info or {})
    ]
    return max(tiers, key=lambda t: TIER_ORDER[t]) if tiers else Tier.T1


def records_of_processing() -> list[dict]:
    """TECH-9: register derived from live schemas, one row per tagged column."""
    rows = []
    for model in _registered_models:
        for column in model.__table__.columns:
            field_tag = (column.info or {}).get("catalog")
            if field_tag is None:
                continue
            rows.append(
                {
                    "table": model.__table__.fullname,
                    "column": column.name,
                    "category": field_tag.category,
                    "purpose": field_tag.purpose,
                    "lawful_basis": field_tag.lawful_basis,
                    "retention_class": field_tag.retention_class,
                    "tier": field_tag.tier.value,
                    "residency_class": field_tag.residency_class,
                }
            )
    return rows
