"""Resource implementations for MCP Server."""

import asyncio
from typing import Any, Dict

from mcp.schemas.base import RequestContext

# Mock data for MVP
MOCK_PROPERTY_DETAILS = {
    "prop_001": {
        "property_id": "prop_001",
        "address": "123 Main Street, Brisbane QLD 4000",
        "property_type": "House",
        "bedrooms": 3,
        "bathrooms": 2,
        "price": 650000,
        "status": "For Sale",
        "listed_date": "2025-01-15",
    }
}

MOCK_PROPERTY_FEEDBACK = {
    "prop_001": [
        {
            "feedback_id": "fb_001",
            "date": "2025-01-20",
            "comment": "Great location, love the neighborhood",
            "sentiment": "positive",
        },
        {
            "feedback_id": "fb_002",
            "date": "2025-01-21",
            "comment": "Kitchen needs updating",
            "sentiment": "neutral",
        },
    ]
}

MOCK_LEDGER_SUMMARY = {
    "tenancy_001": {
        "tenancy_id": "tenancy_001",
        "property_id": "prop_001",
        "current_balance": -150.0,
        "last_payment_date": "2025-01-10",
        "next_payment_due": "2025-02-10",
        "rent_amount": 500.0,
        "status": "active",
    }
}


async def get_property_details_resource(
    property_id: str, context: RequestContext
) -> Dict[str, Any]:
    """
    Get property details resource.

    URI: vault://properties/{id}/details
    """
    # Simulate latency
    await asyncio.sleep(0.1)

    # Return mock data (PII should be redacted by policy gateway)
    return MOCK_PROPERTY_DETAILS.get(property_id, {})


async def get_property_feedback_resource(
    property_id: str, context: RequestContext
) -> Dict[str, Any]:
    """
    Get property feedback resource.

    URI: vault://properties/{id}/feedback
    """
    # Simulate latency
    await asyncio.sleep(0.1)

    return {
        "property_id": property_id,
        "feedback_entries": MOCK_PROPERTY_FEEDBACK.get(property_id, []),
    }


async def get_ledger_summary_resource(tenancy_id: str, context: RequestContext) -> Dict[str, Any]:
    """
    Get ledger summary resource.

    URI: ailo://ledgers/{tenancy_id}/summary
    """
    # Simulate latency
    await asyncio.sleep(0.1)

    return MOCK_LEDGER_SUMMARY.get(tenancy_id, {})


async def get_property_documents_resource(
    property_id: str, context: RequestContext
) -> Dict[str, Any]:
    """
    Get property documents resource.

    URI: vault://properties/{id}/documents
    """
    # Simulate latency
    await asyncio.sleep(0.1)

    return {
        "property_id": property_id,
        "documents": [
            {
                "document_id": "doc_001",
                "document_type": "contract",
                "url": "vault://documents/doc_001.pdf",
                "uploaded_date": "2025-01-15",
            },
            {
                "document_id": "doc_002",
                "document_type": "certificate",
                "url": "vault://documents/doc_002.pdf",
                "uploaded_date": "2025-01-20",
            },
        ],
    }
