"""Request models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CampaignCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    status: Literal["draft", "active", "paused", "archived"] = "draft"
    approval_mode: Literal["manual"] = "manual"
    daily_limit: int = Field(default=250, ge=1, le=10000)
    per_domain_limit: int = Field(default=50, ge=1, le=1000)
    timezone: str = "Asia/Kolkata"
    window_start: str = "09:30"
    window_end: str = "17:30"
    working_days: list[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])
    rotation_strategy: Literal["least_used", "round_robin", "weighted"] = "least_used"
    min_gap_seconds: int = Field(default=90, ge=1, le=86400)
    max_gap_seconds: int = Field(default=360, ge=1, le=86400)
    mailbox_ids: list[int] | None = None

    @field_validator("working_days")
    @classmethod
    def valid_days(cls, value: list[int]) -> list[int]:
        cleaned = sorted({int(day) for day in value})
        if not cleaned or any(day < 1 or day > 7 for day in cleaned):
            raise ValueError("working_days must contain days 1..7")
        return cleaned


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    status: Literal["draft", "active", "paused", "archived"] | None = None
    approval_mode: Literal["manual"] | None = None
    daily_limit: int | None = Field(default=None, ge=1, le=10000)
    per_domain_limit: int | None = Field(default=None, ge=1, le=1000)
    timezone: str | None = None
    window_start: str | None = None
    window_end: str | None = None
    working_days: list[int] | None = None
    rotation_strategy: Literal["least_used", "round_robin", "weighted"] | None = None
    min_gap_seconds: int | None = Field(default=None, ge=1, le=86400)
    max_gap_seconds: int | None = Field(default=None, ge=1, le=86400)
    mailbox_ids: list[int] | None = None


class DomainCreate(BaseModel):
    name: str = Field(min_length=3, max_length=253)
    provider: str = "other"
    dkim_selector: str = "mail"
    status: Literal["active", "paused"] = "active"


class DomainUpdate(BaseModel):
    provider: str | None = None
    dkim_selector: str | None = None
    status: Literal["active", "paused"] | None = None


class MailboxCreate(BaseModel):
    domain_id: int
    email: str = Field(min_length=3, max_length=320)
    display_name: str = ""
    transport: Literal["mock", "smtp", "gas"] = "mock"
    smtp_host: str | None = None
    smtp_port: int | None = Field(default=None, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    imap_host: str | None = None
    imap_port: int | None = Field(default=None, ge=1, le=65535)
    imap_username: str | None = None
    imap_password: str | None = None
    gas_url: str | None = None
    gas_secret: str | None = None
    daily_limit: int = Field(default=25, ge=1, le=1000)
    hourly_limit: int = Field(default=5, ge=1, le=200)
    min_gap_seconds: int = Field(default=45, ge=1, le=86400)
    max_gap_seconds: int = Field(default=240, ge=1, le=86400)
    timezone: str = "Asia/Kolkata"
    status: Literal["active", "paused", "error"] = "active"
    campaign_ids: list[int] | None = None


class MailboxUpdate(BaseModel):
    display_name: str | None = None
    transport: Literal["mock", "smtp", "gas"] | None = None
    smtp_host: str | None = None
    smtp_port: int | None = Field(default=None, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    imap_host: str | None = None
    imap_port: int | None = Field(default=None, ge=1, le=65535)
    imap_username: str | None = None
    imap_password: str | None = None
    gas_url: str | None = None
    gas_secret: str | None = None
    daily_limit: int | None = Field(default=None, ge=1, le=1000)
    hourly_limit: int | None = Field(default=None, ge=1, le=200)
    min_gap_seconds: int | None = Field(default=None, ge=1, le=86400)
    max_gap_seconds: int | None = Field(default=None, ge=1, le=86400)
    timezone: str | None = None
    status: Literal["active", "paused", "error"] | None = None
    campaign_ids: list[int] | None = None


class ApproveRequest(BaseModel):
    mailbox_id: int | None = None


class DenyRequest(BaseModel):
    reason: str = ""
    suppress: bool = False


class BulkRequest(BaseModel):
    draft_ids: list[int] = Field(min_length=1)
    action: Literal["approve", "deny"]
    reason: str = ""
    suppress: bool = False


class DraftUpdate(BaseModel):
    subject: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1, max_length=20000)


class SettingsUpdate(BaseModel):
    values: dict[str, str]


class WarmupStart(BaseModel):
    mailbox_ids: list[int] | None = None
    daily_limit: int | None = Field(default=None, ge=1, le=100)


class WarmupAction(BaseModel):
    mailbox_ids: list[int] | None = None


class WarmupSettingsUpdate(BaseModel):
    values: dict[str, str]


class SuppressionCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    reason: str = ""


class SheetsConfigure(BaseModel):
    spreadsheet_id: str = Field(min_length=10, max_length=200)
    credentials_json: str | None = None
    conflict_policy: Literal["merge", "local", "remote"] = "merge"


class SheetsSyncRequest(BaseModel):
    direction: Literal["pull", "push", "both"] = "both"
    dry_run: bool = False
