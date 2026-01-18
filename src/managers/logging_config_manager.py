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
Logging Configuration Manager - Charter v5.2 Compliant Colorized Logging
----------------------------------------------------------------------------
FILE VERSION: v5.0-6-1.0-1
LAST MODIFIED: 2026-01-17
PHASE: Phase 6 - Logging Colorization Enforcement
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================

RESPONSIBILITIES:
- Configure colorized console logging per Charter v5.2 Rule #9
- Support JSON format for production log aggregation
- Provide consistent log formatting across all Ash-Vault modules
- Enable log level filtering via configuration
- Create child loggers for component isolation
- Custom SUCCESS level for positive confirmations
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Module version
__version__ = "v5.0-6-1.1-1"


# =============================================================================
# Custom SUCCESS Log Level (between INFO and WARNING)
# =============================================================================
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


def _success(self, message, *args, **kwargs):
    """Log a SUCCESS level message."""
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)


# Add success method to Logger class
logging.Logger.success = _success


# =============================================================================
# ANSI Color Codes - Charter v5.2 Standard
# =============================================================================
class Colors:
    """
    ANSI escape codes for colorized console output.

    Charter v5.2 Rule #9 Compliant Color Scheme:
    - CRITICAL: Bright Red Bold - System failures, data loss risks
    - ERROR:    Bright Red      - Exceptions, failed operations
    - WARNING:  Bright Yellow   - Degraded state, potential issues
    - INFO:     Bright Cyan     - Normal operations, status updates
    - DEBUG:    Gray            - Diagnostic details, verbose output
    - SUCCESS:  Bright Green    - Successful completions
    """

    # Reset
    RESET = "\033[0m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Charter v5.2 Standard Log Level Colors
    CRITICAL = "\033[1;91m"  # Bright Red Bold
    ERROR = "\033[91m"        # Bright Red
    WARNING = "\033[93m"      # Bright Yellow
    INFO = "\033[96m"         # Bright Cyan
    DEBUG = "\033[90m"        # Gray
    SUCCESS = "\033[92m"      # Bright Green

    # Additional colors for formatting
    TIMESTAMP = "\033[90m"    # Gray
    LOGGER_NAME = "\033[94m"  # Bright Blue
    MESSAGE = "\033[97m"      # Bright White

    # Legacy color names (for backward compatibility)
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    UNDERLINE = "\033[4m"


