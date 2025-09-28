/**
 * React Hook for Recruiting Workflow
 * Manages recruiting flow state and API interactions
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { RecruitingApi } from '@/lib/api/recruiting';
import { apiClient } from '@/lib/api';
import { useEmbeddingSearch, useContextMemory, useDataPersistence } from './useEmbeddingSearch';
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
  const [serverStatus, setServerStatus] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recruitingApi = new RecruitingApi(apiClient);

  const fetchStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const status = await recruitingApi.getServerStatus();
      setServerStatus(status as any[]);
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

// Enhanced recruiting hook with full context integration
export const useRecruitingWithContext = (sessionId: string) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Core recruiting functionality
  const recruitingFlow = useRecruitingFlow();
  const analytics = useRecruitingAnalytics();
  const mcpStatus = useMCPStatus();

  // Context and embeddings
  const embeddingSearch = useEmbeddingSearch('recruiting_index');
  const contextMemory = useContextMemory(sessionId);
  const dataPersistence = useDataPersistence();

  // Enhanced message sending with context
  const sendMessageWithContext = useCallback(async (
    message: string,
    includeContext = true,
    contextTypes: string[] = ['conversation', 'prospect', 'document']
  ) => {
    try {
      setIsLoading(true);
      setError(null);

      let contextualMessage = message;

      if (includeContext) {
        // Get relevant context from memory and embeddings
        const [relevantContext, searchResults] = await Promise.all([
          contextMemory.getRelevantContext(message, 1000),
          embeddingSearch.search({
            text: message,
            topK: 5,
            threshold: 0.3,
            filters: { type: contextTypes }
          })
        ]);

        // Combine context sources
        const context = [
          relevantContext,
          ...searchResults.map(result => `${result.metadata.source}: ${result.text}`)
        ].filter(Boolean).join('\n\n');

        if (context) {
          contextualMessage = `Context:\n${context}\n\nUser Message: ${message}`;
        }
      }

      // Send message to recruiting flow
      const response = await recruitingFlow.executeFlow({
        prospects: [], // This would be populated based on context
        flow_config: {
          enable_sms: true,
          enable_email: true,
          enable_calendar: true,
          max_retry_attempts: 3,
          delay_between_contacts: 300
        },
        user_context: {
          message: contextualMessage,
          sessionId,
          includeContext
        }
      });

      // Store the interaction in memory
      await contextMemory.addMemory(
        `User: ${message}\nAgent: ${response.message}`,
        'conversation',
        {
          executionId: response.execution_id,
          timestamp: new Date().toISOString()
        }
      );

      // Store in embeddings for future retrieval
      await embeddingSearch.addVector(
        `${message} -> ${response.message}`,
        {
          type: 'conversation',
          sessionId,
          executionId: response.execution_id,
          timestamp: new Date().toISOString()
        }
      );

      return response;

    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to send message with context';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [recruitingFlow, embeddingSearch, contextMemory, sessionId]);

  // Enhanced prospect management with context
  const addProspectWithContext = useCallback(async (prospectData: any) => {
    try {
      setIsLoading(true);
      setError(null);

      // Save prospect to PostgreSQL
      const { id } = await dataPersistence.saveData('prospects', {
        ...prospectData,
        sessionId,
        createdAt: new Date().toISOString()
      });

      // Create embedding for semantic search
      const prospectText = `${prospectData.name} ${prospectData.company || ''} ${prospectData.position || ''} ${prospectData.email} ${prospectData.phone || ''}`;
      await embeddingSearch.addVector(prospectText, {
        type: 'prospect',
        prospectId: id,
        sessionId,
        ...prospectData
      });

      // Add to memory
      await contextMemory.addMemory(
        `Added prospect: ${prospectData.name} from ${prospectData.company || 'Unknown Company'}`,
        'prospect',
        { prospectId: id, ...prospectData }
      );

      return { id, ...prospectData };

    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to add prospect with context';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [dataPersistence, embeddingSearch, contextMemory, sessionId]);

  // Search across all data sources
  const searchEverything = useCallback(async (query: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const [embeddingResults, memoryResults, dbResults] = await Promise.all([
        embeddingSearch.search({
          text: query,
          topK: 10,
          threshold: 0.2
        }),
        contextMemory.searchMemories(query),
        dataPersistence.queryData('prospects', {
          search: query
        }, 'createdAt DESC', 50)
      ]);

      return {
        embeddings: embeddingResults,
        memories: memoryResults,
        prospects: dbResults
      };

    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to search';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [embeddingSearch, contextMemory, dataPersistence]);

  // Get comprehensive context for a query
  const getComprehensiveContext = useCallback(async (query: string) => {
    try {
      const searchResults = await searchEverything(query);

      const context = {
        summary: '',
        relevantProspects: searchResults.prospects.slice(0, 5),
        pastConversations: searchResults.memories.filter(m => m.type === 'conversation').slice(0, 3),
        relatedDocuments: searchResults.embeddings.filter(r => r.metadata.type === 'document').slice(0, 3),
        actionableInsights: []
      };

      // Generate summary from all sources
      const allContext = [
        ...searchResults.embeddings.map(r => r.text),
        ...searchResults.memories.map(m => m.content),
        ...searchResults.prospects.map(p => `${p.name} - ${p.company} (${p.position})`)
      ].join('\n\n');

      context.summary = allContext.substring(0, 500) + (allContext.length > 500 ? '...' : '');

      return context;

    } catch (err: any) {
      console.error('Failed to get comprehensive context:', err);
      return {
        summary: '',
        relevantProspects: [],
        pastConversations: [],
        relatedDocuments: [],
        actionableInsights: []
      };
    }
  }, [searchEverything]);

  return {
    // Core recruiting functionality
    ...recruitingFlow,
    analytics,
    mcpStatus,

    // Enhanced context functionality
    sendMessageWithContext,
    addProspectWithContext,
    searchEverything,
    getComprehensiveContext,

    // Direct access to context tools
    embeddingSearch,
    contextMemory,
    dataPersistence,

    // Combined loading/error states
    isLoading: isLoading || recruitingFlow.isLoading || analytics.isLoading || mcpStatus.isLoading,
    error: error || recruitingFlow.error || analytics.error || mcpStatus.error
  };
};