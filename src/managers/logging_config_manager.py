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
Logging Configuration Manager - Colorized, structured logging system
----------------------------------------------------------------------------
FILE VERSION: v5.0-1-1.0-1
LAST MODIFIED: 2026-01-03
PHASE: Phase 1 - Foundation & Infrastructure
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================

RESPONSIBILITIES:
- Configure colorized console logging for human readability
- Support JSON format for production log aggregation
- Provide consistent log formatting across all modules
- Enable log level filtering via configuration
- Create child loggers for component isolation
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Module version
__version__ = "v5.0-1-1.2-2"


# =============================================================================
# ANSI Color Codes for Terminal Output
# =============================================================================


class Colors:
    """ANSI color codes for terminal output."""

    # Reset
    RESET = "\033[0m"

    # Regular colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"


# =============================================================================
# Custom Formatters
# =============================================================================


class ColorizedFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log output based on level.

    Color scheme:
    - DEBUG:    Cyan (detailed information for debugging)
    - INFO:     Green (general operational messages)
    - WARNING:  Yellow (potential issues, non-critical)
    - ERROR:    Red (errors that need attention)
    - CRITICAL: Magenta + Bold (system failures)
    """

    # Log level colors
    LEVEL_COLORS = {
        logging.DEBUG: Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: f"{Colors.BOLD}{Colors.MAGENTA}",
    }

    # Log level symbols for quick visual identification
    LEVEL_SYMBOLS = {
        logging.DEBUG: "🔍",
        logging.INFO: "✅",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "🚨",
    }

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        use_colors: bool = True,
        use_symbols: bool = True,
    ):
        """
        Initialize the colorized formatter.

        Args:
            fmt: Log message format string
            datefmt: Date format string
            use_colors: Whether to use ANSI colors
            use_symbols: Whether to use emoji symbols
        """
        if fmt is None:
            fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"

        super().__init__(fmt, datefmt)
        self.use_colors = use_colors
        self.use_symbols = use_symbols

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with colors and symbols.

        Args:
            record: The log record to format

        Returns:
            Formatted log string
        """
        # Get color and symbol for this level
        color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)
        symbol = self.LEVEL_SYMBOLS.get(record.levelno, "")

        # Save original values
        original_levelname = record.levelname
        original_msg = record.msg

        # Apply formatting
        if self.use_colors:
            record.levelname = f"{color}{record.levelname}{Colors.RESET}"
            record.msg = f"{color}{record.msg}{Colors.RESET}"

        if self.use_symbols and symbol:
            record.msg = (
                f"{symbol} {original_msg if not self.use_colors else record.msg}"
            )

        # Format the record
        result = super().format(record)

        # Restore original values
        record.levelname = original_levelname
        record.msg = original_msg

        return result


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs logs as JSON for production log aggregation.

    Useful for:
    - Log aggregation systems (ELK, Loki, etc.)
    - Structured log analysis
    - Production environments
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON-formatted log string
        """
        import json

        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        return json.dumps(log_data)


# =============================================================================
# Logging Configuration Manager
# =============================================================================


class LoggingConfigManager:
    """
    Manages logging configuration for Ash-Dash.

    Provides:
    - Colorized console output for human readability
    - JSON format option for production
    - File logging with rotation
    - Child logger creation for components
    - Consistent formatting across the application

    Example:
        >>> logging_manager = create_logging_config_manager(config_manager)
        >>> logger = logging_manager.get_logger("my_module")
        >>> logger.info("Application started")
    """

    def __init__(
        self,
        config_manager: Optional[Any] = None,
        log_level: str = "INFO",
        log_format: str = "human",
        log_file: Optional[str] = None,
        console_output: bool = True,
    ):
        """
        Initialize the LoggingConfigManager.

        Args:
            config_manager: ConfigManager instance for loading settings
            log_level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Output format ('human' for colorized, 'json' for structured)
            log_file: Path to log file (optional)
            console_output: Whether to output to console
        """
        # Store configuration
        self._config_manager = config_manager
        self._log_level = log_level
        self._log_format = log_format
        self._log_file = log_file
        self._console_output = console_output

        # Load from config manager if provided
        if config_manager:
            self._load_from_config()

        # Track configured loggers
        self._configured_loggers: Dict[str, logging.Logger] = {}

        # Configure root logger
        self._configure_root_logger()

        # Create our own logger
        self._logger = self.get_logger("LoggingConfigManager")
        self._logger.info(f"LoggingConfigManager {__version__} initialized")
        self._logger.debug(f"Log level: {self._log_level}, Format: {self._log_format}")

    def _load_from_config(self) -> None:
        """Load logging settings from ConfigManager."""
        if not self._config_manager:
            return

        try:
            logging_config = self._config_manager.get_section("logging")

            self._log_level = logging_config.get("level", self._log_level)
            self._log_format = logging_config.get("format", self._log_format)
            self._log_file = logging_config.get("file", self._log_file)
            self._console_output = logging_config.get("console", self._console_output)

        except Exception as e:
            # Fall back to defaults if config loading fails
            print(f"Warning: Failed to load logging config: {e}")

    def _configure_root_logger(self) -> None:
        """Configure the root logger with handlers."""
        # Get root logger
        root_logger = logging.getLogger()

        # Set level
        numeric_level = getattr(logging, self._log_level.upper(), logging.INFO)
        root_logger.setLevel(numeric_level)

        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()

        # Add console handler if enabled
        if self._console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(numeric_level)

            if self._log_format == "json":
                console_handler.setFormatter(JSONFormatter())
            else:
                # Use colorized formatter for human-readable output
                # Detect if we're in a TTY for color support
                use_colors = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
                console_handler.setFormatter(
                    ColorizedFormatter(use_colors=use_colors, use_symbols=True)
                )

            root_logger.addHandler(console_handler)

        # Add file handler if configured
        if self._log_file:
            self._add_file_handler(root_logger, self._log_file)

        # Reduce noise from third-party libraries
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    def _add_file_handler(
        self,
        logger: logging.Logger,
        file_path: str,
    ) -> None:
        """
        Add a file handler to the logger.

        Args:
            logger: Logger to add handler to
            file_path: Path to log file
        """
        try:
            # Ensure directory exists
            log_path = Path(file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Create file handler
            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)  # Capture all levels to file

            # Always use JSON format for file logs (easier to parse)
            file_handler.setFormatter(JSONFormatter())

            logger.addHandler(file_handler)

        except Exception as e:
            print(f"Warning: Failed to add file handler: {e}")

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger with the given name.

        Args:
            name: Logger name (typically module or class name)

        Returns:
            Configured logger instance
        """
        if name in self._configured_loggers:
            return self._configured_loggers[name]

        logger = logging.getLogger(name)
        self._configured_loggers[name] = logger

        return logger

    def set_level(self, level: str) -> None:
        """
        Update the log level for all loggers.

        Args:
            level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        numeric_level = getattr(logging, level.upper(), logging.INFO)

        # Update root logger
        logging.getLogger().setLevel(numeric_level)

        # Update all handlers
        for handler in logging.getLogger().handlers:
            handler.setLevel(numeric_level)

        self._log_level = level
        self._logger.info(f"Log level changed to {level}")

    def get_level(self) -> str:
        """Get the current log level."""
        return self._log_level

    def get_format(self) -> str:
        """Get the current log format."""
        return self._log_format


# =============================================================================
# Factory Function - Clean Architecture v5.1 Compliance (Rule #1)
# =============================================================================


def create_logging_config_manager(
    config_manager: Optional[Any] = None,
    log_level: str = "INFO",
    log_format: str = "human",
    log_file: Optional[str] = None,
    console_output: bool = True,
) -> LoggingConfigManager:
    """
    Factory function for LoggingConfigManager (Clean Architecture v5.1 Pattern).

    This is the ONLY way to create a LoggingConfigManager instance.
    Direct instantiation should be avoided in production code.

    Args:
        config_manager: ConfigManager instance for loading settings
        log_level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ('human' for colorized, 'json' for structured)
        log_file: Path to log file (optional)
        console_output: Whether to output to console

    Returns:
        Configured LoggingConfigManager instance

    Example:
        >>> from src.managers.config_manager import create_config_manager
        >>> config = create_config_manager()
        >>> logging_mgr = create_logging_config_manager(config)
        >>> logger = logging_mgr.get_logger("my_module")
    """
    return LoggingConfigManager(
        config_manager=config_manager,
        log_level=log_level,
        log_format=log_format,
        log_file=log_file,
        console_output=console_output,
    )


# =============================================================================
# Export public interface
# =============================================================================

__all__ = [
    "LoggingConfigManager",
    "create_logging_config_manager",
    "ColorizedFormatter",
    "JSONFormatter",
    "Colors",
]
