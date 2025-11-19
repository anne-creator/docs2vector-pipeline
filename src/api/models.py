"""Pydantic models for API requests and responses."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class TriggerRequest(BaseModel):
    """Request model for triggering pipeline execution."""
    
    webhook_url: Optional[str] = Field(
        None,
        description="Optional webhook URL to call when pipeline completes"
    )
    

class TriggerResponse(BaseModel):
    """Response model for trigger endpoint."""
    
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: 'started', 'failed'")
    message: str = Field(..., description="Status message")
    timestamp: str = Field(..., description="ISO timestamp when job was triggered")


class StatusResponse(BaseModel):
    """Response model for status endpoint."""
    
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status: 'running', 'completed', 'failed', 'not_found'")
    message: Optional[str] = Field(None, description="Status or error message")
    results: Optional[Dict[str, Any]] = Field(None, description="Pipeline results if completed")
    started_at: Optional[str] = Field(None, description="ISO timestamp when job started")
    completed_at: Optional[str] = Field(None, description="ISO timestamp when job completed")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str = Field(..., description="Health status: 'healthy' or 'unhealthy'")
    message: str = Field(..., description="Health status message")
    version: str = Field(..., description="API version")


class WebhookPayload(BaseModel):
    """Payload sent to webhook URL on pipeline completion."""
    
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="'completed' or 'failed'")
    timestamp: str = Field(..., description="ISO timestamp when pipeline completed")
    results: Optional[Dict[str, Any]] = Field(None, description="Pipeline execution results")
    error: Optional[str] = Field(None, description="Error message if failed")

