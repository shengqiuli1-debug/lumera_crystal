from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


ToolDataSource = Literal["mock", "real_api", "none"]


class ToolError(BaseModel):
    code: str
    message: str


class ToolResult(BaseModel):
    success: bool
    tool_name: str
    data_source: ToolDataSource
    source_detail: str
    data: dict[str, Any] | list[Any] | None = None
    error: ToolError | None = None
    latency_ms: int | None = None
