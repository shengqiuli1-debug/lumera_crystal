export type MailCommandResult = {
  status: "sent" | "ignored" | "error";
  message: string;
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

export async function sendMailCommand(text: string): Promise<MailCommandResult> {
  const response = await fetch(`${API_BASE_URL}/ai/mail/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    const raw = await response.text();
    let detail: unknown = raw;
    try {
      const parsed = raw ? JSON.parse(raw) : null;
      detail = parsed && typeof parsed === "object" && "detail" in parsed ? parsed.detail : parsed;
    } catch {
      detail = raw;
    }
    const message = typeof detail === "string" ? detail : "请求失败";
    throw new Error(message);
  }

  return response.json() as Promise<MailCommandResult>;
}
