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
Health API - FastAPI Monitoring and Status Endpoints
----------------------------------------------------------------------------
FILE VERSION: v5.0-3-3.5a-1
LAST MODIFIED: 2026-01-09
PHASE: Phase 3 - Backup Infrastructure
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ash-vault
============================================================================

This module provides FastAPI endpoints for monitoring the backup service:
- /health - Basic health check (for Docker HEALTHCHECK)
- /status - Detailed status with scheduler information
- / - Service information and available endpoints
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

__version__ = "v5.0-3-3.5a-1"

# Store start time for uptime calculation
_start_time: Optional[datetime] = None

# Create router for health endpoints
router = APIRouter(tags=["health"])


# =============================================================================
# Pydantic Response Models
# =============================================================================


class HealthResponse(BaseModel):
    """Basic health check response."""
    status: str
    service: str
    version: str
    timestamp: str


class ScheduledJob(BaseModel):
    """Information about a scheduled job."""
    id: str
    name: str
    next_run: Optional[str]


class SchedulerInfo(BaseModel):
    """Scheduler status information."""
    running: bool
    jobs: List[ScheduledJob]


class ConfigurationInfo(BaseModel):
    """Configuration summary (safe to expose)."""
    zfs_dataset: Optional[str]
    lofn_target: Optional[str]
    b2_bucket: Optional[str]


class StatusResponse(BaseModel):
    """Detailed status response."""
    status: str
    service: str
    version: str
    timestamp: str
    uptime_seconds: int
    scheduler: SchedulerInfo
    configuration: ConfigurationInfo


class RootResponse(BaseModel):
    """Root endpoint response."""
    service: str
    version: str
    description: str
    endpoints: Dict[str, str]


# =============================================================================
# Global State (set during app creation)
# =============================================================================

_config_manager = None
_logging_manager = None
_scheduler = None


# =============================================================================
# Route Handlers
# =============================================================================


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Basic health check endpoint.
    
    Used by Docker HEALTHCHECK to determine container health.
    Returns 200 OK if the service is running.
    """
    return HealthResponse(
        status="healthy",
        service="ash-vault-backup",
        version=__version__,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    """
    Detailed status endpoint with scheduler and configuration information.
    
    Returns comprehensive status including:
    - Service health
    - Uptime
    - Scheduled jobs and their next run times
    - Configuration summary
    """
    global _start_time, _config_manager, _scheduler
    
    # Calculate uptime
    uptime_seconds = 0
    if _start_time:
        uptime_seconds = int((datetime.utcnow() - _start_time).total_seconds())
    
    # Get scheduled jobs
    jobs: List[ScheduledJob] = []
    scheduler_running = False
    
    if _scheduler:
        scheduler_running = _scheduler.running
        for job in _scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append(ScheduledJob(
                id=job.id,
                name=job.name,
                next_run=next_run.isoformat() if next_run else None
            ))
    
    # Get configuration info (safe subset)
    config_info = ConfigurationInfo(
        zfs_dataset=None,
        lofn_target=None,
        b2_bucket=None
    )
    
    if _config_manager:
        zfs_config = _config_manager.get_section("zfs")
        replication_config = _config_manager.get_section("replication")
        b2_config = _config_manager.get_section("b2")
        
        config_info = ConfigurationInfo(
            zfs_dataset=zfs_config.get("dataset"),
            lofn_target=f"{replication_config.get('lofn_host')}:{replication_config.get('lofn_dataset')}",
            b2_bucket=b2_config.get("bucket")
        )
    
    return StatusResponse(
        status="healthy",
        service="ash-vault-backup",
        version=__version__,
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=uptime_seconds,
        scheduler=SchedulerInfo(
            running=scheduler_running,
            jobs=jobs
        ),
        configuration=config_info
    )


@router.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    """
    Root endpoint - service information and available endpoints.
    """
    return RootResponse(
        service="ash-vault-backup",
        version=__version__,
        description="Ash-Vault Backup Service - Crisis Archive & Backup Infrastructure",
        endpoints={
            "/health": "Basic health check (for Docker HEALTHCHECK)",
            "/status": "Detailed status with scheduler info",
            "/docs": "OpenAPI documentation (Swagger UI)",
            "/redoc": "OpenAPI documentation (ReDoc)"
        }
    )


# =============================================================================
# Application Factory
# =============================================================================


def create_app(
    config_manager: Any,
    logging_manager: Any,
    scheduler: Any = None
) -> FastAPI:
    """
    Create FastAPI application for health endpoint.
    
    Args:
        config_manager: Configuration manager instance
        logging_manager: Logging manager instance
        scheduler: APScheduler instance (optional)
    
    Returns:
        Configured FastAPI application
    """
    global _start_time, _config_manager, _logging_manager, _scheduler
    
    # Store references for route handlers
    _start_time = datetime.utcnow()
    _config_manager = config_manager
    _logging_manager = logging_manager
    _scheduler = scheduler
    
    # Create FastAPI app
    app = FastAPI(
        title="Ash-Vault Backup Service",
        description="Crisis Archive & Backup Infrastructure - Health & Status API",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Include health router
    app.include_router(router)
    
    logger = logging_manager.get_logger(__name__)
    logger.info(f"✅ FastAPI health app created (version {__version__})")
    
    return app


__all__ = ["create_app", "router", "HealthResponse", "StatusResponse"]
