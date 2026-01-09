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
Replication Job - ZFS Replication to Lofn
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
from typing import List, Optional, Tuple

from src.managers.alert_manager import create_alert_manager

__version__ = "v5.0-3-3.5-1"


class ReplicationJob:
    """
    ZFS Replication Job - Replicates encrypted ZFS streams to Lofn.
    
    Uses `zfs send -w` to send raw encrypted data, ensuring Lofn
    never has access to decrypted content.
    """
    
    def __init__(self, config_manager, logging_manager):
        """
        Initialize ReplicationJob.
        
        Args:
            config_manager: Configuration manager instance
            logging_manager: Logging manager instance
        """
        self.config_manager = config_manager
        self.logger = logging_manager.get_logger(__name__)
        self.alert_manager = create_alert_manager(config_manager, logging_manager)
        
        # Get configuration
        zfs_config = config_manager.get_section("zfs")
        self.source_dataset = zfs_config.get("dataset", "syn/archives")
        
        replication_config = config_manager.get_section("replication")
        self.lofn_host = replication_config.get("lofn_host", "10.20.30.253")
        self.lofn_dataset = replication_config.get("lofn_dataset", "backup/ash-vault")
        self.ssh_key = replication_config.get("ssh_key", "/root/.ssh/id_ed25519_lofn")
    
    def _run_command(self, command: List[str], timeout: int = 3600) -> Tuple[bool, str]:
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
    
    def _get_latest_snapshot(self) -> Optional[str]:
        """
        Get the most recent daily snapshot name.
        
        Returns:
            Snapshot name or None if not found
        """
        success, output = self._run_command([
            "zfs", "list", "-t", "snapshot", "-o", "name", "-H", "-r", self.source_dataset
        ])
        
        if not success:
            self.logger.error(f"❌ Failed to list snapshots: {output}")
            return None
        
        # Filter for daily snapshots and get the latest
        snapshots = [
            line for line in output.strip().split("\n")
            if line and "@daily-" in line
        ]
        
        if not snapshots:
            self.logger.warning("⚠️ No daily snapshots found")
            return None
        
        return sorted(snapshots)[-1]
    
    def _get_remote_latest_snapshot(self) -> Optional[str]:
        """
        Get the most recent snapshot on Lofn.
        
        Returns:
            Snapshot name or None if not found
        """
        ssh_cmd = [
            "ssh", "-i", self.ssh_key,
            "-o", "StrictHostKeyChecking=no",
            "-o", "BatchMode=yes",
            f"root@{self.lofn_host}",
            f"zfs list -t snapshot -o name -H -r {self.lofn_dataset} 2>/dev/null | tail -1"
        ]
        
        success, output = self._run_command(ssh_cmd)
        
        if success and output.strip():
            # Extract just the snapshot part after @
            full_name = output.strip()
            if "@" in full_name:
                return full_name
        
        return None
    
    def _check_remote_dataset_exists(self) -> bool:
        """Check if the remote dataset exists on Lofn."""
        ssh_cmd = [
            "ssh", "-i", self.ssh_key,
            "-o", "StrictHostKeyChecking=no",
            "-o", "BatchMode=yes",
            f"root@{self.lofn_host}",
            f"zfs list {self.lofn_dataset} 2>/dev/null"
        ]
        
        success, _ = self._run_command(ssh_cmd)
        return success
    
    def _do_initial_send(self, snapshot: str) -> bool:
        """
        Perform initial full ZFS send to Lofn.
        
        Args:
            snapshot: Full snapshot name to send
        
        Returns:
            True if successful
        """
        self.logger.info(f"📤 Performing initial full send: {snapshot}")
        
        # Use shell=True for pipe
        cmd = (
            f"zfs send -w {snapshot} | "
            f"ssh -i {self.ssh_key} -o StrictHostKeyChecking=no "
            f"root@{self.lofn_host} 'zfs recv -F {self.lofn_dataset}'"
        )
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=7200  # 2 hour timeout for initial send
            )
            
            if result.returncode == 0:
                return True
            else:
                self.logger.error(f"❌ Initial send failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Initial send error: {e}")
            return False
    
    def _do_incremental_send(self, from_snap: str, to_snap: str) -> bool:
        """
        Perform incremental ZFS send to Lofn.
        
        Args:
            from_snap: Previous snapshot name (just the @part)
            to_snap: Current snapshot name (full)
        
        Returns:
            True if successful
        """
        # Extract just the @snapshot part from from_snap
        from_snap_short = from_snap.split("@")[-1] if "@" in from_snap else from_snap
        
        self.logger.info(f"📤 Performing incremental send: @{from_snap_short} -> {to_snap}")
        
        cmd = (
            f"zfs send -w -i @{from_snap_short} {to_snap} | "
            f"ssh -i {self.ssh_key} -o StrictHostKeyChecking=no "
            f"root@{self.lofn_host} 'zfs recv -F {self.lofn_dataset}'"
        )
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                return True
            else:
                self.logger.error(f"❌ Incremental send failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Incremental send error: {e}")
            return False
    
    def run(self) -> bool:
        """
        Run the replication job.
        
        Returns:
            True if successful
        """
        job_name = "ZFS Replication to Lofn"
        start_time = time.time()
        
        self.logger.info(f"🚀 Starting {job_name}")
        self.logger.info(f"   Source: {self.source_dataset}")
        self.logger.info(f"   Target: {self.lofn_host}:{self.lofn_dataset}")
        
        try:
            # Get latest local snapshot
            local_latest = self._get_latest_snapshot()
            if not local_latest:
                raise Exception("No local snapshots available for replication")
            
            self.logger.info(f"📸 Latest local snapshot: {local_latest}")
            
            # Check if remote dataset has snapshots
            remote_latest = self._get_remote_latest_snapshot()
            
            if remote_latest:
                self.logger.info(f"📸 Latest remote snapshot: {remote_latest}")
                
                # Do incremental send
                success = self._do_incremental_send(remote_latest, local_latest)
            else:
                self.logger.info("📭 No remote snapshots - performing initial full send")
                
                # Do initial full send
                success = self._do_initial_send(local_latest)
            
            if not success:
                raise Exception("ZFS send/recv failed")
            
            # Success
            duration = time.time() - start_time
            self.logger.info(f"✅ {job_name} completed in {duration:.1f}s")
            
            self.alert_manager.backup_success(
                job_name=job_name,
                duration_seconds=duration,
                details=f"Replicated to {self.lofn_host}:{self.lofn_dataset}"
            )
            
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"❌ {job_name} failed: {e}")
            
            self.alert_manager.backup_failure(
                job_name=job_name,
                error=str(e),
                details=f"Target: {self.lofn_host}:{self.lofn_dataset}"
            )
            
            return False


def create_replication_job(config_manager, logging_manager) -> ReplicationJob:
    """
    Factory function for ReplicationJob.
    
    Args:
        config_manager: Configuration manager instance
        logging_manager: Logging manager instance
    
    Returns:
        ReplicationJob instance
    """
    return ReplicationJob(config_manager, logging_manager)


__all__ = ["ReplicationJob", "create_replication_job"]
