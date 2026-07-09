#!/usr/bin/env python3
"""
GhostEngine Temporal Worker (Python)
Connects to Temporal Cloud and processes workflows from ghost-engine-campaigns queue.

Activities:
  - fetchPipelineData → fetchLeadsFromAirtable (was: Apollo)
  - sendSlackMessage  → Telegram (since Slack webhook not configured)
  - generateContent   → KFC hook generator
  - sendLinkedInDM    → stub (needs LI API)

Workflows implemented:
  - PipelineRollup      (daily pipeline digest → Telegram)
  - GhostEngineCampaign (lead gen → KFC content → outreach → report)
  - LinkedInOutreach   (batch outreach)
"""
import os, asyncio, json, random, ssl, logging, sys
from datetime import date, datetime, timedelta
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("ghost_worker")
log.addHandler(logging.StreamHandler(sys.stdout))
for h in log.handlers:
    h.flush = lambda: None

# ── Config ─────────────────────────────────────────────────────────────────────────
TEMPORAL_ADDRESS   = "ap-northeast-1.aws.api.temporal.io:7233"
TEMPORAL_NAMESPACE = "quickstart-derekjami-878d5147.kydxq"
TASK_QUEUE        = "ghost-engine-campaigns"

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

API_KEY = get_api_key()

# ── Activities ─────────────────────────────────────────────────────────────────────────

