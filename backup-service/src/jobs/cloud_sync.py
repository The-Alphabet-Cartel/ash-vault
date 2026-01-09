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
Cloud Sync Job - Rclone Sync to Backblaze B2
----------------------------------------------------------------------------
FILE VERSION: v5.0-3-3.5-1
LAST MODIFIED: 2026-01-09
PHASE: Phase 3 - Backup Infrastructure
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================
"""

import subprocess
import time
from typing import List, Tuple

from src.managers.alert_manager import create_alert_manager

__version__ = "v5.0-3-3.5-1"


class CloudSyncJob:
    """
    Cloud Sync Job - Syncs MinIO data to Backblaze B2.
    
    Uses rclone to synchronize the MinIO data directory to B2 cloud storage.
    Data is already encrypted at the application layer, so B2 only sees blobs.
    """
    
    def __init__(self, config_manager, logging_manager):
        """
        Initialize CloudSyncJob.
        
        Args:
            config_manager: Configuration manager instance
            logging_manager: Logging manager instance
        """
        self.config_manager = config_manager
        self.logger = logging_manager.get_logger(__name__)
        self.alert_manager = create_alert_manager(config_manager, logging_manager)
        
        # Get configuration
        cloud_config = config_manager.get_section("cloud")
        self.b2_bucket = cloud_config.get("b2_bucket", "ash-vault-backup-alphabetcartel")
        self.minio_data_path = cloud_config.get("minio_data_path", "/mnt/archives/minio-data")
        self.rclone_remote = cloud_config.get("rclone_remote", "b2")
    
    def _run_command(self, command: List[str], timeout: int = 7200) -> Tuple[bool, str]:
        """
        Run a shell command and return result.
        
        Args:
            command: Command as list of strings
            timeout: Command timeout in seconds
        
        Returns:
            Tuple of (success, output)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def _get_local_size(self) -> str:
        """Get the size of the local MinIO data directory."""
        success, output = self._run_command([
            "du", "-sh", self.minio_data_path
        ])
        
        if success:
            return output.split()[0]
        return "unknown"
    
    def _check_rclone_config(self) -> bool:
        """Verify rclone is configured and can connect to B2."""
        success, output = self._run_command([
            "rclone", "lsd", f"{self.rclone_remote}:"
        ], timeout=60)
        
        if not success:
            self.logger.error(f"❌ Rclone configuration check failed: {output}")
            return False
        
        return True
    
    def _do_sync(self) -> Tuple[bool, str]:
        """
        Perform the rclone sync to B2.
        
        Returns:
            Tuple of (success, stats_output)
        """
        destination = f"{self.rclone_remote}:{self.b2_bucket}"
        
        self.logger.info(f"📤 Syncing {self.minio_data_path} -> {destination}")
        
        cmd = [
            "rclone", "sync",
            self.minio_data_path,
            destination,
            "--transfers", "4",
            "--checkers", "8",
            "--stats", "30s",
            "--stats-one-line",
            "-v"
        ]
        
        success, output = self._run_command(cmd, timeout=7200)  # 2 hour timeout
        
        return success, output
    
    def run(self) -> bool:
        """
        Run the cloud sync job.
        
        Returns:
            True if successful
        """
        job_name = "Cloud Sync to Backblaze B2"
        start_time = time.time()
        
        self.logger.info(f"🚀 Starting {job_name}")
        self.logger.info(f"   Source: {self.minio_data_path}")
        self.logger.info(f"   Destination: {self.rclone_remote}:{self.b2_bucket}")
        
        try:
            # Check rclone configuration
            if not self._check_rclone_config():
                raise Exception("Rclone configuration check failed")
            
            # Get local size for logging
            local_size = self._get_local_size()
            self.logger.info(f"📦 Local data size: {local_size}")
            
            # Perform sync
            success, output = self._do_sync()
            
            if not success:
                raise Exception(f"Rclone sync failed: {output}")
            
            # Success
            duration = time.time() - start_time
            self.logger.info(f"✅ {job_name} completed in {duration:.1f}s")
            
            self.alert_manager.backup_success(
                job_name=job_name,
                duration_seconds=duration,
                details=f"Synced {local_size} to {self.b2_bucket}"
            )
            
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"❌ {job_name} failed: {e}")
            
            self.alert_manager.backup_failure(
                job_name=job_name,
                error=str(e),
                details=f"Destination: {self.rclone_remote}:{self.b2_bucket}"
            )
            
            return False


def create_cloud_sync_job(config_manager, logging_manager) -> CloudSyncJob:
    """
    Factory function for CloudSyncJob.
    
    Args:
        config_manager: Configuration manager instance
        logging_manager: Logging manager instance
    
    Returns:
        CloudSyncJob instance
    """
    return CloudSyncJob(config_manager, logging_manager)


__all__ = ["CloudSyncJob", "create_cloud_sync_job"]
