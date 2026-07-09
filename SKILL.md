---
name: ghost-engine-temporal
description: Temporal workflows for Ghost Engine campaign orchestration — pipeline rollups, lead gen, content generation, and LinkedIn outreach scheduling
compatibility: Created for Zo Computer
metadata:
  author: derekjamieson29.zo.computer
---

# Ghost Engine Temporal Skill

Orchestrate Ghost Engine campaigns using Temporal — daily Slack rollups, lead generation pipelines, content creation, and LinkedIn outreach with built-in idempotency.

## Workflows

| Workflow | Trigger | Purpose |
|---|---|---|
| `pipelineRollup` | Daily (9am) | Aggregate pipeline data → Slack digest |
| `ghostEngineCampaign` | On-demand | Full lead gen → content → follow-up orchestration |
| `linkedInOutreach` | Apr 11, 2026 | Scrape leads → personalize → queue outreach |

## Quick Start

```bash
cd ghost_engine_temporal
bun install
bun run worker.ts
```

## Environment Variables

| Variable | Source |
|---|---|
| `TEMPORAL_API_KEY` | Temporal Cloud API key |
| `TEMPORAL_NAMESPACE` | quickstart-derekjami-878d5147.kydxq |
| `TEMPORAL_ADDRESS` | ap-northeast-1.aws.api.temporal.io:7233 |
| `SLACK_WEBHOOK_URL` | Slack app webhook |
| `APOLLO_API_KEY` | Apollo.io dashboard |

## Workflow Details

### pipelineRollup
- **Schedule**: Daily at 9:00 AM ET via Temporal cron
- **Activities**: `fetchPipelineData` → `sendSlackMessage`
- **Idempotency**: Workflow ID `daily-pipeline-rollup-{date}`

### ghostEngineCampaign
- **Trigger**: On-demand via `client.workflow.start()`
- **Activities**: `fetchLeadsFromApollo` → `generateContent` → `sendSlackMessage`
- **Idempotency**: Workflow ID `ghost-campaign-{timestamp}`

### linkedInOutreach
- **Trigger**: Scheduled Apr 11, 2026 via `startDate`
- **Activities**: `fetchLeadsFromApollo` → `generateContent`
- **Idempotency**: Workflow ID `linkedin-outreach-{date}`

## Workflow IDs

All workflows use deterministic `workflowId` for idempotency:
- `daily-pipeline-rollup-{YYYY-MM-DD}`
- `ghost-campaign-{runId}`
- `linkedin-outreach-{YYYY-MM-DD}`

Temporal ensures only one instance runs per `workflowId` at a time.
