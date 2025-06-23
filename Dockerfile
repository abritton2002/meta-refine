# Meta-Refine Docker Image
# Multi-stage build for efficient container deployment

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    META_REFINE_CACHE_DIR="/app/cache" \
    META_REFINE_OUTPUT_DIR="/app/output"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash metarefine

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=metarefine:metarefine . .

# Create necessary directories
RUN mkdir -p /app/cache /app/output && \
    chown -R metarefine:metarefine /app

# Switch to non-root user
USER metarefine

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python meta_refine.py doctor || exit 1

# Default command
ENTRYPOINT ["python", "meta_refine.py"]
CMD ["--help"]

# Labels
LABEL org.opencontainers.image.title="Meta-Refine" \
      org.opencontainers.image.description="Intelligent code analysis with Meta's Llama 3.1" \
      org.opencontainers.image.vendor="Meta-Refine Team" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT" 