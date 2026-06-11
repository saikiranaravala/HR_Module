"""Single declarative base shared by platform tables and conformance test entities."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
