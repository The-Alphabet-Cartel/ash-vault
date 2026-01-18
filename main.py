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
FILE VERSION: v5.0-3-3.5a-1
LAST MODIFIED: 2026-01-09
PHASE: Phase 3 - Backup Infrastructure
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================

This module initializes and runs the Ash-Vault backup service, which:
- Manages ZFS snapshots (daily, weekly, monthly) with retention policies
- Replicates encrypted ZFS streams to Lofn (Tier 2 backup)
- Syncs MinIO data to Backblaze B2 (Tier 1 cloud backup)
- Provides a FastAPI health endpoint for monitoring
- Sends Discord alerts on backup failures

USAGE:
    # Run directly
    python main.py

    # Run with uvicorn (production)
    uvicorn main:app --host 0.0.0.0 --port 30886
"""

import logging
import signal
import sys
import threading
from typing import Optional

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.managers import (
    create_config_manager,
    create_logging_config_manager,
)
from src.jobs import (
    create_snapshot_job,
    create_replication_job,
    create_cloud_sync_job,
)
from src.api.health import create_app

# Module version
__version__ = "v5.0-3-3.5a-1"

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
    schedules = config_manager.get_section("backup_schedules")
    
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
        CronTrigger.from_crontab(schedules.get("replication_lofn", "0 4 * * *")),
        id="replication_lofn",
        name="ZFS Replication to Lofn"
    )
    logger.info(f"📅 Scheduled: Lofn replication at {schedules.get('replication_lofn', '0 4 * * *')}")
    
    # Schedule cloud sync to B2 (5 AM Sunday)
    sched.add_job(
        cloud_sync_job.run,
        CronTrigger.from_crontab(schedules.get("sync_b2", "0 5 * * 0")),
        id="cloud_sync_b2",
        name="Cloud Sync to Backblaze B2"
    )
    logger.info(f"📅 Scheduled: B2 cloud sync at {schedules.get('sync_b2', '0 5 * * 0')}")
    
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
    logging_manager = create_logging_config_manager(config_manager)
    logger = logging_manager.get_logger(__name__)
    
    # Print startup banner
    logger.info("=" * 60)
    logger.info("  Ash-Vault Backup Service")
    logger.info(f"  Version: {__version__}")
    logger.info("  The Alphabet Cartel - discord.gg/alphabetcartel")
    logger.info("=" * 60)
    
    # Log configuration
    zfs_config = config_manager.get_section("zfs")
    replication_config = config_manager.get_section("replication")
    b2_config = config_manager.get_section("b2")
    
    logger.info(f"📁 ZFS Dataset: {zfs_config.get('dataset')}")
    logger.info(f"🔄 Lofn Target: {replication_config.get('lofn_host')}:{replication_config.get('lofn_dataset')}")
    logger.info(f"☁️  B2 Bucket: {b2_config.get('bucket')}")
    
    # Setup scheduler
    global scheduler
    scheduler = setup_scheduler(config_manager, logging_manager)
    scheduler.start()
    logger.info("⏰ Scheduler started")
    
    # Create FastAPI app
    app = create_app(config_manager, logging_manager, scheduler)
    
    # Get server configuration
    server_config = config_manager.get_section("server")
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 30886)
    
    logger.info(f"🏥 Health endpoint starting on {host}:{port}")
    
    try:
        # Run uvicorn server
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="warning",  # Reduce uvicorn logging noise
            access_log=False
        )
    except Exception as e:
        logger.error(f"❌ Server failed: {e}")
        raise
    finally:
        if scheduler:
            scheduler.shutdown()
        logger.info("👋 Ash-Vault backup service stopped")


# Create app instance for uvicorn CLI usage
def create_application():
    """
    Create application for uvicorn CLI.
    
    Usage:
        uvicorn main:app --host 0.0.0.0 --port 30886
    """
    config_manager = create_config_manager()
    logging_manager = create_logging_config_manager(config_manager)
    
    global scheduler
    scheduler = setup_scheduler(config_manager, logging_manager)
    scheduler.start()
    
    return create_app(config_manager, logging_manager, scheduler)


# Application instance for uvicorn
app = None


if __name__ == "__main__":
    main()
