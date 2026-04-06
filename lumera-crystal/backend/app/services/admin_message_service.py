from fastapi import HTTPException, status

from app.repositories.admin_message_repository import AdminMessageRepository
from app.services.email_service import EmailService


class AdminMessageService:
    def __init__(self, repo: AdminMessageRepository, email_service: EmailService | None = None) -> None:
        self.repo = repo
        self.email_service = email_service or EmailService()

    def list_messages(self, **kwargs):
        return self.repo.list(**kwargs)

    def get_or_404(self, message_id: int):
        item = self.repo.get(message_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        return item

    def mark_read(self, message_id: int, *, is_read: bool = True):
        item = self.get_or_404(message_id)
        return self.repo.mark_read(item, is_read=is_read)

    def reply_to_message(self, message_id: int, *, reply_content: str):
        item = self.get_or_404(message_id)
        text = reply_content.strip()
        if not text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reply content cannot be empty")

        subject = f"关于你的咨询：{item.subject}"
        body = (
            f"你好 {item.name}，\n\n"
            "感谢你联系 LUMERA CRYSTAL，我们已收到并处理你的问题。\n\n"
            "你的问题：\n"
            f"{item.message}\n\n"
            "商家回复：\n"
            f"{text}\n\n"
            "如需继续沟通，直接回复此邮件即可。\n\n"
            "LUMERA CRYSTAL 团队"
        )
        try:
            self.email_service.send_mail(to_email=item.email, subject=subject, body=body)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"邮件发送失败，请检查 SMTP 配置：{exc}",
            ) from exc
        return self.repo.mark_replied(item, subject=subject, body=body)
