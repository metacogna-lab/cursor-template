"""Tier C (Mutation/High-Risk) Agent manifests."""

from mcp.agents import register_agent
from mcp.schemas.base import AgentManifest
from mcp.schemas.tools import (
    PrepareBreachNoticeInput,
    PrepareBreachNoticeOutput,
)


def register_tier_c_agents() -> None:
    """Register all Tier C mutation/high-risk agents."""

    # Agent: prepare_breach_notice (draft-only in MVP)
    register_agent(
        AgentManifest(
            agent_id="agent.pm.prepare_breach_notice",
            version="v1.0.0",
            input_schema=PrepareBreachNoticeInput.model_json_schema(),
            output_schema=PrepareBreachNoticeOutput.model_json_schema(),
            permitted_tools=["prepare_breach_notice", "calculate_breach_status"],
            permitted_resources=["ailo://ledgers/{tenancy_id}/summary"],
            rbac_policy_level="High",
            workflow_version=None,
            prompt_hash=None,
        )
    )
