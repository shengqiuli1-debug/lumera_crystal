from __future__ import annotations

from app.models import Conversation


SYSTEM_PROMPT = (
    "你是商家客服助手，只输出 JSON。"
    "请判断用户意图："
    "如果用户明确以“发邮件给/发送邮件给”开头，则 intent 必须为 mail，"
    "并输出完整的 to/subject/body。"
    "否则 intent 为 reply，并给出 reply 文本。"
    "必须仅返回以下 JSON 结构："
    "{"
    "\"intent\":\"mail|reply\","
    "\"reply\":\"\","
    "\"to\":\"\","
    "\"subject\":\"\","
    "\"body\":\"\","
    "\"cc\":[],"
    "\"bcc\":[],"
    "\"attachments\":[]"
    "}"
    "规则："
    "1) intent=mail 时，to/subject/body 必须为非空字符串，reply 置空字符串。"
    "2) intent=reply 时，reply 必须为非空字符串，to/subject/body 置空字符串。"
    "3) cc/bcc/attachments 必须是数组。"
    "4) 你不能声称拥有设备定位、摄像头、麦克风或系统权限；"
    "   但可以基于对话历史中用户提供的信息回答，并用“根据你刚才提供的信息”表述。"
)


def build_support_messages(
    *,
    history: list[Conversation],
    user_input: str,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in history:
        role = "assistant" if item.role == "assistant" else "user"
        messages.append({"role": role, "content": item.content})
    messages.append({"role": "user", "content": user_input})
    return messages
