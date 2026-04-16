export type SupportChatResult = {
  status: "sent" | "reply" | "error";
  message: string;
  conversation_id?: string | null;
  reply?: string | null;
  mail?: {
    to: string;
    subject: string;
    body: string;
    cc: string[];
    bcc: string[];
    attachments: string[];
    raw_input: string;
    parsed_by: "rule" | "llm" | "hybrid";
    require_confirm: boolean;
  } | null;
  error?: {
    code: string;
    message: string;
  } | null;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function parseError(response: Response) {
  const raw = await response.text();
  let detail: unknown = raw;
  try {
    const parsed = raw ? JSON.parse(raw) : null;
    detail = parsed && typeof parsed === "object" && "detail" in parsed ? (parsed as { detail: unknown }).detail : parsed;
  } catch {
    detail = raw;
  }
  return typeof detail === "string" ? detail : "请求失败";
}

export async function sendSupportChat(text: string, conversationId?: string | null): Promise<SupportChatResult> {
  const response = await fetch(`${API_BASE_URL}/ai/support-chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, conversation_id: conversationId ?? undefined }),
  });

  if (response.ok) {
    return response.json() as Promise<SupportChatResult>;
  }

  const message = await parseError(response);
  throw new Error(message);
}
