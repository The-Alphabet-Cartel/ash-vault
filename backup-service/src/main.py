#!/usr/bin/env python3
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
Main Entry Point - Backup Service Orchestration
----------------------------------------------------------------------------
FILE VERSION: v5.0-3-3.5-1
LAST MODIFIED: 2026-01-09
PHASE: Phase 3 - Backup Infrastructure
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================

This module initializes and runs the Ash-Vault backup service, which:
- Manages ZFS snapshots (daily, weekly, monthly) with retention policies
- Replicates encrypted ZFS streams to Lofn (Tier 2 backup)
- Syncs MinIO data to Backblaze B2 (Tier 1 cloud backup)
- Provides a health endpoint for monitoring
- Sends Discord alerts on backup failures
"""

import logging
import signal
import sys
import threading
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.managers.config_manager import create_config_manager
from src.managers.logging_manager import create_logging_manager
from src.jobs.snapshot import create_snapshot_job
from src.jobs.replicate import create_replication_job
from src.jobs.cloud_sync import create_cloud_sync_job
from src.api.health import create_health_app

# Module version
__version__ = "v5.0-3-3.5-1"

# Global scheduler reference for graceful shutdown
scheduler: Optional[BackgroundScheduler] = None
shutdown_event = threading.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()
    
    if scheduler:
        scheduler.shutdown(wait=False)
    
    sys.exit(0)


def setup_scheduler(config_manager, logging_manager) -> BackgroundScheduler:
    """
    Configure APScheduler with all backup jobs.
    
    Args:
        config_manager: Configuration manager instance
        logging_manager: Logging manager instance
    
    Returns:
        Configured BackgroundScheduler instance
    """
    logger = logging_manager.get_logger(__name__)
    
    sched = BackgroundScheduler(
        timezone="America/Los_Angeles",
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 3600  # 1 hour grace period
        }
    )
    
    # Get schedule configuration
    schedules = config_manager.get_section("schedules")
    
    # Create job instances
    snapshot_job = create_snapshot_job(config_manager, logging_manager)
    replication_job = create_replication_job(config_manager, logging_manager)
    cloud_sync_job = create_cloud_sync_job(config_manager, logging_manager)
    
    # Schedule daily snapshots (3 AM)
    sched.add_job(
        snapshot_job.run_daily,
        CronTrigger.from_crontab(schedules.get("snapshot_daily", "0 3 * * *")),
        id="snapshot_daily",
        name="Daily ZFS Snapshot"
    )
    logger.info(f"📅 Scheduled: Daily snapshot at {schedules.get('snapshot_daily', '0 3 * * *')}")
    
    # Schedule weekly snapshots (3 AM Sunday)
    sched.add_job(
        snapshot_job.run_weekly,
        CronTrigger.from_crontab(schedules.get("snapshot_weekly", "0 3 * * 0")),
        id="snapshot_weekly",
        name="Weekly ZFS Snapshot"
    )
    logger.info(f"📅 Scheduled: Weekly snapshot at {schedules.get('snapshot_weekly', '0 3 * * 0')}")
    
    # Schedule monthly snapshots (3 AM 1st of month)
    sched.add_job(
        snapshot_job.run_monthly,
        CronTrigger.from_crontab(schedules.get("snapshot_monthly", "0 3 1 * *")),
        id="snapshot_monthly",
        name="Monthly ZFS Snapshot"
    )
    logger.info(f"📅 Scheduled: Monthly snapshot at {schedules.get('snapshot_monthly', '0 3 1 * *')}")
    
    # Schedule replication to Lofn (4 AM daily)
    sched.add_job(
        replication_job.run,
        CronTrigger.from_crontab(schedules.get("replication", "0 4 * * *")),
        id="replication_lofn",
        name="ZFS Replication to Lofn"
    )
    logger.info(f"📅 Scheduled: Lofn replication at {schedules.get('replication', '0 4 * * *')}")
    
    # Schedule cloud sync to B2 (5 AM Sunday)
    sched.add_job(
        cloud_sync_job.run,
        CronTrigger.from_crontab(schedules.get("cloud_sync", "0 5 * * 0")),
        id="cloud_sync_b2",
        name="Cloud Sync to Backblaze B2"
    )
    logger.info(f"📅 Scheduled: B2 cloud sync at {schedules.get('cloud_sync', '0 5 * * 0')}")
    
    return sched


def main():
    """
    Main entry point for the Ash-Vault backup service.
    """
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize configuration
    config_manager = create_config_manager()
    
    # Initialize logging
    logging_manager = create_logging_manager(config_manager)
    logger = logging_manager.get_logger(__name__)
    
    # Print startup banner
    logger.info("=" * 60)
    logger.info("  Ash-Vault Backup Service")
    logger.info(f"  Version: {__version__}")
    logger.info("  The Alphabet Cartel - discord.gg/alphabetcartel")
    logger.info("=" * 60)
    
    # Log configuration
    logger.info(f"📁 ZFS Dataset: {config_manager.get('zfs', 'dataset')}")
    logger.info(f"🔄 Lofn Target: {config_manager.get('replication', 'lofn_dataset')}")
    logger.info(f"☁️  B2 Bucket: {config_manager.get('cloud', 'b2_bucket')}")
    
    # Setup scheduler
    global scheduler
    scheduler = setup_scheduler(config_manager, logging_manager)
    scheduler.start()
    logger.info("⏰ Scheduler started")
    
    # Create and run health API
    health_app = create_health_app(config_manager, logging_manager, scheduler)
    
    server_config = config_manager.get_section("server")
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 30886)
    
    logger.info(f"🏥 Health endpoint starting on {host}:{port}")
    
    try:
        # Run Flask app (this blocks)
        health_app.run(host=host, port=port, threaded=True)
    except Exception as e:
        logger.error(f"❌ Health endpoint failed: {e}")
        raise
    finally:
        if scheduler:
            scheduler.shutdown()
        logger.info("👋 Ash-Vault backup service stopped")


if __name__ == "__main__":
    main()
