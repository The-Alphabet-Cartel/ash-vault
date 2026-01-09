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
Health API - Monitoring and Status Endpoint
----------------------------------------------------------------------------
FILE VERSION: v5.0-3-3.5-1
LAST MODIFIED: 2026-01-09
PHASE: Phase 3 - Backup Infrastructure
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================
"""

from datetime import datetime
from typing import Optional

from flask import Flask, jsonify

__version__ = "v5.0-3-3.5-1"

# Store start time for uptime calculation
_start_time: Optional[datetime] = None


def create_health_app(config_manager, logging_manager, scheduler) -> Flask:
    """
    Create Flask application for health endpoint.
    
    Args:
        config_manager: Configuration manager instance
        logging_manager: Logging manager instance
        scheduler: APScheduler instance
    
    Returns:
        Flask application
    """
    global _start_time
    _start_time = datetime.utcnow()
    
    app = Flask(__name__)
    logger = logging_manager.get_logger(__name__)
    
    @app.route("/health", methods=["GET"])
    def health():
        """Basic health check endpoint."""
        return jsonify({
            "status": "healthy",
            "service": "ash-vault-backup",
            "version": __version__,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @app.route("/status", methods=["GET"])
    def status():
        """Detailed status endpoint with job information."""
        # Calculate uptime
        uptime_seconds = 0
        if _start_time:
            uptime_seconds = (datetime.utcnow() - _start_time).total_seconds()
        
        # Get scheduled jobs
        jobs = []
        if scheduler:
            for job in scheduler.get_jobs():
                next_run = job.next_run_time
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": next_run.isoformat() if next_run else None
                })
        
        # Get configuration info
        zfs_config = config_manager.get_section("zfs")
        replication_config = config_manager.get_section("replication")
        cloud_config = config_manager.get_section("cloud")
        
        return jsonify({
            "status": "healthy",
            "service": "ash-vault-backup",
            "version": __version__,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": int(uptime_seconds),
            "scheduler": {
                "running": scheduler.running if scheduler else False,
                "jobs": jobs
            },
            "configuration": {
                "zfs_dataset": zfs_config.get("dataset"),
                "lofn_target": f"{replication_config.get('lofn_host')}:{replication_config.get('lofn_dataset')}",
                "b2_bucket": cloud_config.get("b2_bucket")
            }
        })
    
    @app.route("/", methods=["GET"])
    def root():
        """Root endpoint - redirect info."""
        return jsonify({
            "service": "ash-vault-backup",
            "version": __version__,
            "endpoints": {
                "/health": "Basic health check",
                "/status": "Detailed status with job info"
            }
        })
    
    return app


__all__ = ["create_health_app"]
