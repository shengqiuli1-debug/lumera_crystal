from app.repositories.contact_repository import ContactRepository
from app.schemas.contact import ContactCreate
from app.services.email_service import EmailService


class ContactService:
    def __init__(self, repo: ContactRepository, email_service: EmailService | None = None) -> None:
        self.repo = repo
        self.email_service = email_service or EmailService()

    @staticmethod
    def _build_auto_reply(payload: ContactCreate) -> tuple[str, str]:
        subject = f"已收到你的咨询：{payload.subject}"
        body = (
            f"你好 {payload.name}，\n\n"
            "我们已经收到你的咨询，以下是你提交的问题：\n"
            f"{payload.message}\n\n"
            "初步建议：\n"
            "1. 如果你在选购水晶产品，欢迎补充预算、偏好颜色和佩戴场景，我们会给你更精确推荐。\n"
            "2. 如果是订单或合作问题，请附上相关编号，我们会优先处理。\n\n"
            "这是一封自动回复邮件，我们会在 24 小时内给你进一步答复。\n\n"
            "LUMERA CRYSTAL 团队"
        )
        return subject, body

    def create_message(self, payload: ContactCreate):
        item = self.repo.create(
            name=payload.name,
            email=payload.email,
            subject=payload.subject,
            message=payload.message,
        )
        reply_subject, reply_body = self._build_auto_reply(payload)
        try:
            self.email_service.send_mail(to_email=payload.email, subject=reply_subject, body=reply_body)
            self.repo.update_auto_reply(item, status="sent", subject=reply_subject, body=reply_body)
        except Exception:  # noqa: BLE001
            self.repo.update_auto_reply(item, status="failed", subject=reply_subject, body=reply_body)
        return item
