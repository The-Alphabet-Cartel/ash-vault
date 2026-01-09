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
# Backup Service Dockerfile
# ----------------------------------------------------------------------------
# FILE VERSION: v5.0-3-3.5-1
# LAST MODIFIED: 2026-01-09
# PHASE: Phase 3 - Backup Infrastructure
# CLEAN ARCHITECTURE: Compliant
# Repository: https://github.com/the-alphabet-cartel/ash-vault
# ============================================================================

FROM python:3.11-slim-bookworm

# Set labels
LABEL maintainer="The Alphabet Cartel <https://discord.gg/alphabetcartel>"
LABEL description="Ash-Vault Backup Service - Automated backup orchestration"
LABEL version="5.0.3"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/Los_Angeles \
    VAULT_ENVIRONMENT=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    openssh-client \
    rclone \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN python3.11 -m pip install --no-cache-dir --upgrade pip && \
    python3.11 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config/ ./config/
COPY src/ ./src/

# Create logs directory
RUN mkdir -p /app/logs

# Create non-root user for security (optional, but we need root for ZFS)
# For now, running as root since we need ZFS access

# Expose health endpoint port
EXPOSE 30886

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:30886/health || exit 1

# Run the application
CMD ["python3.11", "-m", "src.main"]
