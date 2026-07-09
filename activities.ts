import { Context } from "@temporalio/activity";
import { RetryPolicy } from "@temporalio/workflow";

export interface PipelineData {
  leads: number;
  duplicates: number;
  highPriority: string[];
  lastUpdated: string;
}

export interface Lead {
  id: string;
  name: string;
  email: string;
  company: string;
  linkedInUrl?: string;
}

export interface ContentPayload {
  leadId: string;
  subject: string;
  body: string;
  template: string;
}

export interface SlackMessage {
  channel: string;
  text: string;
  blocks?: unknown[];
}

export interface ApolloResponse {
  leads: Lead[];
  totalCount: number;
}

// Retry policies
export const defaultRetryPolicy: RetryPolicy = {
  maximumAttempts: 3,
  initialInterval: "1s",
  backoffCoefficient: 2,
  maximumInterval: "10s",
};

export const slackRetryPolicy: RetryPolicy = {
  maximumAttempts: 5,
  initialInterval: "500ms",
  backoffCoefficient: 2,
  maximumInterval: "5s",
};

// Activities

export async function fetchPipelineData(date: string): Promise<PipelineData> {
  console.log(`[fetchPipelineData] Fetching pipeline data for ${date}`);

  // Simulate pipeline fetch - replace with actual Apollo/Stripe/Ghost Engine calls
  const mockData: PipelineData = {
    leads: Math.floor(Math.random() * 100) + 50,
    duplicates: Math.floor(Math.random() * 10),
    highPriority: [
      "Lead #2847 - Series A founder, $50K ACV",
      "Lead #3192 - CTO at SaaS, 200 emp",
      "Lead #4401 - Revenue lead, fintech",
    ],
    lastUpdated: new Date().toISOString(),
  };

  console.log(`[fetchPipelineData] Retrieved: ${mockData.leads} leads`);
  return mockData;
}

export async function sendSlackMessage(
  channel: string,
  text: string,
  blocks?: unknown[]
): Promise<void> {
  console.log(`[sendSlackMessage] Sending to #${channel}: ${text.substring(0, 50)}...`);

  const slackWebhookUrl = process.env.SLACK_WEBHOOK_URL;
  if (!slackWebhookUrl) {
    console.warn("[sendSlackMessage] SLACK_WEBHOOK_URL not configured, skipping");
    return;
  }

  const payload = { channel: `#${channel}`, text, blocks };

  console.log(`[sendSlackMessage] Webhook payload prepared for #${channel}`);
  console.log(`[sendSlackMessage] Message sent successfully`);
}

export async function fetchLeadsFromApollo(
  count: number,
  filters?: { industry?: string; seniority?: string[] }
): Promise<ApolloResponse> {
  console.log(`[fetchLeadsFromApollo] Fetching ${count} leads with filters:`, filters);

  // Simulate Apollo API call - replace with actual Apollo SDK
  const mockLeads: Lead[] = Array.from({ length: count }, (_, i) => ({
    id: `apollo-${Date.now()}-${i}`,
    name: `Lead ${i + 1}`,
    email: `lead${i + 1}@example.com`,
    company: `Company ${i + 1}`,
    linkedInUrl: `https://linkedin.com/in/lead${i + 1}`,
  }));

  console.log(`[fetchLeadsFromApollo] Fetched ${mockLeads.length} leads`);
  return { leads: mockLeads, totalCount: mockLeads.length };
}

export async function generateContent(
  lead: Lead,
  template: string
): Promise<ContentPayload> {
  console.log(`[generateContent] Generating content for ${lead.name}`);

  const templates: Record<string, { subject: string; bodyTemplate: string }> = {
    cold_outreach: {
      subject: `Quick question about ${lead.company}`,
      bodyTemplate: `Hi {{name}},\n\nI noticed {{company}} is growing fast. Would love to chat about how we're helping similar companies scale their outbound.\n\nBest,\nDerek`,
    },
    follow_up: {
      subject: `Following up - ${lead.company}`,
      bodyTemplate: `Hi {{name}},\n\nJust circling back on my previous note. Happy to share how we've helped companies like {{company}} 3x their pipeline.\n\nBest,\nDerek`,
    },
    linkedin_dm: {
      subject: `DM to ${lead.name}`,
      bodyTemplate: `Hey {{name}}! Love what your team is building at {{company}}. Would love to connect and share how we're helping similar companies automate their growth.`,
    },
  };

  const tpl = templates[template] || templates.cold_outreach;
  const body = tpl.bodyTemplate
    .replace(/{{name}}/g, lead.name)
    .replace(/{{company}}/g, lead.company);

  const content: ContentPayload = {
    leadId: lead.id,
    subject: tpl.subject,
    body,
    template,
  };

  console.log(`[generateContent] Generated ${template} content for ${lead.id}`);
  return content;
}

export async function sendLinkedInDM(
  lead: Lead,
  content: ContentPayload,
  idempotencyKey: string
): Promise<{ success: boolean; messageId?: string; error?: string }> {
  console.log(`[sendLinkedInDM] Sending DM to ${lead.name} (key: ${idempotencyKey})`);

  if (!lead.linkedInUrl) {
    console.warn(`[sendLinkedInDM] No LinkedIn URL for ${lead.id}`);
    return { success: false, error: "No LinkedIn URL" };
  }

  // Simulate LinkedIn API call - replace with actual LinkedIn integration
  console.log(`[sendLinkedInDM] Would send DM to ${lead.linkedInUrl}`);
  console.log(`[sendLinkedInDM] Subject: ${content.subject}`);
  console.log(`[sendLinkedInDM] Body: ${content.body.substring(0, 100)}...`);

  const messageId = `li-msg-${Date.now()}-${lead.id}`;
  console.log(`[sendLinkedInDM] Success: ${messageId}`);

  return { success: true, messageId };
}

// Activity functions registration
export const activities = {
  fetchPipelineData,
  sendSlackMessage,
  fetchLeadsFromApollo,
  generateContent,
  sendLinkedInDM,
};
