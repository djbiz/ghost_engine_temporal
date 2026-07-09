#!/usr/bin/env python3
"""
GhostEngine Temporal Client
Triggers Ghost Engine workflows on Temporal Cloud using the Python SDK.

Usage:
    python ghost_engine_temporal_client.py health
    python ghost_engine_temporal_client.py list
    python ghost_engine_temporal_client.py pipelineRollup [date]
    python ghost_engine_temporal_client.py ghostEngineCampaign [leadCount]
    python ghost_engine_temporal_client.py linkedInOutreach [batch]
"""
import os, sys, asyncio, argparse, datetime

# ── Load API key from Hermes config ─────────────────────────────────────────────
def get_api_key():
    for path in [r"C:\Users\starw\AppData\Local\hermes\.env", r"C:\Users\starw\AppData\Local\hermes\config.yaml"]:
        if os.path.exists(path):
            with open(path, "rb") as f:
                for line in f:
                    if b"TEMPORAL_API_KEY" in line:
                        parts = line.split(b"=", 1)
                        if len(parts) == 2:
                            return parts[1].strip().decode("utf-8", errors="replace")
    return ""

# ── Temporal config ─────────────────────────────────────────────────────────────
TEMPORAL_ADDRESS   = "ap-northeast-1.aws.api.temporal.io:7233"
TEMPORAL_NAMESPACE = "quickstart-derekjami-878d5147.kydxq"
TASK_QUEUE         = "ghost-engine-campaigns"

API_KEY = get_api_key()
if not API_KEY:
    print("ERROR: TEMPORAL_API_KEY not set. Run: hermes config set TEMPORAL_API_KEY '...'")
    sys.exit(1)

if API_KEY.count(".") != 2:
    print(f"WARNING: API key has {API_KEY.count('.')} dots (expected 3 parts = 2 dots)")

# ── Temporal Client ─────────────────────────────────────────────────────────────
async def get_client():
    from temporalio.client import Client
    return await Client.connect(
        TEMPORAL_ADDRESS,
        namespace=TEMPORAL_NAMESPACE,
        api_key=API_KEY,
        tls=True,
    )

# ── Workflow triggers ───────────────────────────────────────────────────────────
async def health_check():
    client = await get_client()
    print(f"✓ Connected to Temporal Cloud")
    print(f"  Namespace : {client.namespace}")
    print(f"  Address   : {TEMPORAL_ADDRESS}")
    print(f"  Task Queue: {TASK_QUEUE}")
    return True

async def list_workflows(limit=10):
    client = await get_client()
    from temporalio.api.workflowservice.v1 import ListWorkflowExecutionsRequest
    # Access via client._service (internal) or just show the handle info
    try:
        service = getattr(client, "_service", None) or getattr(client, "service", None)
        if service is None:
            # Fallback: iterate via list on the workflow handle
            count = 0
            print(f"Recent workflows (last {limit}):")
            print("  (listing requires worker to be connected — workflows do execute)")
    except Exception as e:
        print(f"Note: {e}")

async def trigger_pipeline_rollup(date_str: str = ""):
    """pipelineRollup — daily Slack pipeline digest (start only, don't wait)"""
    from datetime import date
    d = date_str or date.today().isoformat()
    wid = f"daily-pipeline-rollup-{d}"
    client = await get_client()
    handle = await client.start_workflow(
        "PipelineRollup",
        d,
        id=wid,
        task_queue=TASK_QUEUE,
    )
    print(f"✓ pipelineRollup started: {wid}")
    print(f"  Run ID: {handle.first_execution_run_id}")

async def trigger_ghost_engine_campaign(lead_count: int = 50):
    """ghostEngineCampaign — full lead gen → content → outreach (start only)"""
    import uuid
    batch_id = uuid.uuid4().hex[:8]
    wid = f"ghost-engine-campaign-{batch_id}"
    client = await get_client()
    handle = await client.start_workflow(
        "GhostEngineCampaign",
        {"leadCount": lead_count, "batchId": batch_id},
        id=wid,
        task_queue=TASK_QUEUE,
    )
    print(f"✓ ghostEngineCampaign started: {wid}")
    print(f"  Run ID: {handle.first_execution_run_id}")
    print(f"  → Worker will process in background (task queue: {TASK_QUEUE})")

async def trigger_linkedin_outreach(batch: int = 1):
    """linkedInOutreach — batch LinkedIn outreach (start only)"""
    wid = f"linkedin-outreach-apr11-{batch}"
    client = await get_client()
    handle = await client.start_workflow(
        "LinkedInOutreach",
        {"batch": batch, "leadsPerBatch": 25},
        id=wid,
        task_queue=TASK_QUEUE,
    )
    print(f"✓ linkedInOutreach batch {batch} started: {wid}")
    print(f"  Run ID: {handle.first_execution_run_id}")

# ── CLI ───────────────────────────────────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser(description="GhostEngine Temporal Client")
    parser.add_argument("command", nargs="?", default="help")
    parser.add_argument("args",    nargs="*")
    ns = parser.parse_args(sys.argv[1:])

    cmd  = ns.command
    args = ns.args

    if cmd == "health":
        await health_check()
    elif cmd == "list":
        limit = int(args[0]) if args else 10
        await list_workflows(limit)
    elif cmd == "pipelineRollup":
        d = args[0] if args else datetime.date.today().isoformat()
        await trigger_pipeline_rollup(d)
    elif cmd == "ghostEngineCampaign":
        count = int(args[0]) if args else 50
        await trigger_ghost_engine_campaign(count)
    elif cmd == "linkedInOutreach":
        batch = int(args[0]) if args else 1
        await trigger_linkedin_outreach(batch)
    else:
        print(__doc__)

if __name__ == "__main__":
    asyncio.run(main())
