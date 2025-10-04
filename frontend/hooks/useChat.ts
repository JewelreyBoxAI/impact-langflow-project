'use client'

import { useState, useCallback } from 'react'
import { type Message } from '@/components/chat/MessageBubble'
import { useSession } from '@/context/SessionContext'
import { useAgent, type AgentType } from '@/context/AgentContext'
import { apiClient } from '@/lib/api'

// Define a proper interface for the Agent object
interface Agent {
  id: string;
  name: string;
  flow_id: string;
}

// This configuration maps agent string identifiers to their full object details.
// Ideally, this would be managed in a central configuration file or the AgentContext.
const agentConfig: { [key: string]: Agent } = {
  recruiting: {
    id: 'recruiting',
    name: 'Recruiting Agent',
    // IMPORTANT: Replace this with your actual Langflow flow ID for the recruiting agent
    flow_id: 'YOUR_RECRUITING_FLOW_ID_HERE',
  },
};

interface UseChatOptions {
  sessionId?: string
  onError?: (error: Error) => void
}

export function useChat(options: UseChatOptions = {}) {
  const { sessionId: providedSessionId, onError } = options
  const { currentSession, addMessage, createSession } = useSession()
  const { currentAgent } = useAgent() // This hook returns a string like "recruiting"

  // Look up the full agent object from the configuration using the string identifier
  const agent = agentConfig[currentAgent as string];

  const [isLoading, setIsLoading] = useState(false)

  const sessionId = providedSessionId || currentSession?.id

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || !agent?.flow_id) {
      console.error("Cannot send message: content is empty or no agent/flow_id is selected.");
      return;
    }

    let activeSessionId = sessionId

    // Create a new session if none exists
    if (!activeSessionId) {
      activeSessionId = createSession(agent.id, `Chat with ${agent.name}`)
    }

    const userMessage: Omit<Message, 'id'> = {
      content: content.trim(),
      sender: 'user',
      timestamp: new Date().toISOString(),
      senderName: 'You',
    }

    // Add user message immediately
    addMessage(activeSessionId, userMessage)
    setIsLoading(true)

    try {
      // Pass a single object to apiClient.sendMessage
      // Include the required flow_id from the current agent
      const response = await apiClient.sendMessage({
        message: content.trim(),
        flow_id: agent.flow_id,
        sessionId: activeSessionId,
      });

      // Update response handling to parse Langflow's output
      // Langflow's final message is often nested. This code safely finds it.
      const agentResponseContent =
        response?.result?.outputs?.[0]?.outputs?.[0]?.results?.message ||
        'I received your message but had trouble responding. Please try again.';

      // Add agent response
      const agentMessage: Omit<Message, 'id'> = {
        content: agentResponseContent,
        sender: 'agent',
        timestamp: new Date().toISOString(),
        senderName: agent.name || 'Assistant',
      }

      addMessage(activeSessionId, agentMessage)

    } catch (error) {
      console.error('Failed to send message:', error)

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