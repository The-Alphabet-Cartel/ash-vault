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
Snapshot Job - ZFS Snapshot Management
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
from datetime import datetime
from typing import List, Optional

from src.managers.alert_manager import create_alert_manager

__version__ = "v5.0-3-3.5-1"


class SnapshotJob:
    """
    ZFS Snapshot Job - Creates and manages ZFS snapshots.
    
    Handles daily, weekly, and monthly snapshots with configurable retention.
    """
    
    def __init__(self, config_manager, logging_manager):
        """
        Initialize SnapshotJob.
        
        Args:
            config_manager: Configuration manager instance
            logging_manager: Logging manager instance
        """
        self.config_manager = config_manager
        self.logger = logging_manager.get_logger(__name__)
        self.alert_manager = create_alert_manager(config_manager, logging_manager)
        
        # Get configuration
        zfs_config = config_manager.get_section("zfs")
        self.dataset = zfs_config.get("dataset", "syn/archives")
        
        retention_config = config_manager.get_section("retention")
        self.retention = {
            "daily": retention_config.get("daily_count", 7),
            "weekly": retention_config.get("weekly_count", 4),
            "monthly": retention_config.get("monthly_count", 12)
        }
    
    def _run_command(self, command: List[str]) -> tuple[bool, str]:
        """
        Run a shell command and return result.
        
        Args:
            command: Command as list of strings
        
        Returns:
            Tuple of (success, output)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def _create_snapshot(self, snapshot_type: str) -> bool:
        """
        Create a ZFS snapshot.
        
        Args:
            snapshot_type: Type of snapshot (daily, weekly, monthly)
        
        Returns:
            True if successful
        """
        timestamp = datetime.now().strftime("%Y-%m-%d")
        snapshot_name = f"{self.dataset}@{snapshot_type}-{timestamp}"
        
        self.logger.info(f"📸 Creating {snapshot_type} snapshot: {snapshot_name}")
        
        success, output = self._run_command(["zfs", "snapshot", snapshot_name])
        
        if success:
            self.logger.info(f"✅ Snapshot created: {snapshot_name}")
            return True
        else:
            self.logger.error(f"❌ Snapshot failed: {output}")
            return False
    
    def _list_snapshots(self, prefix: str) -> List[str]:
        """
        List snapshots matching a prefix.
        
        Args:
            prefix: Snapshot name prefix (e.g., "daily", "weekly")
        
        Returns:
            List of snapshot names, sorted oldest first
        """
        success, output = self._run_command([
            "zfs", "list", "-t", "snapshot", "-o", "name", "-H", "-r", self.dataset
        ])
        
        if not success:
            self.logger.error(f"❌ Failed to list snapshots: {output}")
            return []
        
        # Filter and sort snapshots
        snapshots = []
        for line in output.strip().split("\n"):
            if line and f"@{prefix}-" in line:
                snapshots.append(line)
        
        return sorted(snapshots)
    
    def _cleanup_old_snapshots(self, snapshot_type: str) -> None:
        """
        Remove snapshots exceeding retention limit.
        
        Args:
            snapshot_type: Type of snapshot to clean up
        """
        retention_count = self.retention.get(snapshot_type, 7)
        snapshots = self._list_snapshots(snapshot_type)
        
        if len(snapshots) <= retention_count:
            self.logger.debug(f"📦 {snapshot_type} snapshots within retention ({len(snapshots)}/{retention_count})")
            return
        
        # Delete oldest snapshots
        to_delete = snapshots[:-retention_count]
        
        for snapshot in to_delete:
            self.logger.info(f"🗑️ Deleting old snapshot: {snapshot}")
            success, output = self._run_command(["zfs", "destroy", snapshot])
            
            if success:
                self.logger.info(f"✅ Deleted: {snapshot}")
            else:
                self.logger.error(f"❌ Failed to delete {snapshot}: {output}")
    
    def run_daily(self) -> bool:
        """Run daily snapshot job."""
        return self._run_snapshot_job("daily")
    
    def run_weekly(self) -> bool:
        """Run weekly snapshot job."""
        return self._run_snapshot_job("weekly")
    
    def run_monthly(self) -> bool:
        """Run monthly snapshot job."""
        return self._run_snapshot_job("monthly")
    
    def _run_snapshot_job(self, snapshot_type: str) -> bool:
        """
        Execute a snapshot job with alerting.
        
        Args:
            snapshot_type: Type of snapshot (daily, weekly, monthly)
        
        Returns:
            True if successful
        """
        job_name = f"ZFS {snapshot_type.capitalize()} Snapshot"
        start_time = time.time()
        
        self.logger.info(f"🚀 Starting {job_name}")
        
        try:
            # Create snapshot
            if not self._create_snapshot(snapshot_type):
                raise Exception(f"Failed to create {snapshot_type} snapshot")
            
            # Cleanup old snapshots
            self._cleanup_old_snapshots(snapshot_type)
            
            # Success
            duration = time.time() - start_time
            self.logger.info(f"✅ {job_name} completed in {duration:.1f}s")
            
            self.alert_manager.backup_success(
                job_name=job_name,
                duration_seconds=duration,
                details=f"Dataset: {self.dataset}"
            )
            
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"❌ {job_name} failed: {e}")
            
            self.alert_manager.backup_failure(
                job_name=job_name,
                error=str(e),
                details=f"Dataset: {self.dataset}"
            )
            
            return False


def create_snapshot_job(config_manager, logging_manager) -> SnapshotJob:
    """
    Factory function for SnapshotJob.
    
    Args:
        config_manager: Configuration manager instance
        logging_manager: Logging manager instance
    
    Returns:
        SnapshotJob instance
    """
    return SnapshotJob(config_manager, logging_manager)


__all__ = ["SnapshotJob", "create_snapshot_job"]
