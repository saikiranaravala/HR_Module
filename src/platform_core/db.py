"""Database wiring. Connection URLs come from src/.env (git-ignored)."""
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def load_env(path: Path = _ENV_FILE) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def database_url(test: bool = False) -> str:
    load_env()
    var = "MERIDIAN_TEST_DATABASE_URL" if test else "MERIDIAN_DATABASE_URL"
    url = os.environ.get(var)
    if not url:
        raise RuntimeError(f"{var} is not set (expected in src/.env)")
    return url


def make_engine(test: bool = False):
    return create_engine(database_url(test), future=True)


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
