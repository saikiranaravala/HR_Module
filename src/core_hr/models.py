"""Core HR data model (Specs/01 §2). Schema: core.

Person is the stable human identity; PersonName and Assignment are temporal
series (the EFFDT/EFFSEQ pattern). Worker = one employment relationship
(person × legal entity) — CORE-3 multi-job means N workers per person.
"""
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Integer, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from platform_core.base import Base
from platform_core.catalog import RECORD_KEEPING_TAG, Tier, register_model, tag
from platform_core.temporal import TemporalMixin

_PERSON_TAG = tag(category="personal", purpose="employment-admin",
                  lawful_basis="contract", retention_class="emp+7y", tier=Tier.T1)
_ORG_TAG = tag(category="organization", purpose="employment-admin",
               lawful_basis="legitimate-interest", retention_class="org-10y", tier=Tier.T0)
_EMPLOYMENT_TAG = tag(category="employment", purpose="employment-admin",
                      lawful_basis="contract", retention_class="emp+7y", tier=Tier.T1)


@register_model
class Person(Base):
    __tablename__ = "person"
    __table_args__ = {"schema": "core"}

    person_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    date_of_birth: Mapped[date] = mapped_column(
        Date, info=tag(category="personal", purpose="employment-admin",
                       lawful_basis="contract", retention_class="emp+7y", tier=Tier.T1))
    primary_nationality: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_PERSON_TAG))


@register_model
class PersonName(TemporalMixin, Base):
    """Effective-dated legal names (name changes are history, never overwrites)."""
    __tablename__ = "person_name"
    __table_args__ = {"schema": "core"}
    __temporal_identity__ = "person_id"

    person_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, info=dict(RECORD_KEEPING_TAG))
    given_name: Mapped[str] = mapped_column(Text, info=dict(_PERSON_TAG))
    family_name: Mapped[str] = mapped_column(Text, info=dict(_PERSON_TAG))
    formatted_name: Mapped[str] = mapped_column(Text, info=dict(_PERSON_TAG))
    legal_doc_verified: Mapped[bool] = mapped_column(Boolean, default=False, info=dict(_PERSON_TAG))


@register_model
class NationalId(Base):
    __tablename__ = "national_id"
    __table_args__ = {"schema": "core"}

    national_id_pk: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    person_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(RECORD_KEEPING_TAG))
    id_type: Mapped[str] = mapped_column(Text, info=tag(
        category="national-id", purpose="statutory-reporting",
        lawful_basis="legal-obligation", retention_class="emp+7y", tier=Tier.T1))
    value_encrypted: Mapped[str] = mapped_column(Text, info=tag(
        category="national-id", purpose="statutory-reporting",
        lawful_basis="legal-obligation", retention_class="emp+7y", tier=Tier.T2))
    last_four: Mapped[str] = mapped_column(Text, info=tag(
        category="national-id", purpose="masked-display",
        lawful_basis="legal-obligation", retention_class="emp+7y", tier=Tier.T1))


@register_model
class WorkEligibility(Base):
    __tablename__ = "work_eligibility"
    __table_args__ = {"schema": "core"}

    eligibility_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    person_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(RECORD_KEEPING_TAG))
    country: Mapped[str] = mapped_column(Text, info=dict(_PERSON_TAG))
    document_type: Mapped[str] = mapped_column(Text, info=dict(_PERSON_TAG))  # citizen|visa|work-permit
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, info=dict(_PERSON_TAG))


@register_model
class Worker(Base):
    """One employment relationship (person × legal entity). CORE-3: a person
    may hold N concurrent workers, across entities and countries."""
    __tablename__ = "worker"
    __table_args__ = {"schema": "core"}

    worker_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    person_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(RECORD_KEEPING_TAG))
    legal_entity: Mapped[str] = mapped_column(Text, info=dict(_EMPLOYMENT_TAG))
    entity_country: Mapped[str] = mapped_column(Text, info=dict(_EMPLOYMENT_TAG))
    worker_type: Mapped[str] = mapped_column(Text, info=dict(_EMPLOYMENT_TAG))  # employee|contingent|intern|pensioner
    hire_date: Mapped[date] = mapped_column(Date, info=dict(_EMPLOYMENT_TAG))
    original_hire_date: Mapped[date] = mapped_column(Date, info=dict(_EMPLOYMENT_TAG))  # rehire bridging
    carried_flags: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_EMPLOYMENT_TAG))  # e.g. 'negative-pto-balance'


@register_model
class Assignment(TemporalMixin, Base):
    """The temporal job series per worker — EFFDT/EFFSEQ done right (TECH-4)."""
    __tablename__ = "assignment"
    __table_args__ = {"schema": "core"}
    __temporal_identity__ = "worker_id"

    worker_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, info=dict(RECORD_KEEPING_TAG))
    worker_status: Mapped[str] = mapped_column(Text, info=dict(_EMPLOYMENT_TAG))  # active|leave|suspended|terminated
    job_code: Mapped[str] = mapped_column(Text, info=dict(_EMPLOYMENT_TAG))
    department_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, info=dict(_EMPLOYMENT_TAG))
    position_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, info=dict(_EMPLOYMENT_TAG))
    manager_worker_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, info=dict(_EMPLOYMENT_TAG))
    location_country: Mapped[str] = mapped_column(Text, info=dict(_EMPLOYMENT_TAG))
    fte: Mapped[float] = mapped_column(Numeric(4, 2), default=1.0, info=dict(_EMPLOYMENT_TAG))
    pay_group: Mapped[str | None] = mapped_column(Text, nullable=True, info=dict(_EMPLOYMENT_TAG))


@register_model
class Department(Base):
    __tablename__ = "department"
    __table_args__ = {"schema": "core"}

    department_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    name: Mapped[str] = mapped_column(Text, info=dict(_ORG_TAG))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, info=dict(_ORG_TAG))
    status: Mapped[str] = mapped_column(Text, default="active", info=dict(_ORG_TAG))  # active|inactive


@register_model
class Position(Base):
    __tablename__ = "position"
    __table_args__ = {"schema": "core"}

    position_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, info=dict(RECORD_KEEPING_TAG))
    job_code: Mapped[str] = mapped_column(Text, info=dict(_ORG_TAG))
    department_id: Mapped[uuid.UUID] = mapped_column(Uuid, info=dict(_ORG_TAG))
    headcount_budget: Mapped[int] = mapped_column(Integer, default=1, info=dict(_ORG_TAG))
    status: Mapped[str] = mapped_column(Text, default="active", info=dict(_ORG_TAG))
