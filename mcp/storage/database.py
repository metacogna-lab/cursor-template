"""SQLite database for MCP Server persistence."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from mcp.config import settings


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj):
        """Encode datetime objects as ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class Database:
    """SQLite database manager for MCP Server."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection."""
        self.db_path = db_path or settings.database_path
        self._ensure_db_dir()
        self._init_schema()

    def _ensure_db_dir(self) -> None:
        """Ensure database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Tool execution logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    correlation_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    input_data TEXT,
                    output_data TEXT,
                    execution_time_ms REAL,
                    trace_id TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # LangGraph workflow executions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    correlation_id TEXT NOT NULL,
                    workflow_name TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    state_snapshot TEXT,
                    trace_id TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)

            # Agent manifests
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_manifests (
                    agent_id TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    input_schema TEXT NOT NULL,
                    output_schema TEXT NOT NULL,
                    permitted_tools TEXT,
                    permitted_resources TEXT,
                    rbac_policy_level TEXT NOT NULL,
                    workflow_version TEXT,
                    prompt_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Audit log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    correlation_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    tenant_id TEXT,
                    tool_name TEXT,
                    action TEXT,
                    policy_result TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def log_tool_execution(
        self,
        correlation_id: str,
        tool_name: str,
        user_id: str,
        tenant_id: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[float] = None,
        trace_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Log tool execution to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tool_executions (
                    correlation_id, tool_name, user_id, tenant_id,
                    input_data, output_data, execution_time_ms, trace_id,
                    success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    correlation_id,
                    tool_name,
                    user_id,
                    tenant_id,
                    json.dumps(input_data, cls=DateTimeEncoder),
                    json.dumps(output_data, cls=DateTimeEncoder) if output_data else None,
                    execution_time_ms,
                    trace_id,
                    success,
                    error_message,
                ),
            )
            conn.commit()

    def log_audit_event(
        self,
        correlation_id: str,
        event_type: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        action: Optional[str] = None,
        policy_result: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log audit event."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_log (
                    correlation_id, event_type, user_id, tenant_id,
                    tool_name, action, policy_result, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    correlation_id,
                    event_type,
                    user_id,
                    tenant_id,
                    tool_name,
                    action,
                    policy_result,
                    json.dumps(details, cls=DateTimeEncoder) if details else None,
                ),
            )
            conn.commit()


# Global database instance
_db: Optional[Database] = None


def get_db() -> Database:
    """Get global database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db
