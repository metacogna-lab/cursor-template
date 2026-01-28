"""CLI entrypoint for MCP Server tools and workflows."""

import asyncio
import json
import sys

import click

from mcp.config import settings
from mcp.schemas.base import RequestContext
from mcp.tools import get_tool_registry


@click.group()
def cli():
    """Tenure MCP Server CLI."""
    pass


@cli.command()
@click.argument("tool_name")
@click.option("--input", "-i", type=click.Path(exists=True), help="Input JSON file")
@click.option("--user-id", default="cli_user", help="User ID")
@click.option("--tenant-id", default="cli_tenant", help="Tenant ID")
@click.option("--role", default="agent", type=click.Choice(["agent", "admin"]), help="User role")
def run_tool(tool_name: str, input: str, user_id: str, tenant_id: str, role: str):
    """Run a tool with input from file or stdin."""
    # Load input data
    if input:
        with open(input) as f:
            input_data = json.load(f)
    else:
        # Read from stdin
        input_data = json.load(sys.stdin)

    # Create request context
    context = RequestContext(
        user_id=user_id,
        tenant_id=tenant_id,
        auth_context=f"cli_{user_id}",
        role=role,
    )

    # Get tool
    registry = get_tool_registry()
    tool_func = registry.get(tool_name)
    if not tool_func:
        click.echo(f"Error: Tool '{tool_name}' not found", err=True)
        sys.exit(1)

    # Execute tool
    async def execute():
        try:
            # Parse input based on tool (simplified - would use schema registry in production)
            from mcp.schemas.tools import (
                AnalyzeFeedbackInput,
                CalculateBreachInput,
                ExtractExpiryInput,
                GenerateVendorReportInput,
                OCRDocumentInput,
            )

            schema_map = {
                "analyze_open_home_feedback": AnalyzeFeedbackInput,
                "calculate_breach_status": CalculateBreachInput,
                "ocr_document": OCRDocumentInput,
                "extract_expiry_date": ExtractExpiryInput,
                "generate_vendor_report": GenerateVendorReportInput,
            }

            schema_class = schema_map.get(tool_name)
            if not schema_class:
                click.echo(f"Error: Unknown tool schema for '{tool_name}'", err=True)
                sys.exit(1)

            tool_input = schema_class(**input_data)
            output = await tool_func(tool_input, context)

            # Output result
            output_dict = output.model_dump() if hasattr(output, "model_dump") else dict(output)
            click.echo(json.dumps(output_dict, indent=2, default=str))

        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(execute())


@cli.command()
@click.argument("graph_name")
@click.option("--input", "-i", type=click.Path(exists=True), help="Input JSON file")
def run_graph(graph_name: str, input: str):
    """Run a LangGraph workflow (placeholder for Phase 2)."""
    click.echo(f"LangGraph workflows not yet implemented. Graph: {graph_name}")
    click.echo("This will be available in Phase 2 (Tier B agents)")
    sys.exit(1)


@cli.command()
def list_tools():
    """List all available tools."""
    registry = get_tool_registry()
    tools = registry.list_tools()
    click.echo("Available tools:")
    for tool in tools:
        click.echo(f"  - {tool}")


@cli.command()
@click.option("--tool", help="Tool name to generate token for")
def generate_token(tool: str):
    """Generate HITL token for a tool (MVP stub)."""
    if not tool:
        click.echo("Error: --tool is required", err=True)
        sys.exit(1)

    # In MVP, just return the secret (in production, would sign/encrypt)
    click.echo(f"HITL token for '{tool}': {settings.hitl_token_secret}")
    click.echo("Note: In production, this would be a signed token")


if __name__ == "__main__":
    cli()
