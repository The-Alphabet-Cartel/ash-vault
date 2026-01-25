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
# FILE VERSION: v5.0-4-1.0-1
# LAST MODIFIED: 2026-01-22
# PHASE: Phase 4 - PUID/PGID Standardization
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
# CLEAN ARCHITECTURE COMPLIANCE:
#   - Uses python3.11 -m pip (Rule #10)
#   - Pure Python entrypoint for PUID/PGID (Rule #13)
#   - tini for PID 1 signal handling
#
# ============================================================================

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.12-slim AS builder

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
FROM python:3.12-slim AS runtime

# Labels
LABEL maintainer="PapaBearDoes <github.com/PapaBearDoes>"
LABEL org.opencontainers.image.title="Ash-NLP"
LABEL org.opencontainers.image.description="Crisis Archive & Backup Infrastructure"
LABEL org.opencontainers.image.version="5.0.0"
LABEL org.opencontainers.image.vendor="The Alphabet Cartel"
LABEL org.opencontainers.image.url="https://github.com/the-alphabet-cartel/ash-nlp"
LABEL org.opencontainers.image.source="https://github.com/the-alphabet-cartel/ash-nlp"

# Default user/group IDs (can be overridden at runtime via PUID/PGID)
ARG DEFAULT_UID=1000
ARG DEFAULT_GID=1000

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    PATH="/opt/venv/bin:$PATH" \
    # Application settings
    VAULT_ENVIRONMENT=production \
    VAULT_LOG_LEVEL=INFO \
    TZ=America/Los_Angeles \
    # Default PUID/PGID (LinuxServer.io style)
    PUID=${DEFAULT_UID} \
    PGID=${DEFAULT_GID}

# Install runtime dependencies
# Note: zfsutils-linux is in contrib repo, must enable it first
RUN echo "deb http://deb.debian.org/debian trixie contrib" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tini \
    openssh-client \
    rclone \
    zfsutils-linux \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR ${APP_HOME}

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY main.py .
COPY src/ ./src/

# Copy and set up entrypoint script (Rule #13: Pure Python PUID/PGID handling)
COPY docker-entrypoint.py ${APP_HOME}/docker-entrypoint.py
RUN chmod +x ${APP_HOME}/docker-entrypoint.py

# Create default user/group (will be modified at runtime by entrypoint)
RUN groupadd -g ${PGID} ash-vault \
    && useradd -m -u ${PUID} -g ${PGID} ash-vault

# Create logs directory (entrypoint will fix ownership at runtime)
RUN mkdir -p ${APP_HOME}/logs \
    && chmod 755 ${APP_HOME}/logs \
    && chown -R ${PUID}:${PGID} ${APP_HOME}/logs

# NOTE: We do NOT switch to USER vault here!
# The entrypoint script handles user switching at runtime after fixing permissions.
# This allows PUID/PGID to work correctly with mounted volumes.

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:30886/health || exit 1

# Expose health endpoint port
EXPOSE 30886

# Use tini as init system for proper signal handling
# Then our Python entrypoint for PUID/PGID handling (Rule #13)
ENTRYPOINT ["/usr/bin/tini", "--", "python", "/app/docker-entrypoint.py"]

# Default command (passed to docker-entrypoint.py)
CMD ["python", "main.py"]
