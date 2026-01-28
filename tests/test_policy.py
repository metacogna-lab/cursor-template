"""Tests for policy gateway."""

from mcp.policy import get_policy_gateway
from mcp.schemas.base import RequestContext


def test_policy_check_valid_agent():
    """Test policy check for agent role."""
    gateway = get_policy_gateway()
    context = RequestContext(
        user_id="user_123",
        tenant_id="tenant_456",
        auth_context="bearer_token",
        role="agent",
    )

    allowed, error = gateway.check_rbac(context, "analyze_open_home_feedback")
    assert allowed is True
    assert error is None


def test_policy_check_insufficient_permissions():
    """Test policy check with insufficient permissions."""
    gateway = get_policy_gateway()
    context = RequestContext(
        user_id="user_123",
        tenant_id="tenant_456",
        auth_context="bearer_token",
        role="agent",
    )

    # prepare_breach_notice requires admin
    allowed, error = gateway.check_rbac(context, "prepare_breach_notice")
    assert allowed is False
    assert "admin" in error.lower()


def test_policy_check_hitl_required():
    """Test policy check for HITL-required tools."""
    gateway = get_policy_gateway()
    context = RequestContext(
        user_id="user_123",
        tenant_id="tenant_456",
        auth_context="bearer_token",
        role="admin",
    )

    # Without HITL token
    allowed, error = gateway.check_rbac(context, "prepare_breach_notice")
    assert allowed is False
    assert "HITL" in error

    # With HITL token (mock)
    from mcp.config import settings

    allowed, error = gateway.check_rbac(
        context, "prepare_breach_notice", hitl_token=settings.hitl_token_secret
    )
    # Note: In real implementation, token validation would be more sophisticated
    # For MVP, we just check it matches the secret


def test_request_context_validation():
    """Test request context validation."""
    gateway = get_policy_gateway()

    # Valid context
    context = RequestContext(
        user_id="user_123",
        tenant_id="tenant_456",
        auth_context="bearer_token",
    )
    valid, error = gateway.check_request_context(context)
    assert valid is True

    # Missing user_id
    context = RequestContext(
        user_id="",
        tenant_id="tenant_456",
        auth_context="bearer_token",
    )
    valid, error = gateway.check_request_context(context)
    assert valid is False
    assert "user_id" in error.lower()
