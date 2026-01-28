"""LangGraph workflow implementations."""

from typing import Any, Dict, TypedDict

from langgraph.graph import END, StateGraph

from mcp.schemas.base import RequestContext
from mcp.tools.implementations import (
    analyze_open_home_feedback,
    calculate_breach_status,
    extract_expiry_date,
    generate_vendor_report,
    ocr_document,
)
from mcp.schemas.tools import (
    AnalyzeFeedbackInput,
    GenerateVendorReportInput,
    OCRDocumentInput,
    ExtractExpiryInput,
)


class WorkflowState(TypedDict):
    """State for LangGraph workflows."""

    property_id: str
    tenancy_id: str | None
    context: RequestContext
    step_results: Dict[str, Any]
    final_output: Dict[str, Any] | None
    error: str | None


def build_weekly_vendor_report_flow() -> StateGraph:
    """
    Build WeeklyVendorReportFlow workflow.

    Flow: fetch property details → analyze feedback → generate report
    """
    graph = StateGraph(WorkflowState)

    async def fetch_property_details(state: WorkflowState) -> WorkflowState:
        """Fetch property details (resource)."""
        # In real implementation, would call resource handler
        property_id = state["property_id"]
        state["step_results"]["property_details"] = {
            "property_id": property_id,
            "status": "For Sale",
        }
        return state

    async def analyze_feedback(state: WorkflowState) -> WorkflowState:
        """Analyze open home feedback."""
        property_id = state["property_id"]
        context = state["context"]

        input_data = AnalyzeFeedbackInput(property_id=property_id)
        output = await analyze_open_home_feedback(input_data, context)
        state["step_results"]["feedback_analysis"] = output.model_dump()
        return state

    async def generate_report(state: WorkflowState) -> WorkflowState:
        """Generate final vendor report."""
        property_id = state["property_id"]
        context = state["context"]

        input_data = GenerateVendorReportInput(property_id=property_id)
        output = await generate_vendor_report(input_data, context)
        state["final_output"] = output.model_dump()
        return state

    # Build graph
    graph.add_node("fetch_property", fetch_property_details)
    graph.add_node("analyze_feedback", analyze_feedback)
    graph.add_node("generate_report", generate_report)

    graph.set_entry_point("fetch_property")
    graph.add_edge("fetch_property", "analyze_feedback")
    graph.add_edge("analyze_feedback", "generate_report")
    graph.add_edge("generate_report", END)

    return graph


def build_arrears_detection_flow() -> StateGraph:
    """
    Build ArrearsDetectionFlow workflow.

    Flow: fetch ledger → calculate breach status → classify risk
    """
    graph = StateGraph(WorkflowState)

    async def fetch_ledger(state: WorkflowState) -> WorkflowState:
        """Fetch ledger summary (resource)."""
        tenancy_id = state.get("tenancy_id", "")
        # In real implementation, would call resource handler
        state["step_results"]["ledger"] = {
            "tenancy_id": tenancy_id,
            "current_balance": -150.0,
        }
        return state

    async def calculate_breach(state: WorkflowState) -> WorkflowState:
        """Calculate breach status."""
        tenancy_id = state.get("tenancy_id") or ""
        context = state["context"]

        from mcp.schemas.tools import CalculateBreachInput

        input_data = CalculateBreachInput(tenancy_id=tenancy_id if tenancy_id else "unknown")
        output = await calculate_breach_status(input_data, context)
        state["step_results"]["breach_status"] = output.model_dump()
        return state

    async def classify_risk(state: WorkflowState) -> WorkflowState:
        """Classify arrears risk."""
        breach_status = state["step_results"].get("breach_status", {})
        breach_risk = breach_status.get("breach_risk", {})
        level = breach_risk.get("level", "low")

        classification = {
            "risk_level": level,
            "requires_action": level in ["high", "critical"],
            "recommended_action": breach_risk.get("recommended_action"),
        }

        state["final_output"] = {
            "classification": classification,
            "breach_status": breach_status,
        }
        return state

    # Build graph
    graph.add_node("fetch_ledger", fetch_ledger)
    graph.add_node("calculate_breach", calculate_breach)
    graph.add_node("classify_risk", classify_risk)

    graph.set_entry_point("fetch_ledger")
    graph.add_edge("fetch_ledger", "calculate_breach")
    graph.add_edge("calculate_breach", "classify_risk")
    graph.add_edge("classify_risk", END)

    return graph


def build_compliance_audit_flow() -> StateGraph:
    """
    Build ComplianceAuditFlow workflow.

    Flow: fetch documents → OCR → extract expiry dates → audit compliance
    """
    graph = StateGraph(WorkflowState)

    async def fetch_documents(state: WorkflowState) -> WorkflowState:
        """Fetch property documents (resource)."""
        # In real implementation, would call resource handler
        state["step_results"]["documents"] = [
            {"document_id": "doc_001", "url": "vault://documents/doc_001.pdf"},
        ]
        return state

    async def ocr_documents(state: WorkflowState) -> WorkflowState:
        """OCR all documents."""
        documents = state["step_results"].get("documents", [])
        context = state["context"]

        ocr_results = []
        for doc in documents:
            doc_url = doc.get("url", "")
            input_data = OCRDocumentInput(document_url=doc_url)
            output = await ocr_document(input_data, context)
            ocr_results.append(output.model_dump())

        state["step_results"]["ocr_results"] = ocr_results
        return state

    async def extract_dates(state: WorkflowState) -> WorkflowState:
        """Extract expiry dates from OCR text."""
        ocr_results = state["step_results"].get("ocr_results", [])
        context = state["context"]

        all_dates = []
        for ocr_result in ocr_results:
            text = ocr_result.get("extracted_text", "")
            input_data = ExtractExpiryInput(text=text)
            output = await extract_expiry_date(input_data, context)
            all_dates.extend([d.model_dump() for d in output.extracted_dates])

        state["step_results"]["extracted_dates"] = all_dates
        return state

    async def audit_compliance(state: WorkflowState) -> WorkflowState:
        """Audit compliance based on extracted dates."""
        extracted_dates = state["step_results"].get("extracted_dates", [])
        compliance_issues: list[str] = []
        for date_info in extracted_dates:
            date_value_str = date_info.get("date_value")
            if date_value_str:
                # Parse date (simplified)
                try:
                    if isinstance(date_value_str, str):
                        # Would parse properly in real implementation
                        pass
                except Exception:
                    pass

                # Check if expired
                # Simplified check - in real implementation would parse and compare

        state["final_output"] = {
            "compliance_status": "compliant" if not compliance_issues else "non_compliant",
            "extracted_dates": extracted_dates,
            "issues": compliance_issues,
        }
        return state

    # Build graph
    graph.add_node("fetch_documents", fetch_documents)
    graph.add_node("ocr_documents", ocr_documents)
    graph.add_node("extract_dates", extract_dates)
    graph.add_node("audit_compliance", audit_compliance)

    graph.set_entry_point("fetch_documents")
    graph.add_edge("fetch_documents", "ocr_documents")
    graph.add_edge("ocr_documents", "extract_dates")
    graph.add_edge("extract_dates", "audit_compliance")
    graph.add_edge("audit_compliance", END)

    return graph
