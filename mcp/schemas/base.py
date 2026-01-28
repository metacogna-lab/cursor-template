"""Base schemas for MCP Server requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class RequestContext(BaseModel):
    """Request context for policy enforcement."""

    user_id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant/organization identifier")
    auth_context: str = Field(..., description="Authentication context token")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    role: str = Field(default="agent", description="User role (agent or admin)")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is agent or admin."""
        if v not in ("agent", "admin"):
            raise ValueError("Role must be 'agent' or 'admin'")
        return v


class BaseRequest(BaseModel):
    """Base request schema with context."""

    context: RequestContext
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))

    model_config = {
        "json_schema_extra": {
            "example": {
                "context": {
                    "user_id": "user_123",
                    "tenant_id": "tenant_456",
                    "auth_context": "bearer_token_xyz",
                    "role": "agent",
                },
                "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
    }


class BaseResponse(BaseModel):
    """Base response schema."""

    success: bool
    correlation_id: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseResponse):
    """Error response schema."""

    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ToolExecutionRequest(BaseRequest):
    """Request to execute a tool."""

    tool_name: str = Field(..., description="Name of the tool to execute")
    input_data: Dict[str, Any] = Field(..., description="Tool input parameters")


class ToolExecutionResponse(BaseResponse):
    """Response from tool execution."""

    success: bool = True
    tool_name: str
    output_data: Dict[str, Any]
    execution_time_ms: Optional[float] = None
    trace_id: Optional[str] = None


class AgentManifest(BaseModel):
    """Agent manifest for deployment registration."""

    agent_id: str = Field(..., description="Agent identifier (e.g., agent.pm.get_property_details)")
    version: str = Field(..., description="Semver version (e.g., v1.0.0)")
    input_schema: Dict[str, Any] = Field(..., description="Pydantic schema as JSON")
    output_schema: Dict[str, Any] = Field(..., description="Pydantic schema as JSON")
    permitted_tools: List[str] = Field(default_factory=list, description="List of tool names")
    permitted_resources: List[str] = Field(
        default_factory=list, description="List of resource URI patterns"
    )
    rbac_policy_level: str = Field(..., description="Low, Medium, or High")
    workflow_version: Optional[str] = Field(None, description="Workflow version if LangGraph-based")
    prompt_hash: Optional[str] = Field(None, description="SHA256 hash of static prompts")
    created_at: datetime = Field(default_factory=datetime.now)
