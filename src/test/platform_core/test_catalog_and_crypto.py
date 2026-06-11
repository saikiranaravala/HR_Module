"""Catalog (TECH-9/10) and crypto stub (TECH-7) tests."""
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import (
    missing_tags,
    records_of_processing,
    validate_registry,
)
from platform_core.crypto import decrypt_field, encrypt_field


def test_registry_fully_tagged():
    """Privacy by construction: every column on every registered model is tagged."""
    assert validate_registry() == {}


def test_untagged_column_is_caught():
    class Untagged(Base):
        __tablename__ = "untagged_example"
        id: Mapped[str] = mapped_column(Text, primary_key=True)  # no catalog tag

    assert missing_tags(Untagged) == ["id"]
    Base.metadata.remove(Untagged.__table__)  # keep metadata clean for other tests


def test_records_of_processing_derived_from_schemas():
    register = records_of_processing()
    tables = {row["table"] for row in register}
    assert "platform.audit_event" in tables
    assert "worker_profile" in tables
    sample = next(row for row in register if row["column"] == "base_salary")
    assert sample["tier"] == "T2"
    assert sample["lawful_basis"] == "contract"


def test_envelope_encryption_roundtrip():
    secret = "DE89 3704 0044 0532 0130 00"  # synthetic IBAN-shaped string
    token = encrypt_field(secret)
    assert secret not in token
    assert decrypt_field(token) == secret


def test_envelope_tokens_are_unique_per_call():
    token_a = encrypt_field("same-value")
    token_b = encrypt_field("same-value")
    assert token_a != token_b  # fresh DEK + nonce every call
