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
Jobs Package - Backup Job Implementations
----------------------------------------------------------------------------
FILE VERSION: v5.0-3-3.5a-1
LAST MODIFIED: 2026-01-09
PHASE: Phase 3 - Backup Infrastructure
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================

This package provides backup job implementations following
Clean Architecture v5.2 Rule #1: Factory Function Pattern.

USAGE:
    from src.jobs import (
        create_snapshot_job,
        create_replication_job,
        create_cloud_sync_job,
    )

    # Initialize jobs with managers
    snapshot_job = create_snapshot_job(config_manager, logging_manager)
    replication_job = create_replication_job(config_manager, logging_manager)
    cloud_sync_job = create_cloud_sync_job(config_manager, logging_manager)
"""

# Snapshot Job - ZFS snapshot management
from src.jobs.snapshot import (
    SnapshotJob,
    create_snapshot_job,
)

# Replication Job - ZFS replication to Lofn
from src.jobs.replicate import (
    ReplicationJob,
    create_replication_job,
)

# Cloud Sync Job - Rclone sync to Backblaze B2
from src.jobs.cloud_sync import (
    CloudSyncJob,
    create_cloud_sync_job,
)

# =============================================================================
# Export public interface
# =============================================================================

__all__ = [
    # Snapshot Job
    "SnapshotJob",
    "create_snapshot_job",
    # Replication Job
    "ReplicationJob",
    "create_replication_job",
    # Cloud Sync Job
    "CloudSyncJob",
    "create_cloud_sync_job",
]
