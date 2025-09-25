/**
 * React Hook for Recruiting Workflow
 * Manages recruiting flow state and API interactions
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { RecruitingApi } from '@/lib/api/recruiting';
import { ApiClient } from '@/lib/api/client';
import type {
  RecruitingFlowRequest,
  RecruitingFlowResponse,
  ProspectUploadResponse,
  FlowExecutionStatus,
  OutreachRequest,
  OutreachResponse,
  RecruitingAnalytics,
  UseRecruitingFlowReturn,
  UseChatReturn,
  ChatMessage,
  WebSocketMessage
} from '@/lib/types/recruiting';

// Main recruiting flow hook
export const useRecruitingFlow = (): UseRecruitingFlowReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiClient = new ApiClient();
  const recruitingApi = new RecruitingApi(apiClient);

  const executeFlow = useCallback(async (request: RecruitingFlowRequest): Promise<RecruitingFlowResponse> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await recruitingApi.executeFlow(request);
      return response;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to execute flow';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [recruitingApi]);

  const uploadProspects = useCallback(async (file: File): Promise<ProspectUploadResponse> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await recruitingApi.uploadProspects(file);
      return response;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to upload prospects';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [recruitingApi]);

  const getFlowStatus = useCallback(async (executionId: string): Promise<FlowExecutionStatus> => {
    try {
      const response = await recruitingApi.getFlowStatus(executionId);
      return response;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to get flow status';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [recruitingApi]);

  const sendOutreach = useCallback(async (request: OutreachRequest): Promise<OutreachResponse> => {
    try {
      setIsLoading(true);
      setError(null);

      let response: OutreachResponse;

      switch (request.channel) {
        case 'sms':
          response = await recruitingApi.sendSMS(request);
          break;
        case 'email':
          response = await recruitingApi.sendEmail(request);
          break;
        case 'calendar':
          response = await recruitingApi.scheduleCalendar(request);
          break;
        default:
          throw new Error('Invalid outreach channel');
      }

      return response;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to send outreach';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [recruitingApi]);

  return {
    executeFlow,
    uploadProspects,
    getFlowStatus,
    sendOutreach,
    isLoading,
    error
  };
};

// Chat WebSocket hook
export const useRecruitingChat = (sessionId: string): UseChatReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const apiClient = new ApiClient();
  const recruitingApi = new RecruitingApi(apiClient);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      setConnectionStatus('connecting');
      setError(null);

      wsRef.current = recruitingApi.createWebSocketConnection(sessionId);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        reconnectAttempts.current = 0;
      };

      wsRef.current.onmessage = (event) => {
        try {
          const wsMessage: WebSocketMessage = JSON.parse(event.data);

          if (wsMessage.type === 'agent_response') {
            const newMessage: ChatMessage = {
              session_id: sessionId,
              content: wsMessage.content,
              sender: 'Agent',
              timestamp: wsMessage.timestamp
            };

            setMessages(prev => [...prev, newMessage]);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setConnectionStatus('disconnected');

        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const timeout = Math.pow(2, reconnectAttempts.current) * 1000; // Exponential backoff
          reconnectAttempts.current++;

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, timeout);
        }
      };

      wsRef.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setConnectionStatus('error');
        setError('WebSocket connection error');
      };

    } catch (err: any) {
      console.error('Failed to create WebSocket connection:', err);
      setConnectionStatus('error');
      setError(err.message);
    }
  }, [sessionId, recruitingApi]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User initiated disconnect');
      wsRef.current = null;
    }

    setConnectionStatus('disconnected');
  }, []);

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // Add user message to local state immediately
      const userMessage: ChatMessage = {
        session_id: sessionId,
        content,
        sender: 'User',
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, userMessage]);

      // Send to WebSocket
      wsRef.current.send(JSON.stringify({
        type: 'user_message',
        content,
        session_id: sessionId,
        timestamp: userMessage.timestamp
      }));
    } else {
      console.warn('WebSocket not connected, cannot send message');
      setError('Not connected to chat server');
    }
  }, [sessionId]);

  // Connect on mount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    messages,
    sendMessage,
    isConnected: connectionStatus === 'connected',
    connectionStatus,
    error
  };
};

// Analytics hook
export const useRecruitingAnalytics = (dateFrom?: string, dateTo?: string) => {
  const [analytics, setAnalytics] = useState<RecruitingAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiClient = new ApiClient();
  const recruitingApi = new RecruitingApi(apiClient);

  const fetchAnalytics = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await recruitingApi.getAnalytics(dateFrom, dateTo);
      setAnalytics(data);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch analytics';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [dateFrom, dateTo, recruitingApi]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return {
    analytics,
    isLoading,
    error,
    refetch: fetchAnalytics
  };
};

// Flow status polling hook
export const useFlowStatusPolling = (executionId: string | null, pollInterval: number = 5000) => {
  const [status, setStatus] = useState<FlowExecutionStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiClient = new ApiClient();
  const recruitingApi = new RecruitingApi(apiClient);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const startPolling = useCallback(() => {
    if (!executionId || isPolling) return;

    setIsPolling(true);

    const poll = async () => {
      try {
        const statusResponse = await recruitingApi.getFlowStatus(executionId);
        setStatus(statusResponse);

        // Stop polling if flow is completed or failed
        if (statusResponse.status === 'completed' || statusResponse.status === 'failed') {
          setIsPolling(false);
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }
      } catch (err: any) {
        console.error('Error polling flow status:', err);
        setError(err.message);
      }
    };

    // Initial poll
    poll();

    // Set up interval
    intervalRef.current = setInterval(poll, pollInterval);
  }, [executionId, isPolling, pollInterval, recruitingApi]);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (executionId) {
      startPolling();
    }

    return () => {
      stopPolling();
    };
  }, [executionId, startPolling, stopPolling]);

  return {
    status,
    isPolling,
    error,
    startPolling,
    stopPolling
  };
};

// MCP server status hook
export const useMCPStatus = () => {
  const [serverStatus, setServerStatus] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiClient = new ApiClient();
  const recruitingApi = new RecruitingApi(apiClient);

  const fetchStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const status = await recruitingApi.getServerStatus();
      setServerStatus(status);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch server status';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [recruitingApi]);

  const restartServer = useCallback(async (serverName: string) => {
    try {
      setIsLoading(true);
      await recruitingApi.restartMCPServer(serverName);
      // Refetch status after restart
      await fetchStatus();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to restart server';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [recruitingApi, fetchStatus]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return {
    serverStatus,
    isLoading,
    error,
    refetch: fetchStatus,
    restartServer
  };
};