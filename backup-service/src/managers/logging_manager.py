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
Logging Manager - Structured Logging Configuration
----------------------------------------------------------------------------
FILE VERSION: v5.0-3-3.5-1
LAST MODIFIED: 2026-01-09
PHASE: Phase 3 - Backup Infrastructure
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================
"""

import logging
import sys
from typing import Optional

__version__ = "v5.0-3-3.5-1"


class LoggingManager:
    """
    Logging Manager for Ash-Vault Backup Service.
    
    Provides consistent, colorized logging across all modules.
    """
    
    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m"
    }
    
    def __init__(self, config_manager):
        """
        Initialize LoggingManager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self._configured = False
        self._configure_logging()
    
    def _configure_logging(self) -> None:
        """Configure the logging system."""
        if self._configured:
            return
        
        log_config = self.config_manager.get_section("logging")
        level_str = log_config.get("level", "INFO")
        level = getattr(logging, level_str.upper(), logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Create console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        
        # Reduce noise from third-party libraries
        logging.getLogger("apscheduler").setLevel(logging.WARNING)
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        
        self._configured = True
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name (usually __name__)
        
        Returns:
            Configured Logger instance
        """
        return logging.getLogger(name)


def create_logging_manager(config_manager) -> LoggingManager:
    """
    Factory function for LoggingManager.
    
    Args:
        config_manager: Configuration manager instance
    
    Returns:
        LoggingManager instance
    """
    return LoggingManager(config_manager)


__all__ = ["LoggingManager", "create_logging_manager"]
