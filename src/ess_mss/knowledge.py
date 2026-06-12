"""Knowledge base (ESS-2, Specs/10 §5): population-targeted articles with
review cycles and a legal-review gate for policy content."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ess_mss.models import KbArticle

REVIEW_CYCLE = timedelta(days=365)  # stale-content alert at 12 months


class LegalReviewRequiredError(PermissionError):
    pass


def draft_article(session: Session, *, title: str, body: str, country: str,
                  population: str = "all", is_policy: bool = False) -> KbArticle:
    article = KbArticle(title=title, body=body, country=country,
                        population=population, status="draft", is_policy=is_policy)
    session.add(article)
    session.flush()
    return article


def submit_for_legal_review(session: Session, article: KbArticle) -> KbArticle:
    article.status = "in-legal-review"
    session.flush()
    return article


def publish(session: Session, article: KbArticle, *, on: date,
            legal_approved: bool = False) -> KbArticle:
    """Policy articles cannot skip the legal gate (§5 authoring workflow)."""
    if article.is_policy and not (article.status == "in-legal-review" and legal_approved):
        raise LegalReviewRequiredError("policy article requires legal review before publish")
    article.status = "published"
    article.published_on = on
    article.review_due = on + REVIEW_CYCLE
    session.flush()
    return article


def stale_articles(session: Session, *, as_of: date) -> list[KbArticle]:
    return session.scalars(select(KbArticle).where(
        KbArticle.status == "published",
        KbArticle.review_due <= as_of,
    )).all()


def visible_articles(session: Session, *, country: str, population: str) -> list[KbArticle]:
    """Same variant-safety model as retrieval: country/population are absolute filters."""
    return session.scalars(select(KbArticle).where(
        KbArticle.status == "published",
        KbArticle.country == country,
        KbArticle.population.in_([population, "all"]),
    )).all()
