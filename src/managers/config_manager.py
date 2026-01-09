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
Configuration Manager - JSON + Environment Variable Configuration System
----------------------------------------------------------------------------
FILE VERSION: v5.0-1-1.0-1
LAST MODIFIED: 2026-01-09
PHASE: Phase 1 - Foundation & Infrastructure
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================

RESPONSIBILITIES:
- Load JSON configuration files (default.json, production.json, testing.json)
- Apply environment variable overrides
- Validate configuration values against schemas
- Provide safe fallbacks for invalid/missing values (Rule #5)
- Support multiple environments (production, testing, development)
"""

import json
import os
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

# Module version
__version__ = "v5.0-1-1.0-1"

# Initialize logger
logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Configuration Manager for Ash-Vault Backup Service.

    Implements Clean Architecture v5.2 principles:
    - Factory function pattern (create_config_manager)
    - JSON configuration with environment variable overrides
    - Resilient validation with safe fallbacks
    - Comprehensive logging for debugging

    Attributes:
        config_dir: Path to configuration directory
        environment: Current environment (production, testing, development)
        config: Resolved configuration dictionary
    """

    # Supported environments
    ENVIRONMENTS = ["production", "testing", "development"]

    # Default configuration file
    DEFAULT_CONFIG = "default.json"

    def __init__(
        self,
        config_dir: Optional[Union[str, Path]] = None,
        environment: str = "production",
    ):
        """
        Initialize ConfigManager with configuration directory and environment.

        Args:
            config_dir: Path to configuration directory (default: ./config)
            environment: Environment name (production, testing, development)

        Note:
            Use create_config_manager() factory function instead of direct instantiation.
        """
        # Set configuration directory
        if config_dir is None:
            # Default to ./config relative to project root
            self.config_dir = Path(__file__).parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)

        # Validate environment
        if environment not in self.ENVIRONMENTS:
            logger.warning(
                f"⚠️ Unknown environment '{environment}', falling back to 'production'"
            )
            environment = "production"

        self.environment = environment

        # Initialize configuration storage
        self._raw_config: Dict[str, Any] = {}
        self._resolved_config: Dict[str, Any] = {}
        self._validation_errors: List[str] = []

        # Load and resolve configuration
        self._load_configuration()

        logger.info(
            f"✅ ConfigManager v{__version__} initialized "
            f"(environment: {self.environment})"
        )

    def _load_configuration(self) -> None:
        """
        Load configuration from JSON files and apply environment overrides.

        Load order:
        1. Load default.json (base configuration)
        2. Load {environment}.json (environment overrides)
        3. Apply environment variable overrides
        4. Validate all values
        """
        logger.info(f"📂 Loading configuration from: {self.config_dir}")

        # Step 1: Load default configuration
        default_path = self.config_dir / self.DEFAULT_CONFIG
        self._raw_config = self._load_json_file(default_path)

        if not self._raw_config:
            logger.error(f"❌ Failed to load default configuration: {default_path}")
            self._raw_config = self._get_emergency_defaults()

        # Step 2: Load environment-specific overrides
        env_path = self.config_dir / f"{self.environment}.json"
        if env_path.exists():
            env_config = self._load_json_file(env_path)
            if env_config:
                self._merge_config(env_config)
                logger.info(f"📝 Applied {self.environment} overrides")
        else:
            logger.debug(f"No environment config found: {env_path}")

        # Step 3: Apply environment variable overrides
        self._apply_env_overrides()

        # Step 4: Resolve and validate configuration
        self._resolve_configuration()

    def _load_json_file(self, path: Path) -> Dict[str, Any]:
        """
        Load JSON file with error handling.

        Args:
            path: Path to JSON file

        Returns:
            Parsed JSON as dictionary, empty dict on failure
        """
        try:
            if not path.exists():
                logger.warning(f"⚠️ Config file not found: {path}")
                return {}

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.debug(f"📄 Loaded: {path}")
                return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in {path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Error loading {path}: {e}")
            return {}

    def _merge_config(self, override_config: Dict[str, Any]) -> None:
        """
        Merge override configuration into raw config.

        Only merges non-metadata sections and preserves defaults structure.

        Args:
            override_config: Configuration overrides to apply
        """
        for section, values in override_config.items():
            # Skip metadata
            if section.startswith("_"):
                continue

            if section in self._raw_config:
                if isinstance(values, dict) and isinstance(
                    self._raw_config[section], dict
                ):
                    # Merge section values
                    for key, value in values.items():
                        if key not in ("defaults", "validation", "description"):
                            self._raw_config[section][key] = value
                            logger.debug(f"  Override: {section}.{key} = {value}")
            else:
                # Add new section
                self._raw_config[section] = values

    def _apply_env_overrides(self) -> None:
        """
        Apply environment variable overrides to configuration.

        Scans configuration for ${ENV_VAR} patterns and replaces
        with actual environment variable values.
        """
        override_count = 0

        for section, section_config in self._raw_config.items():
            if section.startswith("_") or not isinstance(section_config, dict):
                continue

            for key, value in section_config.items():
                if key in ("defaults", "validation", "description"):
                    continue

                if (
                    isinstance(value, str)
                    and value.startswith("${")
                    and value.endswith("}")
                ):
                    env_var = value[2:-1]  # Extract VAR from ${VAR}
                    env_value = os.environ.get(env_var)

                    if env_value is not None:
                        # Get expected type from validation schema
                        expected_type = self._get_expected_type(section, key)
                        converted_value = self._convert_type(env_value, expected_type)

                        self._raw_config[section][key] = converted_value
                        override_count += 1
                        logger.debug(
                            f"  ENV override: {env_var} -> {section}.{key} = {converted_value}"
                        )

        if override_count > 0:
            logger.info(f"🔧 Applied {override_count} environment variable overrides")

    def _get_expected_type(self, section: str, key: str) -> str:
        """
        Get expected type for a configuration value from validation schema.

        Args:
            section: Configuration section name
            key: Configuration key name

        Returns:
            Type string (string, integer, float, boolean, list)
        """
        try:
            validation = self._raw_config.get(section, {}).get("validation", {})
            key_validation = validation.get(key, {})
            return key_validation.get("type", "string")
        except Exception:
            return "string"

    def _convert_type(self, value: str, expected_type: str) -> Any:
        """
        Convert string value to expected type.

        Args:
            value: String value to convert
            expected_type: Target type (string, integer, float, boolean, list)

        Returns:
            Converted value, original string on failure
        """
        try:
            if expected_type == "integer":
                return int(value)
            elif expected_type == "float":
                return float(value)
            elif expected_type == "boolean":
                return value.lower() in ("true", "1", "yes", "on")
            elif expected_type == "list":
                return json.loads(value) if isinstance(value, str) else value
            else:
                return value
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(
                f"⚠️ Type conversion failed for '{value}' -> {expected_type}: {e}"
            )
            return value

    def _resolve_configuration(self) -> None:
        """
        Resolve final configuration values with validation.

        For each setting:
        1. Check if explicit value is set
        2. Fall back to defaults if not set
        3. Validate against schema
        4. Use default on validation failure
        """
        self._resolved_config = {}

        for section, section_config in self._raw_config.items():
            if section.startswith("_") or not isinstance(section_config, dict):
                continue

            self._resolved_config[section] = {}
            defaults = section_config.get("defaults", {})
            validation = section_config.get("validation", {})

            for key, default_value in defaults.items():
                # Get current value (may be env override or default reference)
                current_value = section_config.get(key)

                # If still a ${VAR} reference, use default
                if isinstance(current_value, str) and current_value.startswith("${"):
                    current_value = default_value

                # If None or not set, use default
                if current_value is None:
                    current_value = default_value

                # Validate value
                key_validation = validation.get(key, {})
                if key_validation:
                    is_valid, validated_value = self._validate_value(
                        current_value, key_validation, default_value
                    )
                    if not is_valid:
                        self._validation_errors.append(
                            f"{section}.{key}: Invalid value '{current_value}', "
                            f"using default '{default_value}'"
                        )
                    current_value = validated_value

                self._resolved_config[section][key] = current_value

        # Log validation errors (but don't crash - Rule #5)
        if self._validation_errors:
            logger.warning(
                f"⚠️ {len(self._validation_errors)} validation issues resolved with defaults:"
            )
            for error in self._validation_errors:
                logger.warning(f"  - {error}")

    def _validate_value(
        self, value: Any, validation: Dict[str, Any], default: Any
    ) -> tuple[bool, Any]:
        """
        Validate a configuration value against its schema.

        Args:
            value: Value to validate
            validation: Validation schema
            default: Default value to use on failure

        Returns:
            Tuple of (is_valid, validated_or_default_value)
        """
        expected_type = validation.get("type", "string")

        # Type check
        type_valid = self._check_type(value, expected_type)
        if not type_valid:
            logger.debug(f"Type mismatch: {value} is not {expected_type}")
            return False, default

        # Range check (for numeric types)
        if "range" in validation and expected_type in ("integer", "float"):
            min_val, max_val = validation["range"]
            if not (min_val <= value <= max_val):
                logger.debug(f"Range violation: {value} not in [{min_val}, {max_val}]")
                return False, default

        # Allowed values check (for strings)
        if "allowed_values" in validation and expected_type == "string":
            if value not in validation["allowed_values"]:
                logger.debug(
                    f"Value not allowed: {value} not in {validation['allowed_values']}"
                )
                return False, default

        return True, value

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """
        Check if value matches expected type.

        Args:
            value: Value to check
            expected_type: Expected type string

        Returns:
            True if type matches
        """
        type_map = {
            "string": str,
            "integer": int,
            "float": (int, float),  # Accept int as float
            "boolean": bool,
            "list": (list, tuple),
        }

        expected = type_map.get(expected_type)
        if expected is None:
            return True  # Unknown type, accept anything

        return isinstance(value, expected)

    def _get_emergency_defaults(self) -> Dict[str, Any]:
        """
        Return emergency fallback configuration if all else fails.

        This ensures the system can start even without configuration files.
        Rule #5: Operational continuity for backup service.

        Returns:
            Minimal working configuration for Ash-Vault
        """
        logger.warning("🚨 Using emergency fallback configuration!")

        return {
            "server": {
                "defaults": {
                    "host": "0.0.0.0",
                    "port": 30886,
                    "debug": False,
                }
            },
            "logging": {
                "defaults": {
                    "level": "INFO",
                    "format": "human",
                    "file": "/app/logs/ash-vault.log",
                    "console": True,
                }
            },
            "minio": {
                "defaults": {
                    "endpoint": "localhost",
                    "port": 30884,
                    "secure": False,
                }
            },
            "buckets": {
                "defaults": {
                    "archives": "ash-archives",
                    "documents": "ash-documents",
                    "exports": "ash-exports",
                }
            },
            "zfs": {
                "defaults": {
                    "pool": "syn",
                    "dataset": "syn/archives",
                    "mountpoint": "/mnt/archives",
                }
            },
            "backup_schedules": {
                "defaults": {
                    "snapshot_daily": "0 3 * * *",
                    "snapshot_weekly": "0 3 * * 0",
                    "snapshot_monthly": "0 3 1 * *",
                    "replication_lofn": "0 4 * * *",
                    "sync_b2": "0 5 * * 0",
                }
            },
            "retention": {
                "defaults": {
                    "daily_count": 7,
                    "weekly_count": 4,
                    "monthly_count": 12,
                }
            },
            "replication": {
                "defaults": {
                    "lofn_host": "10.20.30.253",
                    "lofn_dataset": "backup/ash-vault",
                    "ssh_key_path": "/root/.ssh/id_ed25519_lofn",
                }
            },
            "b2": {
                "defaults": {
                    "enabled": True,
                    "bucket": "ash-vault-backup",
                }
            },
            "alerting": {
                "defaults": {
                    "enabled": True,
                    "on_backup_success": False,
                    "on_backup_failure": True,
                }
            },
        }

    # =========================================================================
    # PUBLIC API - Getter Methods
    # =========================================================================

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            section: Configuration section (e.g., "server", "logging")
            key: Configuration key within section
            default: Default value if not found

        Returns:
            Configuration value or default
        """
        try:
            return self._resolved_config.get(section, {}).get(key, default)
        except Exception:
            return default

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.

        Args:
            section: Section name

        Returns:
            Section dictionary or empty dict
        """
        return self._resolved_config.get(section, {})

    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration."""
        return self.get_section("server")

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get_section("logging")

    def get_minio_config(self) -> Dict[str, Any]:
        """Get MinIO configuration."""
        return self.get_section("minio")

    def get_buckets_config(self) -> Dict[str, Any]:
        """Get bucket names configuration."""
        return self.get_section("buckets")

    def get_zfs_config(self) -> Dict[str, Any]:
        """Get ZFS configuration."""
        return self.get_section("zfs")

    def get_backup_schedules_config(self) -> Dict[str, Any]:
        """Get backup schedules configuration."""
        return self.get_section("backup_schedules")

    def get_retention_config(self) -> Dict[str, Any]:
        """Get retention policy configuration."""
        return self.get_section("retention")

    def get_replication_config(self) -> Dict[str, Any]:
        """Get replication configuration."""
        return self.get_section("replication")

    def get_b2_config(self) -> Dict[str, Any]:
        """Get Backblaze B2 configuration."""
        return self.get_section("b2")

    def get_alerting_config(self) -> Dict[str, Any]:
        """Get alerting configuration."""
        return self.get_section("alerting")

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_environment(self) -> str:
        """Get current environment name."""
        return self.environment

    def get_validation_errors(self) -> List[str]:
        """Get list of validation errors encountered during loading."""
        return self._validation_errors.copy()

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == "testing"

    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.get("server", "debug", False)

    def to_dict(self) -> Dict[str, Any]:
        """
        Export resolved configuration as dictionary.

        Returns:
            Complete resolved configuration
        """
        return self._resolved_config.copy()

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"ConfigManager(environment='{self.environment}', "
            f"config_dir='{self.config_dir}')"
        )


# =============================================================================
# FACTORY FUNCTION - Clean Architecture v5.2 Compliance (Rule #1)
# =============================================================================


def create_config_manager(
    config_dir: Optional[Union[str, Path]] = None,
    environment: Optional[str] = None,
) -> ConfigManager:
    """
    Factory function for ConfigManager (Clean Architecture v5.2 Pattern).

    This is the ONLY way to create a ConfigManager instance.
    Direct instantiation should be avoided in production code.

    Args:
        config_dir: Path to configuration directory (default: auto-detect)
        environment: Environment name (default: from VAULT_ENVIRONMENT or 'production')

    Returns:
        Configured ConfigManager instance

    Example:
        >>> config = create_config_manager()
        >>> config = create_config_manager(environment="testing")
        >>> config = create_config_manager(config_dir="/custom/path")
    """
    # Determine environment from env var if not specified
    if environment is None:
        environment = os.environ.get("VAULT_ENVIRONMENT", "production")

    logger.info(f"🏭 Creating ConfigManager (environment: {environment})")

    return ConfigManager(config_dir=config_dir, environment=environment)


# =============================================================================
# Export public interface
# =============================================================================

__all__ = ["ConfigManager", "create_config_manager"]
