"""Tool-specific input/output schemas."""

import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from mcp.schemas.versioning import VersionedSchema


class AnalyzeFeedbackInput(VersionedSchema):
    """Input schema for analyze_open_home_feedback tool."""

    property_id: str = Field(..., min_length=1, max_length=100, description="Property identifier")
    version: str = "v1"

    @field_validator("property_id")
    @classmethod
    def validate_property_id(cls, v: str) -> str:
        """Validate property ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Property ID must contain only alphanumeric characters, hyphens, or underscores"
            )
        return v


class SentimentCategory(BaseModel):
    """Sentiment category breakdown."""

    category: str
    count: int
    percentage: float


class AnalyzeFeedbackOutput(VersionedSchema):
    """Output schema for analyze_open_home_feedback tool."""

    property_id: str
    total_feedback_count: int
    sentiment_categories: List[SentimentCategory]
    top_comments: List[str] = Field(default_factory=list, max_length=10)
    version: str = "v1"


class CalculateBreachInput(VersionedSchema):
    """Input schema for calculate_breach_status tool."""

    tenancy_id: str = Field(..., min_length=1, max_length=100, description="Tenancy identifier")
    version: str = "v1"

    @field_validator("tenancy_id")
    @classmethod
    def validate_tenancy_id(cls, v: str) -> str:
        """Validate tenancy ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Tenancy ID must contain only alphanumeric characters, hyphens, or underscores"
            )
        return v


class BreachRisk(BaseModel):
    """Breach risk classification."""

    level: str = Field(..., description="low, medium, high, or critical")
    days_overdue: Optional[int] = None
    breach_legal_status: str = Field(..., description="compliant, at_risk, or breached")
    recommended_action: Optional[str] = None


class CalculateBreachOutput(VersionedSchema):
    """Output schema for calculate_breach_status tool."""

    tenancy_id: str
    breach_risk: BreachRisk
    current_balance: Optional[float] = None
    last_payment_date: Optional[datetime] = None
    version: str = "v1"


class OCRDocumentInput(VersionedSchema):
    """Input schema for ocr_document tool."""

    document_url: str = Field(..., description="URL to document for OCR")
    version: str = "v1"

    @field_validator("document_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not (v.startswith("http://") or v.startswith("https://") or v.startswith("vault://")):
            raise ValueError("Document URL must be http://, https://, or vault://")
        return v


class OCRDocumentOutput(VersionedSchema):
    """Output schema for ocr_document tool."""

    document_url: str
    extracted_text: str
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    page_count: Optional[int] = None
    version: str = "v1"


class ExtractExpiryInput(VersionedSchema):
    """Input schema for extract_expiry_date tool."""

    text: str = Field(
        ..., min_length=10, max_length=10000, description="Text to extract dates from"
    )
    version: str = "v1"


class ExtractedDate(BaseModel):
    """Extracted date field."""

    field_name: str
    date_value: datetime
    confidence: float = Field(ge=0.0, le=1.0)


class ExtractExpiryOutput(VersionedSchema):
    """Output schema for extract_expiry_date tool."""

    extracted_dates: List[ExtractedDate]
    version: str = "v1"


class GenerateVendorReportInput(VersionedSchema):
    """Input schema for generate_vendor_report tool."""

    property_id: str = Field(..., min_length=1, max_length=100, description="Property identifier")
    version: str = "v1"

    @field_validator("property_id")
    @classmethod
    def validate_property_id(cls, v: str) -> str:
        """Validate property ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Property ID must contain only alphanumeric characters, hyphens, or underscores"
            )
        return v


class GenerateVendorReportOutput(VersionedSchema):
    """Output schema for generate_vendor_report tool."""

    property_id: str
    report_date: datetime
    feedback_summary: dict
    market_trends: Optional[dict] = None
    recommendations: List[str] = Field(default_factory=list)
    version: str = "v1"


class PrepareBreachNoticeInput(VersionedSchema):
    """Input schema for prepare_breach_notice tool (Tier C - HITL required)."""

    tenancy_id: str = Field(..., min_length=1, max_length=100, description="Tenancy identifier")
    breach_type: str = Field(
        ...,
        description="Type of breach: rent_arrears, lease_violation, or property_damage",
    )
    version: str = "v1"

    @field_validator("breach_type")
    @classmethod
    def validate_breach_type(cls, v: str) -> str:
        """Validate breach type."""
        valid_types = ["rent_arrears", "lease_violation", "property_damage"]
        if v not in valid_types:
            raise ValueError(f"Invalid breach_type. Must be one of: {valid_types}")
        return v

    @field_validator("tenancy_id")
    @classmethod
    def validate_tenancy_id(cls, v: str) -> str:
        """Validate tenancy ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Tenancy ID must contain only alphanumeric characters, hyphens, or underscores"
            )
        return v


class PrepareBreachNoticeOutput(VersionedSchema):
    """Output schema for prepare_breach_notice tool."""

    notice_id: str = Field(..., description="Unique notice identifier")
    tenancy_id: str
    breach_type: str
    draft_content: str = Field(..., description="Draft breach notice content (MVP: draft-only)")
    status: str = Field(default="draft", description="Status: draft or pending_approval")
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=None))
    version: str = "v1"
