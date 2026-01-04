# =============================================================================
# Streamlit Dashboard - Production Dockerfile
# =============================================================================
# 2025 Best Practices:
# - Multi-stage build for smaller image
# - Non-root user for security
# - Minimal base image (Python slim)
# - Proper layer caching
# - Security hardening
# =============================================================================

# Stage 1: Builder
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
COPY requirements-streamlit.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements-streamlit.txt

# Stage 2: Runtime
FROM python:3.12-slim

# Set labels for metadata (2025 best practice)
LABEL maintainer="BMAD Memory Team"
LABEL description="Streamlit dashboard for BMAD memory intelligence"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user (2025 security best practice)
RUN groupadd -r streamlit && \
    useradd -r -g streamlit -u 1000 streamlit && \
    mkdir -p /app && \
    chown -R streamlit:streamlit /app

# Set working directory
WORKDIR /app

# Copy application files
COPY --chown=streamlit:streamlit . /app/

# Switch to non-root user
USER streamlit

# Expose Streamlit port
EXPOSE 8501

# Health check (2025 best practice)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
