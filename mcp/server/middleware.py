"""FastAPI middleware for authentication and observability."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from opentelemetry import trace

from mcp.config import settings

tracer = trace.get_tracer(__name__)


async def authentication_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware to authenticate requests via bearer token."""
    # Skip auth for health/version/docs endpoints
    if request.url.path in ["/healthz", "/ready", "/version", "/docs", "/openapi.json", "/metrics"]:
        return await call_next(request)

    # Check bearer token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Missing or invalid Authorization header"},
        )

    token = auth_header.replace("Bearer ", "")
    if token != settings.bearer_token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid bearer token"},
        )

    return await call_next(request)


async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware to add correlation ID to requests."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


async def observability_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware for observability (tracing, timing)."""
    start_time = time.time()

    # Get correlation_id (set by request_id_middleware)
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    # Create trace span if OpenTelemetry enabled
    if settings.opentelemetry_enabled:
        with tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("correlation_id", correlation_id)

            response = await call_next(request)

            duration_ms = (time.time() - start_time) * 1000
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("duration_ms", duration_ms)

            response.headers["X-Request-Duration-Ms"] = str(duration_ms)
            return response
    else:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        response.headers["X-Request-Duration-Ms"] = str(duration_ms)
        return response
