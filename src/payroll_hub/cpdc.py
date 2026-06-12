"""Canonical Payroll Data Contract (Specs/03 §2).

The CPDC is the only payroll language spoken upstream of adapters. Elements
come from the governed dictionary (per-country activation); provider code
mappings live inside each adapter, never here.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parent / "config"

CPDC_VERSION = "1.0.0"  # semver; additive minor changes only mid-year


@dataclass
class PayElement:
    element_code: str          # canonical dictionary code (never a provider code)
    kind: str                  # earning|deduction
    amount: Decimal
    units: float | None = None
    retro: bool = False
    original_period: str | None = None


@dataclass
class StateAllocation:
    state: str
    percent: Decimal


@dataclass
class CpdcRecord:
    worker_id: str
    legal_entity: str
    country: str
    pay_group: str
    period_key: str
    elements: list[PayElement] = field(default_factory=list)
    bank_last_changed_days_before_payday: int | None = None
    state_allocations: list[StateAllocation] = field(default_factory=list)
    payee_override: str | None = None      # deceased-worker beneficiary payee
    deceased: bool = False
    ytd_handover_from_entity: str | None = None  # mid-cycle entity transfer
    arrears_carried: Decimal = Decimal("0")

    def gross(self) -> Decimal:
        return sum((e.amount for e in self.elements if e.kind == "earning"), Decimal("0"))

    def deductions(self) -> Decimal:
        return sum((e.amount for e in self.elements if e.kind == "deduction"), Decimal("0"))


def load_element_dictionary(config_dir: Path = CONFIG_DIR) -> dict:
    return yaml.safe_load((config_dir / "elements.yaml").read_text(encoding="utf-8"))["elements"]


def element_active(dictionary: dict, element_code: str, country: str) -> bool:
    spec = dictionary.get(element_code)
    if spec is None:
        return False
    countries = spec.get("countries", ["*"])
    return "*" in countries or country in countries
