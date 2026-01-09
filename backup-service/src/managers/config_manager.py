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
Configuration Manager - JSON + Environment Variable Configuration
----------------------------------------------------------------------------
FILE VERSION: v5.0-3-3.5-1
LAST MODIFIED: 2026-01-09
PHASE: Phase 3 - Backup Infrastructure
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================
"""

import json
import os
import logging
from typing import Any, Dict, Optional, Union
from pathlib import Path

__version__ = "v5.0-3-3.5-1"

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Configuration Manager for Ash-Vault Backup Service.
    
    Loads configuration from JSON files and applies environment variable overrides.
    """
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        Initialize ConfigManager.
        
        Args:
            config_dir: Path to configuration directory
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)
        
        self._config: Dict[str, Any] = {}
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load and resolve configuration."""
        config_file = self.config_dir / "default.json"
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                raw_config = json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            raw_config = self._get_defaults()
        
        # Resolve configuration
        for section, section_config in raw_config.items():
            if section.startswith("_") or not isinstance(section_config, dict):
                continue
            
            self._config[section] = {}
            defaults = section_config.get("defaults", {})
            
            for key, default_value in defaults.items():
                # Check for environment variable override
                env_ref = section_config.get(key, "")
                if isinstance(env_ref, str) and env_ref.startswith("${") and env_ref.endswith("}"):
                    env_var = env_ref[2:-1]
                    env_value = os.environ.get(env_var)
                    
                    if env_value is not None:
                        # Convert type based on default value type
                        if isinstance(default_value, bool):
                            self._config[section][key] = env_value.lower() in ("true", "1", "yes")
                        elif isinstance(default_value, int):
                            try:
                                self._config[section][key] = int(env_value)
                            except ValueError:
                                self._config[section][key] = default_value
                        else:
                            self._config[section][key] = env_value
                    else:
                        self._config[section][key] = default_value
                else:
                    self._config[section][key] = default_value
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Return emergency defaults if config file fails to load."""
        return {
            "server": {"defaults": {"host": "0.0.0.0", "port": 30886}},
            "logging": {"defaults": {"level": "INFO"}},
            "zfs": {"defaults": {"pool": "syn", "dataset": "syn/archives"}},
            "schedules": {"defaults": {
                "snapshot_daily": "0 3 * * *",
                "snapshot_weekly": "0 3 * * 0",
                "snapshot_monthly": "0 3 1 * *",
                "replication": "0 4 * * *",
                "cloud_sync": "0 5 * * 0"
            }},
            "retention": {"defaults": {"daily_count": 7, "weekly_count": 4, "monthly_count": 12}},
            "replication": {"defaults": {
                "lofn_host": "10.20.30.253",
                "lofn_dataset": "backup/ash-vault",
                "ssh_key": "/root/.ssh/id_ed25519_lofn"
            }},
            "cloud": {"defaults": {
                "b2_bucket": "ash-vault-backup-alphabetcartel",
                "minio_data_path": "/mnt/archives/minio-data",
                "rclone_remote": "b2"
            }},
            "alerting": {"defaults": {"enabled": True, "on_success": False, "on_failure": True}}
        }
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(section, {}).get(key, default)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section."""
        return self._config.get(section, {})


def create_config_manager(config_dir: Optional[Union[str, Path]] = None) -> ConfigManager:
    """
    Factory function for ConfigManager.
    
    Args:
        config_dir: Optional path to configuration directory
    
    Returns:
        ConfigManager instance
    """
    return ConfigManager(config_dir=config_dir)


__all__ = ["ConfigManager", "create_config_manager"]
