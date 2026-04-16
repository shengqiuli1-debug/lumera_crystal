import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.mail_command import MailCommandInput, MailCommandResult
from app.schemas.support_chat import SupportChatInput, SupportChatResult
from app.services.ai_service import AIService
from app.services.mail_command_service import MailCommandService
from app.services.support_chat_service import SupportChatService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/health")
def ai_health() -> dict:
    return AIService().health()


@router.post("/mail/command", response_model=MailCommandResult)
def handle_mail_command(payload: MailCommandInput) -> MailCommandResult:
    return MailCommandService().handle_text(payload.text)


@router.post("/support-chat", response_model=SupportChatResult)
def support_chat(payload: SupportChatInput, db: Session = Depends(get_db)) -> SupportChatResult:
    service = SupportChatService(repo=ConversationRepository(db))
    return service.handle_text(
        payload.text,
        conversation_id=payload.conversation_id,
        debug=payload.debug,
        request_id=str(uuid.uuid4()),
    )
