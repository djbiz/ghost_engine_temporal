import { NativeConnection, Worker, Runtime, DefaultLogger } from "@temporalio/worker";
import { fileURLToPath } from "url";
import path from "path";
import * as activities from "./activities";

async function run() {
  const logger = new DefaultLogger("DEBUG");
  Runtime.install({ logger });

  const worker = await Worker.create({
    workflowsPath: path.resolve(path.dirname(fileURLToPath(import.meta.url)), "workflows.ts"),
    activities,
    taskQueue: "ghost-engine-campaigns",
    namespace: process.env.TEMPORAL_NAMESPACE || "quickstart-derekjami-878d5147.kydxq",
    identity: `ghost-engine-worker-${process.pid}`,
  });

  console.log("[Worker] Ghost Engine Temporal Worker starting...");
  console.log(`[Worker] Namespace: ${process.env.TEMPORAL_NAMESPACE || "default"}`);
  console.log(`[Worker] Task Queue: ghost-engine-campaigns`);
  console.log("[Worker] Registered workflows:");
  console.log("  - pipelineRollup");
  console.log("  - ghostEngineCampaign");
  console.log("  - linkedInOutreach");
  console.log("[Worker] Awaiting tasks...");

  await worker.run();
}

run().catch((err) => {
  console.error("[Worker] Fatal error:", err);
  process.exit(1);
});
