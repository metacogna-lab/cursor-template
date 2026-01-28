"""Production deployment tests for Railway."""

import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from mcp.server.app import create_app
from mcp.config import Settings


@pytest.fixture
def client():
    """Create test client with proper lifespan handling."""
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def auth_headers():
    """Authentication headers for API requests."""
    return {
        "Authorization": "Bearer dev-token-insecure",
        "X-User-ID": "test_user",
        "X-Tenant-ID": "test_tenant",
        "X-Auth-Context": "test_context",
        "X-Role": "agent",
    }


class TestHealthEndpoints:
    """Test health and readiness endpoints."""

    def test_healthz_endpoint(self, client):
        """Test /healthz returns healthy status."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_readiness_endpoint(self, client):
        """Test /ready returns readiness status with dependency checks."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert data["checks"]["database"] is True
        assert data["checks"]["tools_registered"] is True
        assert data["checks"]["resources_registered"] is True

    def test_version_endpoint(self, client):
        """Test /version returns version info."""
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "api_version" in data

    def test_metrics_endpoint(self, client):
        """Test /metrics returns Prometheus-compatible metrics."""
        response = client.get("/metrics")
        assert response.status_code == 200
        # Should return text content
        assert response.text is not None


class TestToolEndpoints:
    """Test tool execution endpoints."""

    def test_tool_execution_analyze_feedback(self, client, auth_headers):
        """Test analyze_open_home_feedback tool via API."""
        response = client.post(
            "/v1/tools/analyze_open_home_feedback",
            json={
                "tool_name": "analyze_open_home_feedback",
                "context": {
                    "user_id": "test_user",
                    "tenant_id": "test_tenant",
                    "auth_context": "test_token",
                    "role": "agent",
                },
                "input_data": {"property_id": "prop_001"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tool_name"] == "analyze_open_home_feedback"

    def test_tool_execution_calculate_breach(self, client, auth_headers):
        """Test calculate_breach_status tool via API."""
        response = client.post(
            "/v1/tools/calculate_breach_status",
            json={
                "tool_name": "calculate_breach_status",
                "context": {
                    "user_id": "test_user",
                    "tenant_id": "test_tenant",
                    "auth_context": "test_token",
                    "role": "agent",
                },
                "input_data": {"tenancy_id": "tenancy_001"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_tool_not_found(self, client, auth_headers):
        """Test 403 for unknown tool (RBAC check first for security)."""
        response = client.post(
            "/v1/tools/nonexistent_tool",
            json={
                "tool_name": "nonexistent_tool",
                "context": {
                    "user_id": "test_user",
                    "tenant_id": "test_tenant",
                    "auth_context": "test_token",
                    "role": "agent",
                },
                "input_data": {},
            },
            headers=auth_headers,
        )
        # Returns 403 because RBAC check happens before existence check (more secure)
        assert response.status_code == 403


class TestWorkflowEndpoints:
    """Test workflow execution endpoints."""

    def test_workflow_weekly_vendor_report(self, client, auth_headers):
        """Test weekly_vendor_report workflow via API."""
        response = client.post(
            "/v1/workflows/weekly_vendor_report",
            json={"property_id": "prop_001"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["workflow_name"] == "weekly_vendor_report"

    def test_workflow_arrears_detection(self, client, auth_headers):
        """Test arrears_detection workflow via API."""
        response = client.post(
            "/v1/workflows/arrears_detection",
            json={"tenancy_id": "tenancy_001"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_workflow_not_found(self, client, auth_headers):
        """Test 404 for unknown workflow."""
        response = client.post(
            "/v1/workflows/nonexistent_workflow",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestResourceEndpoints:
    """Test resource retrieval endpoints."""

    def test_get_property_details(self, client, auth_headers):
        """Test property details resource retrieval."""
        response = client.get(
            "/v1/resources/vault://properties/prop_001/details",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_property_feedback(self, client, auth_headers):
        """Test property feedback resource retrieval."""
        response = client.get(
            "/v1/resources/vault://properties/prop_001/feedback",
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestPolicyEnforcement:
    """Test RBAC and policy enforcement via API."""

    def test_admin_tool_requires_admin_role(self, client, auth_headers):
        """Test that admin tools reject agent role."""
        # Agent trying to access admin tool
        response = client.post(
            "/v1/tools/prepare_breach_notice",
            json={
                "tool_name": "prepare_breach_notice",
                "context": {
                    "user_id": "test_user",
                    "tenant_id": "test_tenant",
                    "auth_context": "test_token",
                    "role": "agent",
                },
                "input_data": {"tenancy_id": "tenancy_001", "breach_type": "rent_arrears"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_missing_context_rejected(self, client, auth_headers):
        """Test that missing context fields are rejected."""
        response = client.post(
            "/v1/tools/analyze_open_home_feedback",
            json={
                "tool_name": "analyze_open_home_feedback",
                "context": {
                    "user_id": "",  # Empty user_id
                    "tenant_id": "test_tenant",
                    "auth_context": "test_token",
                },
                "input_data": {"property_id": "prop_001"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestConfiguration:
    """Test configuration loading for production."""

    def test_settings_load_from_env(self):
        """Test settings can be loaded from environment variables."""
        with patch.dict(
            os.environ,
            {
                "BEARER_TOKEN": "test-production-token",
                "MCP_SERVER_PORT": "9000",
                "DATABASE_PATH": "/tmp/test.db",
            },
        ):
            settings = Settings()
            assert settings.bearer_token == "test-production-token"
            assert settings.mcp_server_port == 9000
            assert settings.database_path == "/tmp/test.db"

    def test_production_defaults(self):
        """Test production-ready default values."""
        settings = Settings()
        assert settings.mcp_server_host == "0.0.0.0"
        assert settings.mcp_server_port == 8000
        assert settings.mcp_api_version == "v1"
        assert settings.hitl_enabled is True

    def test_feature_flags_default_to_safe(self):
        """Test feature flags default to safe MVP values."""
        settings = Settings()
        # These should be disabled by default for MVP
        assert settings.multi_tenant_enabled is False
        assert settings.production_integrations_enabled is False
        # Mocks should be enabled
        assert settings.vaultre_mock_enabled is True
        assert settings.ailo_mock_enabled is True


class TestDatabasePersistence:
    """Test database operations for production."""

    def test_database_schema_initialization(self):
        """Test database initializes with correct schema."""
        import tempfile
        from mcp.storage.database import Database

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            db = Database(db_path=f.name)

            # Verify tables exist
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = {row[0] for row in cursor.fetchall()}

            assert "tool_executions" in tables
            assert "workflow_executions" in tables
            assert "agent_manifests" in tables
            assert "audit_log" in tables

    def test_audit_log_persistence(self):
        """Test audit events are persisted correctly."""
        import tempfile
        from mcp.storage.database import Database

        with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
            db = Database(db_path=f.name)

            db.log_audit_event(
                correlation_id="test-123",
                event_type="test_event",
                user_id="user_1",
                tenant_id="tenant_1",
                tool_name="test_tool",
                action="test_action",
                policy_result="allowed",
            )

            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM audit_log")
                count = cursor.fetchone()[0]

            assert count == 1
