"""Policy gateway for RBAC and access control."""

from typing import Dict, List, Optional

from mcp.config import settings
from mcp.schemas.base import RequestContext
from mcp.storage import get_db


class PolicyGateway:
    """Policy enforcement gateway for MCP Server."""

    # RBAC matrix: tool_name -> required_role
    RBAC_MATRIX: Dict[str, str] = {
        "get_property_details": "agent",
        "analyze_open_home_feedback": "agent",
        "check_ledger_arrears": "agent",
        "calculate_breach_status": "agent",
        "ocr_document": "agent",
        "extract_expiry_date": "agent",
        "generate_vendor_report": "agent",
        # High-risk tools require admin
        "prepare_breach_notice": "admin",
        "archive_listing": "admin",
    }

    # Tools requiring HITL token
    HITL_REQUIRED: List[str] = [
        "prepare_breach_notice",
        "archive_listing",
    ]

    # Mutation tools (for audit logging) - Tier C high-risk
    MUTATION_TOOLS: List[str] = [
        "prepare_breach_notice",
        "archive_listing",
    ]

    def __init__(self):
        """Initialize policy gateway."""
        self.db = get_db()

    def check_rbac(
        self, context: RequestContext, tool_name: str, hitl_token: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check RBAC policy for tool execution.

        Returns:
            (allowed, error_message)
        """
        # Check if tool exists in matrix
        required_role = self.RBAC_MATRIX.get(tool_name)
        if required_role is None:
            return False, f"Tool '{tool_name}' not found in RBAC matrix"

        # Check role permission
        role_hierarchy = {"agent": 1, "admin": 2}
        user_level = role_hierarchy.get(context.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        if user_level < required_level:
            return False, f"Insufficient permissions: '{tool_name}' requires role '{required_role}'"

        # Check HITL token for high-risk tools
        if tool_name in self.HITL_REQUIRED:
            if not settings.hitl_enabled:
                return False, "HITL is disabled in configuration"
            if not hitl_token:
                return False, f"Tool '{tool_name}' requires HITL confirmation token"
            # In MVP, we just check token exists; real validation would verify signature
            if hitl_token != settings.hitl_token_secret:
                return False, "Invalid HITL token"

        return True, None

    def check_request_context(self, context: RequestContext) -> tuple[bool, Optional[str]]:
        """Validate request context has required fields."""
        if not context.user_id:
            return False, "Missing user_id in request context"
        if not context.tenant_id:
            return False, "Missing tenant_id in request context"
        if not context.auth_context:
            return False, "Missing auth_context in request context"
        return True, None

    def redact_output(self, output: dict, context: RequestContext, tool_name: str) -> dict:
        """
        Redact sensitive data from output based on context and tool.

        In MVP, we do basic PII redaction. Full implementation would use
        more sophisticated redaction rules.
        """
        # Basic PII patterns to redact for non-admin users
        if context.role != "admin":
            # Redact email addresses
            import re

            redacted = str(output)
            redacted = re.sub(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]", redacted
            )
            # Redact phone numbers
            redacted = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]", redacted)

            # For structured output, we'd need more sophisticated redaction
            # For MVP, we return as-is but log that redaction was applied
            self.db.log_audit_event(
                correlation_id="",
                event_type="redaction_applied",
                user_id=context.user_id,
                tenant_id=context.tenant_id,
                tool_name=tool_name,
                action="redact_output",
            )

        return output

    def log_policy_decision(
        self,
        correlation_id: str,
        context: RequestContext,
        tool_name: str,
        allowed: bool,
        reason: Optional[str] = None,
    ) -> None:
        """Log policy decision for audit trail."""
        self.db.log_audit_event(
            correlation_id=correlation_id,
            event_type="policy_check",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            tool_name=tool_name,
            action="execute" if allowed else "block",
            policy_result="allowed" if allowed else "denied",
            details={"reason": reason} if reason else None,
        )


# Global policy gateway instance
_policy_gateway: Optional[PolicyGateway] = None


def get_policy_gateway() -> PolicyGateway:
    """Get global policy gateway instance."""
    global _policy_gateway
    if _policy_gateway is None:
        _policy_gateway = PolicyGateway()
    return _policy_gateway


def check_policy(
    context: RequestContext, tool_name: str, hitl_token: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """Convenience function to check policy."""
    gateway = get_policy_gateway()
    return gateway.check_rbac(context, tool_name, hitl_token)
