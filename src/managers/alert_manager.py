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
Alert Manager - Discord Webhook Notifications
----------------------------------------------------------------------------
FILE VERSION: v5.0-4-1.2-1
LAST MODIFIED: 2026-01-18
PHASE: Phase 3 - Backup Infrastructure
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================
"""

import logging
from datetime import datetime
from typing import Any, List, Optional
from pathlib import Path

import httpx

__version__ = "v5.0-3-3.5a-1"


class AlertManager:
    """
    Alert Manager for Discord webhook notifications.
    
    Sends backup status alerts to Discord channels.
    """
    
    # Embed colors
    COLOR_SUCCESS = 0x00FF00  # Green
    COLOR_FAILURE = 0xFF0000  # Red
    COLOR_WARNING = 0xFFFF00  # Yellow
    COLOR_INFO = 0x0099FF     # Blue
    
    def __init__(self, config_manager: Any, logging_manager: Any):
        """
        Initialize AlertManager.
        
        Args:
            config_manager: Configuration manager instance
            logging_manager: Logging manager instance
        """
        self.config_manager = config_manager
        self.logger = logging_manager.get_logger(__name__)
        
        # Load alerting configuration
        self.alerting_config = config_manager.get_section("alerting")
        self.enabled = self.alerting_config.get("enabled", True)
        self.on_success = self.alerting_config.get("on_backup_success", False)
        self.on_failure = self.alerting_config.get("on_backup_failure", True)
        
        # Load webhook URL from Docker secret
        self.webhook_url = self._load_webhook_url()
    
    def _load_webhook_url(self) -> Optional[str]:
        """Load Discord webhook URL from Docker secret."""
        secret_paths = [
            Path("/run/secrets/ash_vault_discord_alert_token"),
            Path("/app/secrets/ash_vault_discord_alert_token"),
            Path("secrets/ash_vault_discord_alert_token"),
        ]
        
        for path in secret_paths:
            if path.exists():
                try:
                    return path.read_text().strip()
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to read webhook secret: {e}")
        
        self.logger.warning("⚠️ Discord webhook not configured - alerts disabled")
        return None
    
    def send_alert(
        self,
        title: str,
        message: str,
        color: int,
        fields: Optional[List[dict]] = None
    ) -> bool:
        """
        Send an alert to Discord.
        
        Args:
            title: Alert title
            message: Alert message
            color: Embed color (hex)
            fields: Optional list of embed fields
        
        Returns:
            True if sent successfully
        """
        if not self.enabled or not self.webhook_url:
            return False
        
        embed = {
            "title": title,
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Ash-Vault Backup Service"
            }
        }
        
        if fields:
            embed["fields"] = fields
        
        payload = {
            "embeds": [embed]
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    self.webhook_url,
                    json=payload
                )
                response.raise_for_status()
            
            self.logger.debug(f"📤 Alert sent: {title}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to send alert: {e}")
            return False
    
    def backup_success(
        self,
        job_name: str,
        duration_seconds: float,
        details: str = ""
    ) -> bool:
        """
        Send a backup success alert.
        
        Args:
            job_name: Name of the backup job
            duration_seconds: How long the backup took
            details: Additional details
        
        Returns:
            True if sent successfully
        """
        if not self.on_success:
            return False
        
        fields = [
            {"name": "Job", "value": job_name, "inline": True},
            {"name": "Duration", "value": f"{duration_seconds:.1f}s", "inline": True}
        ]
        
        if details:
            fields.append({"name": "Details", "value": details, "inline": False})
        
        return self.send_alert(
            title="✅ Backup Successful",
            message=f"The {job_name} backup completed successfully.",
            color=self.COLOR_SUCCESS,
            fields=fields
        )
    
    def backup_failure(
        self,
        job_name: str,
        error: str,
        details: str = ""
    ) -> bool:
        """
        Send a backup failure alert.
        
        Args:
            job_name: Name of the backup job
            error: Error message
            details: Additional details
        
        Returns:
            True if sent successfully
        """
        if not self.on_failure:
            return False
        
        fields = [
            {"name": "Job", "value": job_name, "inline": True},
            {"name": "Error", "value": str(error)[:1000], "inline": False}
        ]
        
        if details:
            fields.append({"name": "Details", "value": details[:1000], "inline": False})
        
        return self.send_alert(
            title="❌ Backup Failed",
            message=f"The {job_name} backup encountered an error.",
            color=self.COLOR_FAILURE,
            fields=fields
        )


def create_alert_manager(config_manager: Any, logging_manager: Any) -> AlertManager:
    """
    Factory function for AlertManager.
    
    Args:
        config_manager: Configuration manager instance
        logging_manager: Logging manager instance
    
    Returns:
        AlertManager instance
    """
    return AlertManager(config_manager, logging_manager)


__all__ = ["AlertManager", "create_alert_manager"]
