export interface RecruitingFlowRequest {
  prospects: any[];
  flow_config: any;
  user_context: any;
}

export interface RecruitingFlowResponse {
  execution_id: string;
  message: string;
}

export interface ProspectUploadResponse {
  success: boolean;
  count: number;
  message: string;
}

export interface FlowExecutionStatus {
  status: 'completed' | 'failed' | 'running' | 'unknown';
  result?: any;
}

export interface OutreachRequest {
  channel: 'sms' | 'email' | 'calendar';
  // Add other properties like recipient, content, etc. as needed
}

export interface OutreachResponse {
  success: boolean;
  messageId?: string;
  eventId?: string;
}

export interface RecruitingAnalytics {
  total_outreach: number;
  response_rate: number;
  total_prospects: number;
  conversion_rate: number; // Fixes the current error
  interviews_scheduled: number; // A likely future property
  contracts_sent: number; // A likely future property
  hires: number; // A likely future property
}

export interface ChatMessage {
  session_id: string;
  content: string;
  sender: 'User' | 'Agent';
  timestamp: string;
}

export interface WebSocketMessage {
  type: 'agent_response';
  content: string;
  timestamp: string;
}

// Defines the return shape for the main useRecruitingFlow hook
export interface UseRecruitingFlowReturn {
  executeFlow: (request: RecruitingFlowRequest) => Promise<RecruitingFlowResponse>;
  uploadProspects: (file: File) => Promise<ProspectUploadResponse>;
  getFlowStatus: (executionId: string) => Promise<FlowExecutionStatus>;
  sendOutreach: (request: OutreachRequest) => Promise<OutreachResponse>;
  isLoading: boolean;
  error: string | null;
}

// Defines the return shape for the WebSocket chat hook
export interface UseChatReturn {
  messages: ChatMessage[];
  sendMessage: (content: string) => void;
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  error: string | null;
}
