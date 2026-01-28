"""Tool registry for MCP Server."""

from typing import Any, Callable, Dict, Optional


class ToolRegistry:
    """Registry for MCP tools."""

    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, Callable] = {}
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        func: Callable,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a tool."""
        self._tools[name] = func
        self._tool_metadata[name] = metadata or {}

    def get(self, name: str) -> Optional[Callable]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """Get tool metadata."""
        return self._tool_metadata.get(name, {})

    def list_tools(self) -> list[str]:
        """List all registered tools."""
        return list(self._tools.keys())


# Global tool registry
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def register_tool(name: str, func: Callable, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Register a tool in the global registry."""
    get_tool_registry().register(name, func, metadata)


def get_tool(name: str) -> Optional[Callable]:
    """Get a tool from the global registry."""
    return get_tool_registry().get(name)
