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
    name: "Impact-Realty-Agent",
    // IMPORTANT: Replace this with your actual Langflow flow ID for the recruiting agent
    flow_id: '89d4ca09-b973-4358-8934-9829486d2e03',
    description: "Agent for managing recruiting leads and outreach.",
    initialMessage: "Hello! I'm the Impact-Realty AI Recruiting Agent, your recruiting assistant. How can I help you today?",
    features: ["Conversational Document Q&A (RAG)", "Zoho CRM Sync", "SMS Outreach","Calendar Scheduling"],
  },
  // NOTE: Configurations for other agents like "Karen" would be added here later.
};