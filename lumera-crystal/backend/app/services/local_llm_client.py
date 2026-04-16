from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class LocalLLMClient:
    def __init__(self) -> None:
        if not settings.llm_provider or not settings.llm_base_url or not settings.llm_model:
            raise RuntimeError("LLM is not configured")
        self.provider = settings.llm_provider.lower()
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model = settings.llm_model
        self.api_key = settings.llm_api_key
        self.timeout = settings.llm_timeout_seconds

    def parse_mail_command(self, text: str) -> dict[str, Any]:
        if self.provider == "ollama":
            return self._call_ollama(text)
        if self.provider == "openai":
            return self._call_openai(text)
        raise RuntimeError(f"Unsupported LLM provider: {self.provider}")

    def chat(self, text: str) -> str:
        if self.provider == "ollama":
            return self._chat_ollama(text)
        if self.provider == "openai":
            return self._chat_openai(text)
        raise RuntimeError(f"Unsupported LLM provider: {self.provider}")

    def support_chat(self, text: str) -> dict[str, Any]:
        if self.provider == "ollama":
            return self._support_chat_ollama(text)
        if self.provider == "openai":
            return self._support_chat_openai(text)
        raise RuntimeError(f"Unsupported LLM provider: {self.provider}")

    def support_chat_messages(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        if self.provider == "ollama":
            return self._support_chat_ollama_messages(messages)
        if self.provider == "openai":
            return self._support_chat_openai_messages(messages)
        raise RuntimeError(f"Unsupported LLM provider: {self.provider}")

    def _call_openai(self, text: str) -> dict[str, Any]:
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": _mail_system_prompt()},
                {"role": "user", "content": text},
            ],
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = json.dumps(payload).encode("utf-8")
        try:
            request = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                response_text = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            logger.error("LLM request failed: %s", exc)
            raise RuntimeError("LLM request failed") from exc
        return _extract_json_from_response(response_text)

    def _call_ollama(self, text: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": _mail_system_prompt()},
                {"role": "user", "content": text},
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        try:
            request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                response_text = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            logger.error("LLM request failed: %s", exc)
            raise RuntimeError("LLM request failed") from exc
        return _extract_json_from_response(response_text)

    def _chat_openai(self, text: str) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "temperature": 0.4,
            "messages": [
                {"role": "system", "content": _support_system_prompt()},
                {"role": "user", "content": text},
            ],
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = json.dumps(payload).encode("utf-8")
        try:
            request = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                response_text = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            logger.error("LLM request failed: %s", exc)
            raise RuntimeError("LLM request failed") from exc
        return _extract_text_from_response(response_text)

    def _chat_ollama(self, text: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": _support_system_prompt()},
                {"role": "user", "content": text},
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        try:
            request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                response_text = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            logger.error("LLM request failed: %s", exc)
            raise RuntimeError("LLM request failed") from exc
        return _extract_text_from_response(response_text)

    def _support_chat_openai(self, text: str) -> dict[str, Any]:
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": _support_chat_system_prompt()},
                {"role": "user", "content": text},
            ],
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = json.dumps(payload).encode("utf-8")
        try:
            request = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                response_text = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            logger.error("LLM request failed: %s", exc)
            raise RuntimeError("LLM request failed") from exc
        return _extract_json_from_response(response_text)

    def _support_chat_ollama(self, text: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": _support_chat_system_prompt()},
                {"role": "user", "content": text},
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        try:
            request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                response_text = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            logger.error("LLM request failed: %s", exc)
            raise RuntimeError("LLM request failed") from exc
        return _extract_json_from_response(response_text)

    def _support_chat_openai_messages(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": messages,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = json.dumps(payload).encode("utf-8")
        try:
            request = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                response_text = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            logger.error("LLM request failed: %s", exc)
            raise RuntimeError("LLM request failed") from exc
        return _extract_json_from_response(response_text)

    def _support_chat_ollama_messages(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": messages,
        }
        data = json.dumps(payload).encode("utf-8")
        try:
            request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                response_text = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            logger.error("LLM request failed: %s", exc)
            raise RuntimeError("LLM request failed") from exc
        return _extract_json_from_response(response_text)


def _mail_system_prompt() -> str:
    return (
        "你是一个只输出 JSON 的严格结构化助手。"
        "必须仅返回一个 JSON 对象，且必须包含以下键："
        "to, subject, body, cc, bcc, attachments。"
        "其中 to/subject/body 必须是非空字符串；cc/bcc/attachments 必须是数组（可为空）。"
        "不要输出任何额外文本、解释或 markdown。"
    )


def _support_system_prompt() -> str:
    return (
        "你是商家客服助手。"
        "请用简洁、礼貌、专业的中文回复用户问题。"
        "不要编造无法确认的事实。"
    )


def _support_chat_system_prompt() -> str:
    return (
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
        "不要输出任何额外文本。"
    )


def _extract_json_from_response(response_text: str) -> dict[str, Any]:
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("LLM response is not valid JSON") from exc

    content: str | None = None
    if isinstance(data, dict) and "choices" in data:
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:  # noqa: BLE001
            content = None
    elif isinstance(data, dict) and "message" in data:
        content = data.get("message", {}).get("content")

    if content is None:
        if isinstance(data, dict) and _looks_like_mail_json(data):
            return data
        raise RuntimeError("LLM response missing content")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("LLM content is not valid JSON") from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("LLM content must be a JSON object")
    return parsed


def _extract_text_from_response(response_text: str) -> str:
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("LLM response is not valid JSON") from exc

    content: str | None = None
    if isinstance(data, dict) and "choices" in data:
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:  # noqa: BLE001
            content = None
    elif isinstance(data, dict) and "message" in data:
        content = data.get("message", {}).get("content")

    if not content or not isinstance(content, str):
        raise RuntimeError("LLM response missing content")
    return content.strip()


def _looks_like_mail_json(data: dict[str, Any]) -> bool:
    keys = {"to", "subject", "body", "cc", "bcc", "attachments"}
    return keys.issubset(set(data.keys()))
