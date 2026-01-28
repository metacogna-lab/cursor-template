"""MCP Resources implementation."""

from mcp.resources.registry import (
    ResourceRegistry,
    get_resource,
    get_resource_registry,
    register_resource,
)

__all__ = ["ResourceRegistry", "get_resource_registry", "register_resource", "get_resource"]
