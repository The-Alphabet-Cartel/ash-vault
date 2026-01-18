"""
============================================================================
Ash-Vault: Crisis Archive & Backup Infrastructure
The Alphabet Cartel - https://discord.gg/alphabetcartel | alphabetcartel.org
============================================================================

MISSION - NEVER TO BE VIOLATED:
    Secure     → Encrypt sensitive session data with defense-in-depth layering
    Archive    → Preserve crisis records in resilient object storage
    Replicate  → Maintain backups across device, site, and cloud tiers
    Protect    → Safeguard our LGBTQIA+ community through vigilant data guardianship

============================================================================
API Package - FastAPI Health and Status Endpoints
----------------------------------------------------------------------------
FILE VERSION: v5.0-3-3.5a-1
LAST MODIFIED: 2026-01-09
PHASE: Phase 3 - Backup Infrastructure
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================

This package provides FastAPI endpoints for health monitoring and status.

USAGE:
    from src.api import create_app

    # Create FastAPI application
    app = create_app(config_manager, logging_manager, scheduler)
"""

# Health API
from src.api.health import (
    create_app,
    router as health_router,
)

# =============================================================================
# Export public interface
# =============================================================================

__all__ = [
    "create_app",
    "health_router",
]
