# API Integration Guide

This guide explains how to use the Docs2Vector Pipeline API to trigger and monitor scraping jobs.

## Table of Contents

- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Webhooks](#webhooks)

---

## Quick Start

### 1. Start the API Server

**Local Development:**
```bash
python scripts/run_api_server.py
```

**Using Docker:**
```bash
docker-compose up -d
```

**API will be available at:**
- API Base: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs` (Interactive Swagger UI)

### 2. Trigger a Pipeline Job

```bash
curl -X POST http://localhost:8000/api/v1/trigger-scrape \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://your-n8n.com/webhook/pipeline-complete",
    "mode": "full"
  }'
```

**Response:**
```json
{
  "job_id": "job_20241118_123045",
  "status": "started",
  "message": "Pipeline execution started successfully (mode: full)",
  "timestamp": "2024-11-18T12:30:45.123456"
}
```

### 3. Check Job Status

```bash
curl http://localhost:8000/api/v1/status/job_20241118_123045
```

---

## API Endpoints

### POST `/api/v1/trigger-scrape`

Trigger a new pipeline execution.

**Request Body:**
```json
{
  "webhook_url": "https://your-webhook-url.com",  // Optional
  "mode": "full"  // "full" or "incremental", default: "full"
}
```

**Response:**
```json
{
  "job_id": "job_20241118_123045",
  "status": "started",
  "message": "Pipeline execution started successfully",
  "timestamp": "2024-11-18T12:30:45.123456"
}
```

**Status Codes:**
- `200`: Job started successfully
- `429`: Another job is already running
- `500`: Server error

---

### GET `/api/v1/status/{job_id}`

Check the status of a pipeline job.

**Response (Running):**
```json
{
  "job_id": "job_20241118_123045",
  "status": "running",
  "message": null,
  "results": null,
  "started_at": "2024-11-18T12:30:45.123456",
  "completed_at": null
}
```

**Response (Completed):**
```json
{
  "job_id": "job_20241118_123045",
  "status": "completed",
  "message": null,
  "results": {
    "documents_processed": 150,
    "chunks_created": 1245,
    "embeddings_generated": 1245,
    "chunks_synced_pinecone": 1245,
    "storage_mode": "local",
    "success": true
  },
  "started_at": "2024-11-18T12:30:45.123456",
  "completed_at": "2024-11-18T12:45:30.789012"
}
```

**Status Codes:**
- `200`: Job found
- `404`: Job not found

---

### GET `/api/v1/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "API is running",
  "version": "1.0.0"
}
```

---

### GET `/api/v1/jobs?limit=10`

List recent pipeline jobs.

**Query Parameters:**
- `limit`: Maximum number of jobs to return (default: 10)

**Response:**
```json
{
  "total": 25,
  "limit": 10,
  "jobs": [
    {
      "job_id": "job_20241118_123045",
      "status": "completed",
      "mode": "full",
      "created_at": "2024-11-18T12:30:45.123456",
      "started_at": "2024-11-18T12:30:45.123456",
      "completed_at": "2024-11-18T12:45:30.789012",
      "results": {...}
    },
    ...
  ]
}
```

---

## Usage Examples

### Example 1: Trigger and Wait (Python)

```python
import requests
import time

# 1. Trigger pipeline
response = requests.post(
    "http://localhost:8000/api/v1/trigger-scrape",
    json={"mode": "full"}
)
job_id = response.json()["job_id"]
print(f"Job started: {job_id}")

# 2. Poll for completion
while True:
    status_response = requests.get(
        f"http://localhost:8000/api/v1/status/{job_id}"
    )
    status_data = status_response.json()
    
    print(f"Status: {status_data['status']}")
    
    if status_data["status"] in ["completed", "failed"]:
        print("Results:", status_data.get("results"))
        break
    
    time.sleep(10)  # Check every 10 seconds
```

### Example 2: Trigger with Webhook (curl)

```bash
# Trigger job with webhook notification
curl -X POST http://localhost:8000/api/v1/trigger-scrape \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://your-n8n.com/webhook/abc123",
    "mode": "full"
  }'

# API returns immediately with job_id
# Your webhook will be called when job completes
```

### Example 3: Health Check

```bash
# Simple health check
curl http://localhost:8000/api/v1/health
```

---

## Error Handling

### Common Errors

**1. Another job already running (429)**
```json
{
  "detail": "Another pipeline job is already running. Please wait for it to complete."
}
```

**Solution:** Wait for current job to complete, then retry.

**2. Job not found (404)**
```json
{
  "detail": "Job job_20241118_123045 not found"
}
```

**Solution:** Check job_id is correct.

**3. Configuration error (500)**
```json
{
  "detail": "PINECONE_API_KEY is required when USE_PINECONE is enabled"
}
```

**Solution:** Check your `.env` configuration.

---

## Webhooks

When you provide a `webhook_url` in the trigger request, the API will POST to that URL when the job completes.

### Webhook Payload (Success)

```json
{
  "job_id": "job_20241118_123045",
  "status": "completed",
  "timestamp": "2024-11-18T12:45:30.789012",
  "results": {
    "documents_processed": 150,
    "chunks_created": 1245,
    "embeddings_generated": 1245,
    "chunks_synced_pinecone": 1245,
    "storage_mode": "local",
    "success": true
  },
  "error": null
}
```

### Webhook Payload (Failure)

```json
{
  "job_id": "job_20241118_123045",
  "status": "failed",
  "timestamp": "2024-11-18T12:35:15.123456",
  "results": null,
  "error": "Failed to connect to Pinecone: Invalid API key"
}
```

### Handling Webhooks in N8N

See [N8N_WORKFLOW.md](./N8N_WORKFLOW.md) for detailed N8N integration guide.

---

## Configuration

The API behavior is controlled by environment variables in `.env`:

```bash
# Pinecone (Vector Storage)
USE_PINECONE=true
PINECONE_API_KEY=your-api-key
PINECONE_INDEX_NAME=your-index-name

# Pipeline Mode
PIPELINE_MODE=streaming  # or "batch"
STORAGE_MODE=auto        # "local", "s3", or "auto"

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

See `env.example` for full configuration options.

---

## Next Steps

- **N8N Integration**: See [N8N_WORKFLOW.md](./N8N_WORKFLOW.md)
- **Deployment**: See [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Interactive API Docs**: Visit `http://localhost:8000/docs`

