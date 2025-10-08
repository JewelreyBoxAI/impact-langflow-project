// Define a proper interface for the Agent object that includes all properties
export interface Agent {
  id: string;
  name: string;
  flow_id: string; // Required for making API calls
  description: string;
  initialMessage: string;
  features: string[];
}

// This configuration maps agent string identifiers to their full object details.
export const AGENT_CONFIGS: { [key: string]: Agent } = {
  recruiting: {
    id: "recruiting",
    name: "Katelyn (Recruiting)",
    // IMPORTANT: Replace this with your actual Langflow flow ID for the recruiting agent
    flow_id: '109ab46f-12fa-4865-8b26-37cf540ad101',
    description: "Agent for managing recruiting leads and outreach.",
    initialMessage: "Hello! I'm Katelyn, your recruiting assistant. How can I help you today?",
    features: ["CSV Import", "Zoho CRM Sync", "SMS Outreach"],
  },
  // NOTE: Configurations for other agents like "Karen" would be added here later.
};