# =============================================================================
# Colorized Formatter - Charter v5.2 Compliant
# =============================================================================
class ColorizedFormatter(logging.Formatter):
    """
    Custom formatter with Charter v5.2 compliant colorization.

    Format: [TIMESTAMP] LEVEL    | logger_name | message
    """

    LEVEL_COLORS = {
        logging.CRITICAL: Colors.CRITICAL,
        logging.ERROR: Colors.ERROR,
        logging.WARNING: Colors.WARNING,
        logging.INFO: Colors.INFO,
        logging.DEBUG: Colors.DEBUG,
        SUCCESS_LEVEL: Colors.SUCCESS,
    }

    LEVEL_SYMBOLS = {
        logging.CRITICAL: "🚨",
        logging.ERROR: "❌",
        logging.WARNING: "⚠️ ",
        logging.INFO: "ℹ️ ",
        logging.DEBUG: "🔍",
        SUCCESS_LEVEL: "✅",
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
            fmt: Log message format string (ignored, using custom format)
            datefmt: Date format string
            use_colors: Whether to use ANSI color codes
            use_symbols: Whether to use emoji symbols
        """
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"
        super().__init__(datefmt=datefmt)
        self.use_colors = use_colors
        self.use_symbols = use_symbols

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors and alignment."""
        # Get color for this level
        level_color = self.LEVEL_COLORS.get(record.levelno, Colors.RESET)
        symbol = self.LEVEL_SYMBOLS.get(record.levelno, "") if self.use_symbols else ""

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime(self.datefmt)

        # Pad level name for alignment
        level_name = record.levelname.ljust(8)

        # Truncate logger name if too long
        logger_name = record.name
        if len(logger_name) > 25:
            logger_name = "..." + logger_name[-22:]
        logger_name = logger_name.ljust(25)

        # Get the message
        message = record.getMessage()

        # Build formatted output
        if self.use_colors:
            formatted = (
                f"{Colors.TIMESTAMP}[{timestamp}]{Colors.RESET} "
                f"{level_color}{level_name}{Colors.RESET} "
                f"{Colors.DIM}|{Colors.RESET} "
                f"{Colors.LOGGER_NAME}{logger_name}{Colors.RESET} "
                f"{Colors.DIM}|{Colors.RESET} "
                f"{symbol} {level_color}{message}{Colors.RESET}"
            )
        else:
            formatted = (
                f"[{timestamp}] {level_name} | {logger_name} | {symbol} {message}"
            )

        # Add exception info if present
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            if self.use_colors:
                formatted += f"\n{Colors.ERROR}{exc_text}{Colors.RESET}"
            else:
                formatted += f"\n{exc_text}"

        return formatted


# =============================================================================
# JSON Formatter for Production
# =============================================================================
class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs logs as JSON for production log aggregation.

    Useful for:
    - Log aggregation systems (ELK, Loki, etc.)
    - Structured log analysis
    - Production environments
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
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
    Manages logging configuration with Charter v5.2 compliant colorization.

    Features:
        - Colorized console output (human format) per Charter v5.2 Rule #9
        - JSON format for production log aggregation
        - Custom SUCCESS level for positive confirmations
        - File logging with JSON format
        - Per-module logger creation

    Example:
        >>> logging_manager = create_logging_config_manager(config_manager)
        >>> logger = logging_manager.get_logger("my_module")
        >>> logger.info("Backup started")
        >>> logger.success("Backup completed successfully")
    """

    def __init__(
        self,
        config_manager: Optional[Any] = None,
        log_level: str = "INFO",
        log_format: str = "human",
        log_file: Optional[str] = None,
        console_output: bool = True,
        app_name: str = "ash-vault",
    ):
        """
        Initialize the LoggingConfigManager.

        Args:
            config_manager: ConfigManager instance for loading settings
            log_level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Output format ('human' for colorized, 'json' for structured)
            log_file: Path to log file (optional)
            console_output: Whether to output to console
            app_name: Application name for root logger
        """
        # Store configuration
        self._config_manager = config_manager
        self._log_level = log_level
        self._log_format = log_format
        self._log_file = log_file
        self._console_output = console_output
        self._app_name = app_name

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
            if hasattr(self._config_manager, "get_section"):
                logging_config = self._config_manager.get_section("logging")
                self._log_level = logging_config.get("level", self._log_level)
                self._log_format = logging_config.get("format", self._log_format)
                self._log_file = logging_config.get("file", self._log_file)
                self._console_output = logging_config.get(
                    "console", self._console_output
                )
        except Exception as e:
            # Fall back to defaults if config loading fails
            print(f"Warning: Failed to load logging config: {e}")

    def _configure_root_logger(self) -> None:
        """Configure the root logger with handlers."""
        # Get root logger
        root_logger = logging.getLogger(self._app_name)

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
                # Check for forced color output (useful for Docker containers)
                # Set FORCE_COLOR=1 in environment to enable colors without TTY
                force_color = os.environ.get("FORCE_COLOR", "").lower() in ("1", "true", "yes")
                use_colors = force_color or (hasattr(sys.stdout, "isatty") and sys.stdout.isatty())
                console_handler.setFormatter(
                    ColorizedFormatter(use_colors=use_colors, use_symbols=True)
                )

            root_logger.addHandler(console_handler)

        # Add file handler if configured
        if self._log_file:
            self._add_file_handler(root_logger, self._log_file)

        # Prevent propagation
        root_logger.propagate = False

        # Reduce noise from third-party libraries
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("boto3").setLevel(logging.WARNING)
        logging.getLogger("botocore").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

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

        if not name.startswith(self._app_name):
            name = f"{self._app_name}.{name}"

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
        root_logger = logging.getLogger(self._app_name)
        root_logger.setLevel(numeric_level)

        # Update all handlers
        for handler in root_logger.handlers:
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
# Factory Function - Clean Architecture v5.2 Compliance (Rule #1)
# =============================================================================
def create_logging_config_manager(
    config_manager: Optional[Any] = None,
    log_level: str = "INFO",
    log_format: str = "human",
    log_file: Optional[str] = None,
    console_output: bool = True,
    app_name: str = "ash-vault",
) -> LoggingConfigManager:
    """
    Factory function for LoggingConfigManager (Clean Architecture v5.2 Pattern).

    This is the ONLY way to create a LoggingConfigManager instance.
    Direct instantiation should be avoided in production code.

    Args:
        config_manager: ConfigManager instance for loading settings
        log_level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ('human' for colorized, 'json' for structured)
        log_file: Path to log file (optional)
        console_output: Whether to output to console
        app_name: Application name for root logger

    Returns:
        Configured LoggingConfigManager instance

    Example:
        >>> from src.managers.config_manager import create_config_manager
        >>> config = create_config_manager()
        >>> logging_mgr = create_logging_config_manager(config)
        >>> logger = logging_mgr.get_logger("backup_manager")
    """
    return LoggingConfigManager(
        config_manager=config_manager,
        log_level=log_level,
        log_format=log_format,
        log_file=log_file,
        console_output=console_output,
        app_name=app_name,
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
    "SUCCESS_LEVEL",
]