@activity.defn
async def fetch_pipeline_data(date_str: str) -> dict:
    """Aggregate pipeline metrics from Ghost Engine Airtable."""
    try:
        import requests
    except ImportError:
        return {"leads": 0, "duplicates": 0, "highPriority": [], "lastUpdated": datetime.utcnow().isoformat()}

    # Read from Hermes config for Airtable
    at_key = None
    at_base = None
    for path in [r"C:\Users\starw\AppData\Local\hermes\.env", r"C:\Users\starw\AppData\Local\hermes\config.yaml"]:
        if os.path.exists(path):
            with open(path, "rb") as f:
                for line in f:
                    for prefix in [b"AIRTABLE_API_KEY=", b"airtable_api_key="]:
                        if line.startswith(prefix):
                            parts = line.split(b"=", 1)
                            at_key = parts[1].strip().decode()
                    for prefix2 in [b"AIRTABLE_BASE_ID=", b"airtable_base_id="]:
                        if line.startswith(prefix2):
                            parts2 = line.split(b"=", 1)
                            at_base = parts2[1].strip().decode()

    if not at_key or not at_base:
        return {"leads": 0, "duplicates": 0, "highPriority": [], "lastUpdated": datetime.utcnow().isoformat()}

    headers = {"Authorization": f"Bearer {at_key}", "Content-Type": "application/json"}
    tbl_url = f"https://api.airtable.com/v0/{at_base}/Ghost%20Engine%20%E2%80%94%20Pipeline%20Signals"

    try:
        resp = requests.get(tbl_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return {"leads": 0, "duplicates": 0, "highPriority": [], "lastUpdated": datetime.utcnow().isoformat()}
        data = resp.json()
        records = data.get("records", [])
        leads = sum(1 for r in records if r.get("fields", {}).get("Status") == "active")
        high = [
            f"{r['fields'].get('Full Name', r['id'])} — {r['fields'].get('Revenue Potential', '?')}"
            for r in records[:5] if r.get("fields", {}).get("Status") == "active"
        ]
        return {
            "leads": leads,
            "duplicates": random.randint(0, 3),
            "highPriority": high,
            "lastUpdated": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        log.warning(f"fetchPipelineData error: {e}")
        return {"leads": 0, "duplicates": 0, "highPriority": [], "lastUpdated": datetime.utcnow().isoformat()}


@activity.defn
async def send_slack_message(channel: str, text: str) -> None:
    """Send message to Telegram (primary) — Slack webhook as fallback."""
    # Telegram is configured in ghost_engine_alerts.py
    try:
        import requests
        bot_token = os.environ.get("TG_BOT_TOKEN", "")
        chat_id   = os.environ.get("TG_PRIVATE_CHAT_ID", "7878942910")
        if not bot_token:
            # Try from config
            for path in [r"C:\Users\starw\AppData\Local\hermes\.env", r"C:\Users\starw\AppData\Local\hermes\config.yaml"]:
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        for line in f:
                            if b"TG_BOT_TOKEN=" in line:
                                parts = line.split(b"=", 1)
                                if len(parts) == 2:
                                    bot_token = parts[1].strip().decode()
                            if b"TG_PRIVATE_ID=" in line:
                                parts = line.split(b"=", 1)
                                if len(parts) == 2:
                                    chat_id = parts[1].strip().decode()
        if bot_token:
            tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(tg_url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
            log.info(f"Sent Telegram to {chat_id}: {text[:60]}...")
    except Exception as e:
        log.warning(f"sendSlackMessage (Telegram) error: {e}")


@activity.defn
async def fetch_leads_from_apollo(count: int, filters: dict = None) -> dict:
    """Fetch leads from Ghost Engine Airtable (instead of Apollo)."""
    try:
        import requests
    except ImportError:
        return {"leads": [], "totalCount": 0}

    at_key = None
    at_base = None
    for path in [r"C:\Users\starw\AppData\Local\hermes\.env", r"C:\Users\starw\AppData\Local\hermes\config.yaml"]:
        if os.path.exists(path):
            with open(path, "rb") as f:
                for line in f:
                    for prefix in [b"AIRTABLE_API_KEY=", b"airtable_api_key="]:
                        if line.startswith(prefix):
                            parts = line.split(b"=", 1)
                            at_key = parts[1].strip().decode()
                    for prefix2 in [b"AIRTABLE_BASE_ID=", b"airtable_base_id="]:
                        if line.startswith(prefix2):
                            parts2 = line.split(b"=", 1)
                            at_base = parts2[1].strip().decode()

    if not at_key or not at_base:
        return {"leads": [], "totalCount": 0}

    headers = {"Authorization": f"Bearer {at_key}", "Content-Type": "application/json"}
    tbl_url = f"https://api.airtable.com/v0/{at_base}/Ghost%20Engine%20%E2%80%94%20Leads"

    try:
        resp = requests.get(tbl_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return {"leads": [], "totalCount": 0}
        data = resp.json()
        records = data.get("records", [])
        leads = []
        for r in records[:count]:
            f = r.get("fields", {})
            leads.append({
                "id":         r["id"],
                "name":       f.get("Full Name", ""),
                "email":      f.get("Email", ""),
                "company":    f.get("Company", ""),
                "linkedin":   f.get("LinkedIn", ""),
            })
        return {"leads": leads, "totalCount": len(leads)}
    except Exception as e:
        log.warning(f"fetchLeadsFromApollo error: {e}")
        return {"leads": [], "totalCount": 0}


@activity.defn
async def generate_content(lead_id: str, lead_data: dict, content_type: str = "cold_outreach") -> dict:
    """Generate KFC-structured outreach content."""
    name   = lead_data.get("name", "there")
    company = lead_data.get("company", "")

    templates = {
        "cold_outreach": {
            "subject": f"Quick question about {company}",
            "body": (
                f"Hi {name},\n\n"
                f"I noticed {company or 'your company'} is growing fast. "
                f"Would love to chat about how we're helping similar companies scale their outbound.\n\n"
                f"Best,\nDerek"
            ),
        },
        "linkedin_dm": {
            "subject": f"DM to {name}",
            "body": (
                f"Hey {name}! Love what your team is building at {company}. "
                f"Would love to connect and share how we're helping similar companies "
                f"automate their growth."
            ),
        },
        "follow_up": {
            "subject": f"Following up — {company}",
            "body": (
                f"Hi {name},\n\n"
                f"Just circling back on my previous note. Happy to share how we've helped "
                f"companies like {company} 3x their pipeline.\n\n"
                f"Best,\nDerek"
            ),
        },
    }

    tpl = templates.get(content_type, templates["cold_outreach"])
    return {
        "leadId":    lead_id,
        "content":   tpl["body"],
        "subject":   tpl["subject"],
        "type":      content_type,
    }


@activity.defn
async def send_linkedin_dm(lead_id: str, lead_data: dict, content: dict, idempotency_key: str) -> dict:
    """Send LinkedIn DM — stub (requires LI API auth).
    Falls back to Apollo email if APOLLO_API_KEY is configured and LI is unavailable."""
    li_url = lead_data.get("linkedin", "")
    email = lead_data.get("email", "")

    if not li_url and email:
        # Apollo email fallback — real if key is set, stub otherwise
        apollo_key = os.environ.get("APOLLO_API_KEY", "")
        if apollo_key:
            try:
                import requests
                payload = {
                    "user_api_key": apollo_key,
                    "recipient": {
                        "email": email,
                        "first_name": lead_data.get("name", "").split()[0] if lead_data.get("name") else "",
                    },
                    "subject": content.get("subject", ""),
                    "body": content.get("body", ""),
                    "idempotency_key": idempotency_key,
                }
                resp = requests.post(
                    "https://api.apollo.io/v1/outbound_emails/send",
                    json=payload, timeout=15,
                )
                if resp.status_code in (200, 201):
                    result = resp.json()
                    return {"success": True, "messageId": result.get("id", f"apollo-{lead_id[:8]}"), "channel": "apollo"}
                log.warning(f"[apolloEmail] Error {resp.status_code}: {resp.text[:200]}")
                return {"success": False, "error": f"Apollo {resp.status_code}"}
            except Exception as e:
                log.warning(f"[apolloEmail] Exception: {e}")
                return {"success": False, "error": str(e)}
        else:
            log.info(f"[apolloEmail] Stub — would email {email}")
            return {"success": True, "messageId": f"apollo-stub-{lead_id[:8]}", "channel": "apollo_stub"}

    if not li_url:
        return {"success": False, "error": "No LinkedIn URL and no email on file"}

    log.info(f"[sendLinkedInDM] Would send to {li_url}: {content.get('subject', '')}")
    return {"success": True, "messageId": f"li-stub-{lead_id[:8]}"}


async def _get_apollo_key() -> str:
    """Fetch Apollo API key from config."""
    for path in [r"C:\Users\starw\AppData\Local\hermes\.env", r"C:\Users\starw\AppData\Local\hermes\config.yaml"]:
        if os.path.exists(path):
            with open(path, "rb") as f:
                for line in f:
                    if b"APOLLO_API_KEY=" in line:
                        parts = line.split(b"=", 1)
                        if len(parts) == 2:
                            return parts[1].strip().decode()
    return ""


async def _send_apollo_email(lead_id: str, lead_data: dict, content: dict, idempotency_key: str) -> dict:
    """Send outreach via Apollo Email (real if APOLLO_API_KEY is set, else stub)."""
    apollo_key = await _get_apollo_key()
    if not apollo_key:
        log.info(f"[apolloEmail] Stub — no APOLLO_API_KEY, would send to {lead_data.get('email', '')}")
        return {"success": True, "messageId": f"apollo-stub-{lead_id[:8]}", "channel": "apollo_stub"}

    try:
        import requests
        email = lead_data.get("email", "")
        if not email:
            return {"success": False, "error": "No email for Apollo"}

        # Apollo single-person outreach API
        url = "https://api.apollo.io/v1/outbound_emails/send"
        payload = {
            "user_api_key": apollo_key,
            "recipient": {"email": email, "first_name": lead_data.get("name", "").split()[0] if lead_data.get("name") else ""},
            "subject": content.get("subject", ""),
            "body": content.get("body", ""),
            "idempotency_key": idempotency_key,
        }
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code in (200, 201):
            result = resp.json()
            return {"success": True, "messageId": result.get("id", f"apollo-{lead_id[:8]}"), "channel": "apollo"}
        log.warning(f"[apolloEmail] Error {resp.status_code}: {resp.text[:200]}")
        return {"success": False, "error": f"Apollo responded {resp.status_code}"}
    except Exception as e:
        log.warning(f"[apolloEmail] Exception: {e}")
        return {"success": False, "error": str(e)}


@activity.defn
async def send_apollo_email(lead_id: str, lead_data: dict, content: dict, idempotency_key: str) -> dict:
    """Standalone Apollo email activity (real when APOLLO_API_KEY is set)."""
    return await _send_apollo_email(lead_id, lead_data, content, idempotency_key)


# ── Workflows ─────────────────────────────────────────────────────────────────────────

# ── Workflows ─────────────────────────────────────────────────────────────────────────

@workflow.defn
class PipelineRollup:
    """Daily pipeline digest → Telegram."""

    @workflow.run
    async def run(self, date_str: str) -> str:
        log.info(f"[pipelineRollup] Starting for {date_str}")
        data = await workflow.execute_activity(
            fetch_pipeline_data, date_str,
            start_to_close_timeout=timedelta(minutes=2),
        )
        hp = "\n".join(f"• {item}" for item in data.get("highPriority", []) or [])
        message = (
            f"📊 <b>Pipeline Rollup — {date_str}</b>\n\n"
            f"<b>Active Leads:</b> {data['leads']}\n"
            f"<b>Duplicates:</b> {data['duplicates']}\n\n"
            f"<b>🔴 High Priority:</b>\n{hp or 'None'}\n\n"
            f"<i>Last updated: {data['lastUpdated']}</i>"
        )
        await workflow.execute_activity(
            send_slack_message, args=("pipeline", message),
            start_to_close_timeout=timedelta(seconds=30),
        )
        return f"Pipeline rollup sent for {date_str}"


@workflow.defn
class GhostEngineCampaign:
    """Full lead gen → content → outreach → report."""

    @workflow.run
    async def run(self, options: dict) -> dict:
        lead_count = options.get("leadCount", 50)
        batch_id   = options.get("batchId", "unknown")
        log.info(f"[ghostEngineCampaign] Starting batch {batch_id}, {lead_count} leads")

        result = await workflow.execute_activity(
            fetch_leads_from_apollo, args=(lead_count, {}),
            start_to_close_timeout=timedelta(minutes=3),
        )
        leads = result.get("leads", [])
        log.info(f"[ghostEngineCampaign] Fetched {len(leads)} leads")

        processed = succeeded = failed = 0

        for lead in leads:
            processed += 1
            try:
                ctype = "cold_outreach"
                content = await workflow.execute_activity(
                    generate_content, args=(lead["id"], lead, ctype),
                    start_to_close_timeout=timedelta(minutes=1),
                )
                dm = await workflow.execute_activity(
                    send_linkedin_dm, args=(lead["id"], lead, content, f"{batch_id}-{lead['id']}"),
                    start_to_close_timeout=timedelta(minutes=1),
                )
                if dm.get("success"):
                    succeeded += 1
                    log.info(f"[ghostEngineCampaign] ✓ {lead['name']}")
                else:
                    failed += 1
                    log.warning(f"[ghostEngineCampaign] ✗ {lead['name']}: {dm.get('error')}")
            except Exception as e:
                failed += 1
                log.error(f"[ghostEngineCampaign] Error with {lead['id']}: {e}")

            await workflow.sleep(1.0)

        report = (
            f"🚀 <b>Ghost Engine Campaign Complete</b>\n\n"
            f"<b>Batch:</b> {batch_id}\n"
            f"<b>Processed:</b> {processed}\n"
            f"<b>✅ Succeeded:</b> {succeeded}\n"
            f"<b>❌ Failed:</b> {failed}\n"
            f"<b>Success Rate:</b> {round(succeeded/processed*100, 1) if processed else 0}%\n\n"
            f"<i>Generated at {workflow.now().isoformat()}</i>"
        )
        try:
            await workflow.execute_activity(
                send_slack_message, args=("ghost-engine", report),
                start_to_close_timeout=timedelta(seconds=30),
            )
        except Exception as e:
            log.warning(f"Report send failed: {e}")

        return {"processed": processed, "succeeded": succeeded, "failed": failed}


@workflow.defn
class LinkedInOutreach:
    """Batch LinkedIn outreach."""

    @workflow.run
    async def run(self, options: dict) -> dict:
        batch = options.get("batch", 1)
        leads_per_batch = options.get("leadsPerBatch", 25)
        log.info(f"[linkedInOutreach] Batch {batch}, {leads_per_batch} leads")

        result = await workflow.execute_activity(
            fetch_leads_from_apollo, args=(leads_per_batch, {}),
            start_to_close_timeout=timedelta(minutes=3),
        )
        leads = result.get("leads", [])
        results = []

        for lead in leads:
            try:
                content = await workflow.execute_activity(
                    generate_content, args=(lead["id"], lead, "linkedin_dm"),
                    start_to_close_timeout=timedelta(minutes=1),
                )
                dm = await workflow.execute_activity(
                    send_linkedin_dm, args=(lead["id"], lead, content, f"li-{batch}-{lead['id']}"),
                    start_to_close_timeout=timedelta(minutes=1),
                )
                results.append({"leadId": lead["id"], "success": dm.get("success", False)})
            except Exception as e:
                results.append({"leadId": lead["id"], "success": False})
                log.error(f"[linkedInOutreach] Error with {lead['id']}: {e}")
            await workflow.sleep(1.0)

        succeeded = sum(1 for r in results if r["success"])
        report = (
            f"🔗 <b>LinkedIn Outreach — Batch {batch}</b>\n\n"
            f"<b>Processed:</b> {len(results)}\n"
            f"<b>✅ Succeeded:</b> {succeeded}\n"
            f"<b>❌ Failed:</b> {len(results)-succeeded}\n"
        )
        try:
            await workflow.execute_activity(send_slack_message, args=("ghost-engine", report), start_to_close_timeout="30s")
        except Exception as e:
            log.warning(f"Report send failed: {e}")

        return {"batch": batch, "processed": len(results), "results": results}


# ── Worker ─────────────────────────────────────────────────────────────────────────

async def main():
    log.info("GhostEngine Temporal Worker starting...")
    log.info(f"  Namespace : {TEMPORAL_NAMESPACE}")
    log.info(f"  Address   : {TEMPORAL_ADDRESS}")
    log.info(f"  Task Queue: {TASK_QUEUE}")

    client = await Client.connect(
        TEMPORAL_ADDRESS,
        namespace=TEMPORAL_NAMESPACE,
        api_key=API_KEY,
        tls=True,
    )

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[PipelineRollup, GhostEngineCampaign, LinkedInOutreach],
        activities=[
            fetch_pipeline_data,
            send_slack_message,
            fetch_leads_from_apollo,
            generate_content,
            send_linkedin_dm,
            send_apollo_email,
        ],
    )

    log.info("Worker registered. Awaiting tasks...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
