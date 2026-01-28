"""Agent registry for deployment registration."""

import json
from typing import Dict, Optional

from mcp.schemas.base import AgentManifest
from mcp.storage import get_db


class AgentRegistry:
    """Registry for agent manifests."""

    def __init__(self):
        """Initialize agent registry."""
        self._agents: Dict[str, AgentManifest] = {}
        self.db = get_db()

    def register(self, manifest: AgentManifest) -> None:
        """Register an agent manifest."""
        self._agents[manifest.agent_id] = manifest

        # Persist to database
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO agent_manifests (
                    agent_id, version, input_schema, output_schema,
                    permitted_tools, permitted_resources, rbac_policy_level,
                    workflow_version, prompt_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    manifest.agent_id,
                    manifest.version,
                    json.dumps(manifest.input_schema),
                    json.dumps(manifest.output_schema),
                    json.dumps(manifest.permitted_tools),
                    json.dumps(manifest.permitted_resources),
                    manifest.rbac_policy_level,
                    manifest.workflow_version,
                    manifest.prompt_hash,
                ),
            )
            conn.commit()

    def get(self, agent_id: str) -> Optional[AgentManifest]:
        """Get agent manifest by ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> list[str]:
        """List all registered agent IDs."""
        return list(self._agents.keys())


# Global agent registry
_agent_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get global agent registry."""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry


def register_agent(manifest: AgentManifest) -> None:
    """Register an agent in the global registry."""
    get_agent_registry().register(manifest)
