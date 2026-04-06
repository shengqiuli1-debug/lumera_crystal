from app.repositories.newsletter_repository import NewsletterRepository
from app.schemas.newsletter import NewsletterCreate


class NewsletterService:
    def __init__(self, repo: NewsletterRepository) -> None:
        self.repo = repo

    def subscribe(self, payload: NewsletterCreate):
        exists = self.repo.get_by_email(payload.email)
        if exists:
            return exists, False
        return self.repo.create(email=payload.email, source=payload.source), True
