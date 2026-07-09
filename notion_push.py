import urllib.request, json, urllib.error

key = "ntn_58...GcJ7"
page_id = "391dbc2b-713e-8155-805e-fabde075cf8d"

NOTION_URL = "https://api.notion.com/v1"
headers = {"Authorization": f"Bearer {key}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}

def api(path, method="GET", data=None):
    url = f"{NOTION_URL}{path}"
    payload = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def append_blocks(children):
    return api(f"/blocks/{page_id}/children", method="PATCH", data={"children": children})

# ── Block 1: System Status ──────────────────────────────────────────────
block1 = {
    "object": "block", "type": "callout",
    "callout": {
        "rich_text": [{"type": "text", "text": {"content": "LIVE MARKET OPEN SCREEN — Last refresh: 2026-07-02 | All systems nominal"}}],
        "icon": {"emoji": "📊"}, "color": "blue_bg"
    }
}

# ── Block 2: Signal Registry ────────────────────────────────────────────
block2_header = {
    "object": "block", "type": "heading_2",
    "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Signal Registry (Governance)"}}]}
}

signal_rows = [
    ["SIG-001", "EXP-001", "AUM > $10M threshold", "ACTIVE", "DM channel events", "High"],
    ["SIG-002", "EXP-002", "CPA < $47", "ACTIVE", "Ad pixel conversions", "High"],
    ["SIG-003", "EXP-001", "Retention rate > 82%", "TESTING", "Cohort analysis", "Medium"],
    ["SIG-004", "EXP-002", "LTV > $1,200", "TESTING", "Stripe + HubSpot", "Medium"],
    ["SIG-005", "EXP-001", "NTF alert (free trial)", "INACTIVE", "Firebase anon sig", "Low"],
    ["SIG-006", "EXP-002", "Churn spike > 15% in 7d", "INACTIVE", "Stripe subscription events", "Medium"],
    ["SIG-007", "EXP-001", "Sales cycle < 18 days", "INACTIVE", "CRM close date delta", "Low"],
]

signal_table = {
    "object": "block", "type": "table",
    "table": {
        "table_width": 6,
        "has_column_header": True,
        "has_row_header": False,
        "children": [
            {"object": "block", "type": "table_row", "table_row": {
                "cells": [["Signal ID"], ["Experiment"], ["Trigger Rule"], ["Status"], ["Data Source"], ["Priority"]]
            }},
            *[{"object": "block", "type": "table_row", "table_row": {"cells": [row]}} for row in signal_rows]
        ]
    }
}

# ── Block 3: Rule Engine ─────────────────────────────────────────────────
block3_header = {
    "object": "block", "type": "heading_2",
    "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Rule Engine (6 Immutable Laws)"}}]}
}

laws = [
    ("Law 1", "Uncertainty Gate", "IF uncertainty > threshold THEN block_all_inference()"),
    ("Law 2", "Calibration Lock", "IF calibration != learning_safe THEN lock_calibration()"),
    ("Law 3", "Drift Arming", "IF drift_score > 0.7 THEN arm_drift_layer()"),
    ("Law 4", "Experiment Isolation", "IF experiment.status != ACTIVE THEN skip_signal()"),
    ("Law 5", "Numeric Output Guard", "IF system_state == insufficient_data THEN deny_numeric_output()"),
    ("Law 6", "Med Spa Gate", "IF system_state != OBSERVABLE THEN block_med_spa_lab()"),
]

law_blocks = []
for num, name, code in laws:
    law_blocks.append({
        "object": "block", "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [
                {"type": "text", "text": {"content": f"{num} — {name}: "}, "annotations": {"bold": True}},
                {"type": "text", "text": {"content": code}, "annotations": {"code": True}}
            ]
        }
    })

# ── Block 4: Pipeline Map ───────────────────────────────────────────────
block4_header = {
    "object": "block", "type": "heading_2",
    "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Pipeline Map (WorkClaw → MiroFish)"}}]}
}

pipeline_diagram = {
    "object": "block", "type": "code",
    "code": {
        "rich_text": [{"type": "text", "text": {
            "content": (
                "WorkClaw Crawler → Firecrawl Parse → Airtable (lead_repo)\n"
                "  ↓\n"
                "Ghost Engine: enriches + qualifies + routes\n"
                "  ↓\n"
                "Signal Registry (Redis) ← Truth Gate ← MiroFish UFIA\n"
                "  ↓\n"
                "Regime Layer: ACTIVE / ACCUMULATING / OBSERVABLE / LOCKED\n"
                "  ↓\n"
                "Prediction Output → Dashboard → Operator Command Panel"
            )
        }}],
        "language": "plain text"
    }
}

# ── Block 5: Output Contracts ───────────────────────────────────────────
block5_header = {
    "object": "block", "type": "heading_2",
    "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Output Contracts"}}]}
}

contracts = [
    ("WorkClaw", "Crawl → parse → Airtable", '{"leads": [], "status": "success"}'),
    ("MiroFish", "UFIA → signal → regime", '{"signal": "SIG-XXX", "confidence": 0.XX}'),
    ("Redis",    "Signal cache + TTL",        '{"key": "sig:SIG-XXX", "ttl": 3600}'),
    ("FastAPI",  "Prediction endpoint",       '{"prediction": null, "reason": "uncertainty_gate"}'),
    ("Dashboard","Operator display",          '{"system_state": "insufficient_data"}'),
]

contract_blocks = []
for system, contract, example in contracts:
    contract_blocks.append({
        "object": "block", "type": "toggle",
        "toggle": {
            "rich_text": [{"type": "text", "text": {"content": f"{system} — {contract}"}, "annotations": {"bold": True}}],
            "children": [{
                "object": "block", "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": example}}],
                    "language": "json"
                }
            }]
        }
    })

# ── Append all blocks ───────────────────────────────────────────────────
all_blocks = [
    {"object": "block", "type": "divider", "divider": {}},
    block1,
    block2_header, signal_table,
    block3_header, *law_blocks,
    block4_header, pipeline_diagram,
    block5_header, *contract_blocks,
]

result = append_blocks(all_blocks)
print(f"Appended {len(all_blocks)} blocks. Children count: {len(result.get('results', []))}")
