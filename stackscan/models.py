from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ScanResult(BaseModel):
    scanner: str
    category: Literal["security", "code_quality"]
    severity: Literal["critical", "high", "medium", "low", "info"]
    title: str
    detail: str
    file_path: Optional[str] = None
    line: Optional[int] = None


class ScanReport(BaseModel):
    scan_id: UUID = Field(default_factory=uuid4)
    repo: str = ""
    commit_sha: str = ""
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    findings: list[ScanResult] = Field(default_factory=list)
