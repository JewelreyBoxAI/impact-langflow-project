'use client'

import { useState, useCallback } from 'react'
import { type Message } from '@/components/chat/MessageBubble'
import { useSession } from '@/context/SessionContext'
import { useAgent } from '@/context/AgentContext'
import { apiClient } from '@/lib/api'

interface UseChatOptions {
  sessionId?: string
  onError?: (error: Error) => void
}

export function useChat(options: UseChatOptions = {}) {
  const { sessionId: providedSessionId, onError } = options
  const { currentSession, addMessage, createSession } = useSession()
  const { currentAgent } = useAgent()
  const [isLoading, setIsLoading] = useState(false)

  const sessionId = providedSessionId || currentSession?.id

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return

    let activeSessionId = sessionId

    // Create a new session if none exists
    if (!activeSessionId) {
      activeSessionId = createSession(currentAgent, `Chat with ${currentAgent}`)
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
      // Call the API
      const response = await apiClient.sendMessage(currentAgent, {
        message: content.trim(),
        sessionId: activeSessionId,
        conversationId: activeSessionId,
      })

      // Add agent response
      const agentMessage: Omit<Message, 'id'> = {
        content: response.message || 'I received your message but had trouble responding. Please try again.',
        sender: 'agent',
        timestamp: new Date().toISOString(),
        senderName: response.agentName || 'Assistant',
        smsStatus: response.smsStatus || undefined,
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
  }, [sessionId, currentAgent, addMessage, createSession, onError])

  const messages = currentSession?.messages || []

  return {
    messages,
    isLoading,
    sendMessage,
    sessionId: currentSession?.id,
  }
}