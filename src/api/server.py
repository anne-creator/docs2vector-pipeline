"""FastAPI server for pipeline API."""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import requests

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    TriggerRequest,
    TriggerResponse,
    StatusResponse,
    HealthResponse,
    WebhookPayload
)
from src.pipeline.orchestrator import PipelineOrchestrator
from config.settings import Settings

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Docs2Vector Pipeline API",
    description="API for triggering and monitoring document scraping and vectorization pipeline",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (use Redis/DB for production)
jobs: Dict[str, Dict[str, Any]] = {}

# Thread pool for running pipeline in background
executor = ThreadPoolExecutor(max_workers=1)  # Only allow 1 concurrent pipeline execution


def generate_job_id() -> str:
    """Generate unique job ID."""
    return f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def notify_webhook(webhook_url: str, payload: WebhookPayload) -> None:
    """
    Send notification to webhook URL.
    
    Args:
        webhook_url: Webhook URL to POST to
        payload: Payload to send
    """
    try:
        logger.info(f"Sending webhook notification to: {webhook_url}")
        response = requests.post(
            webhook_url,
            json=payload.dict(),
            timeout=30
        )
        response.raise_for_status()
        logger.info(f"✅ Webhook notification sent successfully")
    except Exception as e:
        logger.error(f"❌ Failed to send webhook notification: {e}")


def run_pipeline_sync(job_id: str, mode: str, webhook_url: Optional[str]) -> None:
    """
    Run pipeline synchronously in background thread.
    
    Args:
        job_id: Job identifier
        mode: Pipeline mode ('full' or 'incremental')
        webhook_url: Optional webhook URL to notify on completion
    """
    try:
        logger.info(f"🚀 Starting pipeline execution for job: {job_id}")
        
        # Update job status
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = datetime.now().isoformat()
        
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Run pipeline
        if mode == "incremental":
            results = orchestrator.run_incremental_update()
        else:
            results = orchestrator.run_full_pipeline()
        
        # Update job with results
        jobs[job_id]["status"] = "completed" if results.get("success") else "failed"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["results"] = results
        
        if not results.get("success"):
            jobs[job_id]["error"] = results.get("error", "Unknown error")
        
        logger.info(f"✅ Pipeline execution completed for job: {job_id}")
        
        # Send webhook notification if provided
        if webhook_url:
            webhook_payload = WebhookPayload(
                job_id=job_id,
                status=jobs[job_id]["status"],
                timestamp=jobs[job_id]["completed_at"],
                results=results if results.get("success") else None,
                error=jobs[job_id].get("error")
            )
            notify_webhook(webhook_url, webhook_payload)
        
    except Exception as e:
        logger.exception(f"❌ Pipeline execution failed for job: {job_id}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["error"] = str(e)
        
        # Send webhook notification on failure
        if webhook_url:
            webhook_payload = WebhookPayload(
                job_id=job_id,
                status="failed",
                timestamp=jobs[job_id]["completed_at"],
                error=str(e)
            )
            notify_webhook(webhook_url, webhook_payload)


@app.post(
    "/api/v1/trigger-scrape",
    response_model=TriggerResponse,
    summary="Trigger pipeline execution",
    description="Trigger a new pipeline execution. Returns immediately with job ID."
)
async def trigger_scrape(request: TriggerRequest, background_tasks: BackgroundTasks):
    """
    Trigger pipeline execution.
    
    The pipeline runs in the background and the job ID is returned immediately.
    Use the /status/{job_id} endpoint to check progress.
    """
    try:
        # Check if another job is running
        running_jobs = [job for job in jobs.values() if job["status"] == "running"]
        if running_jobs:
            raise HTTPException(
                status_code=429,
                detail="Another pipeline job is already running. Please wait for it to complete."
            )
        
        # Generate job ID
        job_id = generate_job_id()
        
        # Create job record
        jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "mode": request.mode,
            "webhook_url": request.webhook_url,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "results": None,
            "error": None
        }
        
        # Start pipeline in background
        background_tasks.add_task(
            run_pipeline_sync,
            job_id,
            request.mode,
            request.webhook_url
        )
        
        logger.info(f"Pipeline job triggered: {job_id}")
        
        return TriggerResponse(
            job_id=job_id,
            status="started",
            message=f"Pipeline execution started successfully (mode: {request.mode})",
            timestamp=jobs[job_id]["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/v1/status/{job_id}",
    response_model=StatusResponse,
    summary="Check job status",
    description="Check the status of a pipeline execution job"
)
async def get_status(job_id: str):
    """
    Get status of a pipeline job.
    
    Returns job status, results if completed, or error if failed.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = jobs[job_id]
    
    return StatusResponse(
        job_id=job_id,
        status=job["status"],
        message=job.get("error") if job["status"] == "failed" else None,
        results=job.get("results"),
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at")
    )


@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the API is running"
)
async def health_check():
    """
    Health check endpoint.
    
    Returns API health status and version.
    """
    return HealthResponse(
        status="healthy",
        message="API is running",
        version="1.0.0"
    )


@app.get(
    "/api/v1/jobs",
    summary="List all jobs",
    description="List all pipeline jobs (recent first)"
)
async def list_jobs(limit: int = 10):
    """
    List recent pipeline jobs.
    
    Args:
        limit: Maximum number of jobs to return (default: 10)
    """
    # Sort jobs by created_at descending
    sorted_jobs = sorted(
        jobs.values(),
        key=lambda x: x["created_at"],
        reverse=True
    )
    
    return {
        "total": len(sorted_jobs),
        "limit": limit,
        "jobs": sorted_jobs[:limit]
    }


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("=" * 70)
    logger.info("🚀 Docs2Vector Pipeline API Starting")
    logger.info(f"   Storage Mode: {Settings.STORAGE_MODE}")
    logger.info(f"   Pipeline Mode: {Settings.PIPELINE_MODE}")
    logger.info(f"   Pinecone: {'Enabled' if Settings.USE_PINECONE else 'Disabled'}")
    logger.info("=" * 70)
    
    # Validate settings
    if not Settings.validate():
        logger.error("❌ Configuration validation failed!")
        raise RuntimeError("Invalid configuration")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("👋 Docs2Vector Pipeline API Shutting Down")
    executor.shutdown(wait=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

