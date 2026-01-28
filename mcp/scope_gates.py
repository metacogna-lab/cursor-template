"""MVP scope gates to prevent use of excluded features."""

from mcp.config import settings


def check_multi_tenant_enabled() -> None:
    """Raise if multi-tenant is attempted but disabled."""
    if not settings.multi_tenant_enabled:
        raise NotImplementedError("Multi-tenant mode is not enabled in MVP")


def check_production_integrations() -> None:
    """Raise if production integrations are attempted but disabled."""
    if not settings.production_integrations_enabled:
        raise NotImplementedError(
            "Production VaultRE/Ailo integrations are not enabled in MVP. Use mock clients."
        )


def check_hitl_ui() -> None:
    """Raise if HITL UI is attempted (not in MVP)."""
    raise NotImplementedError(
        "HITL UI dashboard is not available in MVP. Use CLI token generation."
    )


def check_feature_flag(feature: str) -> None:
    """Check if a feature is enabled."""
    feature_map = {
        "multi_tenant": check_multi_tenant_enabled,
        "production_integrations": check_production_integrations,
        "hitl_ui": check_hitl_ui,
    }

    checker = feature_map.get(feature)
    if checker:
        checker()
    else:
        raise ValueError(f"Unknown feature flag: {feature}")
