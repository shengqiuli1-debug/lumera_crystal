from app.repositories.admin_newsletter_repository import AdminNewsletterRepository


class AdminNewsletterService:
    def __init__(self, repo: AdminNewsletterRepository) -> None:
        self.repo = repo

    def list_newsletter(self, **kwargs):
        return self.repo.list(**kwargs)
