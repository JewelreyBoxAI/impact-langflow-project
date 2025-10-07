'use client'

import { useState, useCallback } from 'react'
import { type Message } from '@/components/chat/MessageBubble'
import { useSession } from '@/context/SessionContext'
import { useAgent } from '@/context/AgentContext'
import { apiClient } from '@/lib/api'
import { AGENT_CONFIGS } from '@/lib/constants'

interface UseChatOptions {
  sessionId?: string
  onError?: (error: Error) => void
}

export function useChat(options: UseChatOptions = {}) {
  const { sessionId: providedSessionId, onError } = options
  const { currentSession, addMessage, createSession } = useSession()
  const { currentAgent } = useAgent()

  // Use the centralized agent configuration from constants
  const agent = AGENT_CONFIGS[currentAgent as keyof typeof AGENT_CONFIGS]

  const [isLoading, setIsLoading] = useState(false)

  const sessionId = providedSessionId || currentSession?.id

  const sendMessage = useCallback(async (content: string) => {
    console.log('🚀 sendMessage called with:', content);
    console.log('🔧 Agent:', agent);
    console.log('🔧 Flow ID:', agent?.flow_id);
    
    if (!content.trim() || !agent?.flow_id) {
      console.error("❌ Cannot send message: content is empty or no agent/flow_id is selected.");
      return;
    }

    let activeSessionId = sessionId

    // Create a new session if none exists
    if (!activeSessionId) {
      console.log('📝 Creating new session');
      activeSessionId = createSession(agent.id, `Chat with ${agent.name}`)
    }

    const userMessage: Omit<Message, 'id'> = {
      content: content.trim(),
      sender: 'user',
      timestamp: new Date().toISOString(),
      senderName: 'You',
    }

    console.log('💬 Adding user message:', userMessage);
    // Add user message immediately
    addMessage(activeSessionId, userMessage)
    setIsLoading(true)

    try {
      console.log('📤 Sending to API...');
      // Send message with the correct flow_id from AGENT_CONFIGS
      const response = await apiClient.sendMessage({
        message: content.trim(),
        flow_id: agent.flow_id,
        sessionId: activeSessionId,
      });

      console.log('📥 Full Langflow response:', JSON.stringify(response, null, 2));

      // Update response handling to parse Langflow's output and extract text
      const messageData = response?.result?.outputs?.[0]?.outputs?.[0]?.results?.message;
      const agentResponseContent = 
        messageData?.text || 
        messageData?.data?.text || 
        'I received your message but had trouble responding. Please try again.';

      console.log('🤖 Agent response content:', agentResponseContent);

      // Add agent response
      const agentMessage: Omit<Message, 'id'> = {
        content: agentResponseContent,
        sender: 'agent',
        timestamp: new Date().toISOString(),
        senderName: agent.name || 'Assistant',
      }

      console.log('✅ Adding agent message:', agentMessage);
      addMessage(activeSessionId, agentMessage)

    } catch (error) {
      console.error('❌ Failed to send message:', error)

      // Add error message
      const errorMessage: Omit<Message, 'id'> = {
        content: 'Sorry, I encountered an error while processing your message. Please try again.',
        sender: 'system',
        timestamp: new Date().toISOString(),
      }

      addMessage(activeSessionId, errorMessage)

      if (onError) {
        onError(error instanceof Error ? error : new Error('Failed to send message'))
      }
    } finally {
      console.log('🏁 Setting loading to false');
      setIsLoading(false)
    }
  }, [sessionId, agent, addMessage, createSession, onError])

  const messages = currentSession?.messages || []

  return {
    messages,
    isLoading,
    sendMessage,
    sessionId: currentSession?.id,
  }
}