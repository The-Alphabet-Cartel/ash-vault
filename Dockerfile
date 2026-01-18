# ============================================================================
# Ash-Vault: Crisis Archive & Backup Infrastructure
# The Alphabet Cartel - https://discord.gg/alphabetcartel | alphabetcartel.org
# ============================================================================
#
# MISSION - NEVER TO BE VIOLATED:
#     Secure     → Encrypt sensitive session data with defense-in-depth layering
#     Archive    → Preserve crisis records in resilient object storage
#     Replicate  → Maintain backups across device, site, and cloud tiers
#     Protect    → Safeguard our LGBTQIA+ community through vigilant data guardianship
#
# ============================================================================
# Production Dockerfile - Backup Service
# ----------------------------------------------------------------------------
# FILE VERSION: v5.0-3-3.5a-2
# LAST MODIFIED: 2026-01-18
# PHASE: Phase 3 - Backup Infrastructure
# Repository: https://github.com/the-alphabet-cartel/ash-vault
# ============================================================================
#
# USAGE:
#   # Build the image
#   docker build -t ghcr.io/the-alphabet-cartel/ash-vault:latest .
#
#   # Run with docker compose (recommended)
#   docker compose up -d
#
# MULTI-STAGE BUILD:
#   Stage 1 (builder): Install dependencies
#   Stage 2 (runtime): Minimal production image
#
# ============================================================================

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim-trixie AS builder

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.11-slim-trixie AS runtime

# Labels
LABEL org.opencontainers.image.title="Ash-Vault" \
      org.opencontainers.image.description="Crisis Archive & Backup Infrastructure" \
      org.opencontainers.image.version="5.0.3" \
      org.opencontainers.image.vendor="The Alphabet Cartel" \
      org.opencontainers.image.source="https://github.com/the-alphabet-cartel/ash-vault" \
      org.opencontainers.image.licenses="MIT"

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    # Application settings
    VAULT_ENVIRONMENT=production \
    VAULT_LOG_LEVEL=INFO \
    TZ=America/Los_Angeles

# Install runtime dependencies
# Note: zfsutils-linux is in contrib repo, must enable it first
RUN echo "deb http://deb.debian.org/debian trixie contrib" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    openssh-client \
    rclone \
    zfsutils-linux \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY main.py .
COPY src/ ./src/

# Create logs directory
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:30886/health || exit 1

# Expose health endpoint port
EXPOSE 30886

# Run the backup service
CMD ["python", "main.py"]
