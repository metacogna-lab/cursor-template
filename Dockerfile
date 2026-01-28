# Dockerfile for Tenure MCP Server
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Production image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY mcp/ ./mcp/
COPY backend/ ./backend/

# Create data directory for SQLite with proper permissions
RUN mkdir -p /app/data && chmod 755 /app/data

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port (Railway uses $PORT)
EXPOSE 8000

# Health check using curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/healthz || exit 1

# Run the server - Railway provides $PORT
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
