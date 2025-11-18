# N8N Workflow Integration Guide

This guide shows you how to integrate the Docs2Vector Pipeline with N8N for automated monthly scraping and vector uploads to Pinecone.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [N8N Workflow Setup](#n8n-workflow-setup)
- [Workflow Templates](#workflow-templates)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

The integration uses a simple architecture:

```
┌─────────────────┐
│ N8N Workflow    │
│ (Cron Trigger)  │
└────────┬────────┘
         │
         │ POST /api/v1/trigger-scrape
         ▼
┌─────────────────┐
│ Pipeline API    │
│ (Your Server)   │
└────────┬────────┘
         │
         │ Runs pipeline: scrape → process → chunk → embed → Pinecone
         ▼
┌─────────────────┐
│ Webhook to N8N  │
│ (On Complete)   │
└─────────────────┘
```

**Benefits:**
- ✅ Simple N8N workflow (3-4 nodes only)
- ✅ Pipeline runs independently (reliable)
- ✅ Automatic monthly execution
- ✅ Notification on completion/failure
- ✅ All retry logic in pipeline (not N8N)

---

## Prerequisites

1. **N8N Instance** (self-hosted or cloud)
2. **Pipeline API Running** (see [DEPLOYMENT.md](./DEPLOYMENT.md))
3. **Pipeline API URL** (e.g., `http://your-server.com:8000`)

---

## N8N Workflow Setup

### Step 1: Create New Workflow

1. Open N8N
2. Click **"New Workflow"**
3. Name it: `"Monthly Amazon Scraper to Pinecone"`

### Step 2: Add Cron Trigger

1. Click **"Add first step"**
2. Select **"Schedule Trigger"**
3. Configure:
   - **Mode**: Cron
   - **Expression**: `0 0 1 * *` (1st of every month at midnight)
   - Or use the visual builder: Monthly, Day 1, 00:00

### Step 3: Add HTTP Request Node

1. Click **"+"** after Cron Trigger
2. Select **"HTTP Request"**
3. Name it: `"Trigger Pipeline"`
4. Configure:
   - **Method**: POST
   - **URL**: `http://your-server.com:8000/api/v1/trigger-scrape`
   - **Authentication**: None (or add if you implement auth)
   - **Body Content Type**: JSON
   - **Specify Body**: Using Fields Below
   - **JSON Parameters**:
     - **Name**: `webhook_url`
     - **Value**: `{{ $('Webhook').item.json.webhookUrl }}` (we'll add this webhook next)
     - **Name**: `mode`
     - **Value**: `full`

### Step 4: Add Webhook Node (for completion notification)

1. Go back to the beginning of the workflow
2. Add a parallel branch from start
3. Add **"Webhook"** node
4. Name it: `"Pipeline Complete"`
5. Configure:
   - **HTTP Method**: POST
   - **Path**: `pipeline-complete` (or your choice)
   - **Response Mode**: Immediately
6. **Copy the webhook URL** (looks like: `https://your-n8n.com/webhook/abc123...`)

### Step 5: Update HTTP Request with Webhook URL

1. Go back to **"Trigger Pipeline"** node
2. Update the `webhook_url` field with your actual webhook URL:
   ```
   https://your-n8n.com/webhook/abc123...
   ```

### Step 6: Add Success/Failure Nodes (Optional)

After the **"Pipeline Complete"** webhook:

**Option A: Send Email Notification**
1. Add **"Gmail"** or **"Send Email"** node
2. Configure to send success/failure email

**Option B: Send Slack Message**
1. Add **"Slack"** node
2. Configure channel and message

**Option C: Just Log**
1. Add **"Set"** node to log results
2. View in N8N execution history

---

## Workflow Templates

### Template 1: Simple (Trigger + Wait)

```
[Cron Trigger] → [HTTP: Trigger Pipeline] → [Webhook: Pipeline Complete] → [Email: Notify]
```

**Node Configuration:**

**1. Cron Trigger**
```json
{
  "mode": "cron",
  "cronExpression": "0 0 1 * *"
}
```

**2. HTTP Request: Trigger Pipeline**
```json
{
  "method": "POST",
  "url": "http://your-server.com:8000/api/v1/trigger-scrape",
  "body": {
    "webhook_url": "https://your-n8n.com/webhook/pipeline-complete",
    "mode": "full"
  }
}
```

**3. Webhook: Pipeline Complete**
```json
{
  "httpMethod": "POST",
  "path": "pipeline-complete",
  "responseMode": "immediately"
}
```

**4. Send Email (Gmail example)**
```json
{
  "to": "your-email@example.com",
  "subject": "Pipeline {{ $json.status }}",
  "text": "Job {{ $json.job_id }} {{ $json.status }}\n\nResults:\n{{ JSON.stringify($json.results, null, 2) }}"
}
```

---

### Template 2: Advanced (with Retry and Error Handling)

```
[Cron] → [HTTP: Trigger] 
           ├→ [Success] → [Webhook] → [Slack: Success]
           └→ [Error] → [HTTP: Retry] → [Slack: Error]
```

**Add Error Handling:**

1. After **"Trigger Pipeline"** node
2. Click **"On Error"** at bottom
3. Add **"HTTP Request"** to retry
4. Add **"Slack"** or **"Email"** to notify on failure

---

## Testing

### Test 1: Manual Trigger

1. Open your N8N workflow
2. Click **"Test workflow"** (top right)
3. Click **"Execute Workflow"** on the Cron Trigger node
4. Check execution:
   - ✅ HTTP Request returns job_id
   - ✅ Webhook receives completion notification
   - ✅ Email/Slack notification sent

### Test 2: Check Pipeline API

```bash
# Check API is running
curl http://your-server.com:8000/api/v1/health

# Check job status
curl http://your-server.com:8000/api/v1/status/{job_id}
```

### Test 3: End-to-End

1. Manually trigger N8N workflow
2. Wait for pipeline to complete (10-30 minutes depending on data)
3. Verify:
   - ✅ Webhook received
   - ✅ Data in Pinecone (check via Pinecone console)
   - ✅ Notification received

---

## Example Webhook Payloads

### Success Payload

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
    "pinecone_sync_details": {
      "new_count": 1200,
      "updated_count": 45,
      "unchanged_count": 0
    },
    "storage_mode": "local",
    "success": true
  },
  "error": null
}
```

### Failure Payload

```json
{
  "job_id": "job_20241118_123045",
  "status": "failed",
  "timestamp": "2024-11-18T12:35:15.123456",
  "results": null,
  "error": "Failed to connect to Pinecone: Invalid API key"
}
```

---

## Troubleshooting

### Issue 1: Webhook Not Received

**Symptoms:** Pipeline completes but N8N doesn't receive webhook

**Solutions:**
1. Check webhook URL is correct in HTTP Request node
2. Verify N8N webhook is active (status bar should be green)
3. Check N8N webhook logs for errors
4. Test webhook manually:
   ```bash
   curl -X POST https://your-n8n.com/webhook/abc123 \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   ```

### Issue 2: Pipeline Fails Immediately

**Symptoms:** Job status returns "failed" quickly

**Solutions:**
1. Check API logs: `docker logs docs2vector-api`
2. Verify `.env` configuration (Pinecone keys, etc.)
3. Test API health: `curl http://your-server.com:8000/api/v1/health`
4. Check pipeline can run manually: `python scripts/run_pipeline.py`

### Issue 3: N8N Can't Reach API

**Symptoms:** HTTP Request node fails with connection error

**Solutions:**
1. Verify API is running: `curl http://your-server.com:8000/api/v1/health`
2. Check firewall allows N8N → API traffic
3. If using Docker, ensure correct network configuration
4. Test from N8N server: `curl` from same machine N8N runs on

### Issue 4: Multiple Jobs Running Simultaneously

**Symptoms:** Get 429 error "Another pipeline job is already running"

**Solutions:**
1. Check N8N workflow isn't triggered multiple times
2. Verify only one workflow targets the API
3. Check previous jobs have completed before starting new ones
4. View all jobs: `curl http://your-server.com:8000/api/v1/jobs`

---

## Best Practices

### 1. Schedule During Off-Hours
```
# Run at 2 AM on 1st of month (less traffic)
0 2 1 * *
```

### 2. Add Monitoring
- Use N8N's built-in execution history
- Add Slack/Email notifications
- Monitor API logs

### 3. Handle Failures Gracefully
- Add retry logic in N8N (use "On Error" flows)
- Alert on failures
- Don't retry too aggressively (pipeline is long-running)

### 4. Test Before Production
- Test workflow with "Test workflow" button
- Run manually first time to verify everything works
- Check Pinecone data quality

---

## N8N Workflow JSON (Copy-Paste Ready)

```json
{
  "name": "Monthly Amazon Scraper to Pinecone",
  "nodes": [
    {
      "name": "Cron Trigger",
      "type": "n8n-nodes-base.cronTrigger",
      "parameters": {
        "cronExpression": "0 0 1 * *"
      },
      "position": [250, 300]
    },
    {
      "name": "Trigger Pipeline",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "=http://YOUR_SERVER:8000/api/v1/trigger-scrape",
        "jsonParameters": true,
        "options": {},
        "bodyParametersJson": "={\"webhook_url\": \"YOUR_N8N_WEBHOOK_URL\", \"mode\": \"full\"}"
      },
      "position": [450, 300]
    },
    {
      "name": "Pipeline Complete",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "httpMethod": "POST",
        "path": "pipeline-complete",
        "responseMode": "immediately"
      },
      "position": [250, 500]
    },
    {
      "name": "Send Notification",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "toEmail": "your-email@example.com",
        "subject": "=Pipeline {{ $json.status }}",
        "text": "=Job {{ $json.job_id }} completed with status: {{ $json.status }}"
      },
      "position": [450, 500]
    }
  ],
  "connections": {
    "Cron Trigger": {
      "main": [[{ "node": "Trigger Pipeline", "type": "main", "index": 0 }]]
    },
    "Pipeline Complete": {
      "main": [[{ "node": "Send Notification", "type": "main", "index": 0 }]]
    }
  }
}
```

**To use:**
1. Copy the JSON above
2. In N8N, click **"..."** menu → **"Import from JSON"**
3. Paste and update:
   - Replace `YOUR_SERVER` with your API server URL
   - Replace `YOUR_N8N_WEBHOOK_URL` with your webhook URL
   - Replace email address

---

## Next Steps

- **Deployment**: See [DEPLOYMENT.md](./DEPLOYMENT.md) for deploying the API
- **API Reference**: See [API_INTEGRATION.md](./API_INTEGRATION.md) for full API docs
- **Monitor**: Set up proper monitoring and alerting

