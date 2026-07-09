import { Workflow, WorkflowInteractionType, continueAsNew, proxyActivities } from "@temporalio/workflow";
import { RetryPolicy } from "@temporalio/workflow";
import type * as activities from "./activities";

const {
  fetchPipelineData,
  sendSlackMessage,
  fetchLeadsFromApollo,
  generateContent,
  sendLinkedInDM,
} = proxyActivities<typeof activities>({
  startToCloseTimeout: "60s",
});

// =====================
// pipelineRollup
// Daily Slack #legacy-forge-campaign alert
// =====================
export async function PipelineRollup(date: string): Promise<void> {
  const workflowId = `pipeline-rollup-${date}`;
  console.log(`[pipelineRollup] Starting workflow ${workflowId}`);

  let pipelineData;
  try {
    pipelineData = await fetchPipelineData(date);
  } catch (err) {
    console.error("[pipelineRollup] Failed to fetch pipeline data:", err);
    throw err;
  }

  const highPriorityList = pipelineData.highPriority
    .map((item) => `• ${item}`)
    .join("\n");

  const message = `
*📊 Pipeline Rollup — ${date}*

*Leads:* ${pipelineData.leads}
*Duplicates:* ${pipelineData.duplicates}

*🔴 High Priority:*
${highPriorityList}

_Last updated: ${pipelineData.lastUpdated}_
`;

  try {
    await sendSlackMessage("legacy-forge-campaign", message);
  } catch (err) {
    console.error("[pipelineRollup] Failed to send Slack message:", err);
    throw err;
  }

  console.log(`[pipelineRollup] Completed successfully`);
}

// =====================
// ghostEngineCampaign
// Master orchestrator: leads → content → outreach → Slack report
// =====================
export async function GhostEngineCampaign(
  options: { leadCount?: number; batchId?: string } = {}
): Promise<{ processed: number; succeeded: number; failed: number }> {
  const { leadCount = 50, batchId = options.batchId || "unknown" } = options;
  const workflowId = `ghost-engine-campaign-${batchId}`;
  console.log(`[ghostEngineCampaign] Starting workflow ${workflowId}`);

  let processed = 0;
  let succeeded = 0;
  let failed = 0;

  try {
    console.log(`[ghostEngineCampaign] Fetching ${leadCount} leads from Apollo`);

    const response = await fetchLeadsFromApollo(leadCount, {
      seniority: ["Founder", "VP", "Director"],
    });
    const { leads } = response;
    console.log(`[ghostEngineCampaign] Fetched ${leads.length} leads`);

    for (const lead of leads) {
      processed++;
      const idempotencyKey = `${workflowId}-${lead.id}`;

      try {
        const content = await generateContent(
          lead,
          Math.random() > 0.5 ? "linkedin_dm" : "cold_outreach"
        );

        const result = await sendLinkedInDM(lead, content, idempotencyKey);

        if (result.success) {
          succeeded++;
          console.log(`[ghostEngineCampaign] ✓ Sent DM to ${lead.name}`);
        } else {
          failed++;
          console.warn(`[ghostEngineCampaign] ✗ Failed to send to ${lead.name}: ${result.error}`);
        }
      } catch (err) {
        failed++;
        console.error(`[ghostEngineCampaign] Error processing lead ${lead.id}:`, err);
      }
    }

    const report = `
*🚀 Ghost Engine Campaign Complete*

*Batch:* ${batchId}
*Processed:* ${processed}
*✅ Succeeded:* ${succeeded}
*❌ Failed:* ${failed}
*Success Rate:* ${processed > 0 ? ((succeeded / processed) * 100).toFixed(1) : 0}%

_Report generated at ${new Date().toISOString()}_
`;

    try {
      await sendSlackMessage("legacy-forge-campaign", report);
    } catch (err) {
      console.error("[ghostEngineCampaign] Failed to send report to Slack:", err);
    }

    console.log(`[ghostEngineCampaign] Campaign complete: ${succeeded}/${processed} succeeded`);
    return { processed, succeeded, failed };
  } catch (err) {
    console.error("[ghostEngineCampaign] Workflow failed:", err);
    throw err;
  }
}

// =====================
// linkedInOutreach
// Fires on Apr 11 - sandbox lift trigger
// =====================
export async function LinkedInOutreach(
  options: { batch?: number; leadsPerBatch?: number } = {}
): Promise<{
  batch: number;
  processed: number;
  results: Array<{ leadId: string; success: boolean }>;
}> {
  const { batch = 1, leadsPerBatch = 25 } = options;
  const workflowId = `linkedin-outreach-apr11-${batch}`;
  console.log(`[linkedInOutreach] Starting workflow ${workflowId}`);

  const results: Array<{ leadId: string; success: boolean }> = [];

  try {
    const response = await fetchLeadsFromApollo(leadsPerBatch, {
      seniority: ["Founder", "VP"],
    });
    const { leads } = response;
    console.log(`[linkedInOutreach] Fetched ${leads.length} leads for batch ${batch}`);

    for (const lead of leads) {
      const idempotencyKey = `${workflowId}-${lead.id}`;

      try {
        const content = await generateContent(lead, "linkedin_dm");

        const result = await sendLinkedInDM(lead, content, idempotencyKey);
        results.push({ leadId: lead.id, success: result.success });

        if (result.success) {
          console.log(`[linkedInOutreach] ✓ ${lead.name}`);
        } else {
          console.warn(`[linkedInOutreach] ✗ ${lead.name}: ${result.error}`);
        }
      } catch (err) {
        results.push({ leadId: lead.id, success: false });
        console.error(`[linkedInOutreach] Error with ${lead.id}:`, err);
      }
    }

    const succeeded = results.filter((r) => r.success).length;
    const report = `
*🔗 LinkedIn Outreach — Apr 11 Batch ${batch}*

*Leads Processed:* ${results.length}
*✅ Succeeded:* ${succeeded}
*❌ Failed:* ${results.length - succeeded}

_Powered by Ghost Engine Temporal_
`;

    try {
      await sendSlackMessage("legacy-forge-campaign", report);
    } catch (err) {
      console.warn("[linkedInOutreach] Slack report failed:", err);
    }

    console.log(`[linkedInOutreach] Batch ${batch} complete: ${succeeded}/${results.length}`);
    return { batch, processed: results.length, results };
  } catch (err) {
    console.error("[linkedInOutreach] Workflow failed:", err);
    throw err;
  }
}

// CLI entry point for testing
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  console.log("[GhostEngine Workflows] CLI starting...");
  console.log(`Command: ${command}`);

  switch (command) {
    case "pipelineRollup":
      const date = args[1] || new Date().toISOString().split("T")[0];
      console.log(`Executing PipelineRollup for ${date}`);
      await PipelineRollup(date);
      break;

    case "ghostEngineCampaign":
      const leads = parseInt(args[1] || "50", 10);
      console.log(`Executing GhostEngineCampaign with ${leads} leads`);
      await GhostEngineCampaign({ leadCount: leads });
      break;

    case "linkedInOutreach":
      const batchNum = parseInt(args[1] || "1", 10);
      console.log(`Executing LinkedInOutreach batch ${batchNum}`);
      await LinkedInOutreach({ batch: batchNum });
      break;

    default:
      console.log("Usage:");
      console.log("  npx tsx workflows.ts pipelineRollup [date]");
      console.log("  npx tsx workflows.ts ghostEngineCampaign [leadCount]");
      console.log("  npx tsx workflows.ts linkedInOutreach [batchNum]");
  }
}

if (require.main === module) {
  main().catch(console.error);
}

export { main };
