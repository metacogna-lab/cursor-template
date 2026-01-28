"""Tests for Tier C (mutation/high-risk) agents."""

import pytest

from mcp.schemas.base import RequestContext
from mcp.schemas.tools import (
    PrepareBreachNoticeInput,
    PrepareBreachNoticeOutput,
)
from mcp.tools.implementations import prepare_breach_notice


@pytest.fixture
def context():
    """Create test request context."""
    return RequestContext(
        user_id="test_user",
        tenant_id="test_tenant",
        auth_context="test_token",
        role="admin",  # Tier C requires admin
    )


@pytest.mark.asyncio
async def test_prepare_breach_notice_valid(context):
    """Test prepare_breach_notice with valid input."""
    input_data = PrepareBreachNoticeInput(tenancy_id="tenancy_001", breach_type="rent_arrears")
    output = await prepare_breach_notice(input_data, context)

    assert output.notice_id.startswith("notice_")
    assert output.tenancy_id == "tenancy_001"
    assert output.breach_type == "rent_arrears"
    assert output.status == "draft"
    assert len(output.draft_content) > 0
    assert "DRAFT" in output.draft_content.upper()


@pytest.mark.asyncio
async def test_prepare_breach_notice_invalid_breach_type(context):
    """Test prepare_breach_notice with invalid breach_type."""
    with pytest.raises(ValueError, match="Invalid breach_type"):
        PrepareBreachNoticeInput(tenancy_id="tenancy_001", breach_type="invalid_type")


@pytest.mark.asyncio
async def test_prepare_breach_notice_all_breach_types(context):
    """Test prepare_breach_notice with all valid breach types."""
    for breach_type in ["rent_arrears", "lease_violation", "property_damage"]:
        input_data = PrepareBreachNoticeInput(tenancy_id="tenancy_001", breach_type=breach_type)
        output = await prepare_breach_notice(input_data, context)
        assert output.breach_type == breach_type
        assert output.status == "draft"


def test_prepare_breach_notice_output_serialization():
    """Test PrepareBreachNoticeOutput serialization."""
    from datetime import datetime

    output = PrepareBreachNoticeOutput(
        notice_id="notice_123",
        tenancy_id="tenancy_001",
        breach_type="rent_arrears",
        draft_content="Test draft",
        status="draft",
        created_at=datetime.now(),
    )

    dumped = output.model_dump()
    assert dumped["notice_id"] == "notice_123"
    assert dumped["tenancy_id"] == "tenancy_001"
    assert dumped["breach_type"] == "rent_arrears"
    assert dumped["status"] == "draft"
    assert "created_at" in dumped
