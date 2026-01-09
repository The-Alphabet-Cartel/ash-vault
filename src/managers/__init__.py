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
Managers Package - Clean Architecture Factory Functions
----------------------------------------------------------------------------
FILE VERSION: v5.0-1-1.0-1
LAST MODIFIED: 2026-01-09
PHASE: Phase 1 - Foundation & Infrastructure
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================

This package provides factory functions for all managers following
Clean Architecture v5.2 Rule #1: Factory Function Pattern.

USAGE:
    from src.managers import (
        create_config_manager,
        create_secrets_manager,
        create_logging_config_manager,
    )

    # Initialize managers
    config = create_config_manager()
    secrets = create_secrets_manager()
    logging_mgr = create_logging_config_manager(config)
"""

# Configuration Manager
from src.managers.config_manager import (
    ConfigManager,
    create_config_manager,
)

# Secrets Manager
from src.managers.secrets_manager import (
    SecretsManager,
    create_secrets_manager,
    get_secrets_manager,
    get_secret,
    SecretNotFoundError,
)

# Logging Configuration Manager
from src.managers.logging_config_manager import (
    LoggingConfigManager,
    create_logging_config_manager,
)

# =============================================================================
# Export public interface
# =============================================================================

__all__ = [
    # Config Manager
    "ConfigManager",
    "create_config_manager",
    # Secrets Manager
    "SecretsManager",
    "create_secrets_manager",
    "get_secrets_manager",
    "get_secret",
    "SecretNotFoundError",
    # Logging Manager
    "LoggingConfigManager",
    "create_logging_config_manager",
]
