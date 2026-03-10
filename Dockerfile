# ============================================
# Stage 1: Builder (Alpine-based for musl libc compatibility)
# ============================================
FROM python:3.11-alpine AS builder

WORKDIR /build

# Install build dependencies including Rust/Cargo for cryptography
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust

# Copy requirements and install dependencies to a venv
COPY requirements.txt ./
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir --no-binary cryptography -r requirements.txt

# Copy application code
COPY lakeventory ./lakeventory
COPY setup.py pyproject.toml ./

# Install application (not editable - for container portability)
RUN /opt/venv/bin/pip install --no-cache-dir .

# ============================================
# Stage 2: Runtime (Minimal)
# ============================================
FROM python:3.11-alpine AS runtime

# Install runtime dependencies only
RUN apk add --no-cache \
    libstdc++ \
    libgcc \
    libffi \
    openssl \
    ca-certificates

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application files
COPY --from=builder /build/lakeventory ./lakeventory
COPY docs ./docs
COPY README.md LICENSE* ./
COPY scripts/run_scheduled.sh /app/run_scheduled.sh

RUN chmod +x /app/run_scheduled.sh

# Use venv Python
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=300s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import lakeventory; print('OK')" || exit 1

# Non-root user for security
RUN addgroup -g 1000 lakeventory && \
    adduser -D -u 1000 -G lakeventory lakeventory && \
    chown -R lakeventory:lakeventory /app

USER lakeventory

# Monte .lakeventory/config.yaml aqui em runtime:
#   docker run -v $(pwd)/.lakeventory:/app/.lakeventory:ro ...
VOLUME /app/.lakeventory

ENTRYPOINT ["/app/run_scheduled.sh"]
