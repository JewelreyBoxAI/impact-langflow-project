'use client'

import * as React from "react"
import { type Message } from "@/components/chat/MessageBubble"
import { generateId } from "@/lib/utils"

interface Session {
  id: string
  title: string
  agentType: string
  messages: Message[]
  createdAt: string
  updatedAt: string
  status: 'active' | 'archived' | 'paused'
}

interface SessionContextType {
  sessions: Session[]
  currentSession: Session | null
  isLoading: boolean
  createSession: (agentType: string, title?: string) => string
  selectSession: (sessionId: string) => void
  addMessage: (sessionId: string, message: Omit<Message, 'id'>) => void
  updateSession: (sessionId: string, updates: Partial<Session>) => void
  deleteSession: (sessionId: string) => void
}

const SessionContext = React.createContext<SessionContextType | undefined>(undefined)

interface SessionProviderProps {
  children: React.ReactNode
}

export function SessionProvider({ children }: SessionProviderProps) {
  const [sessions, setSessions] = React.useState<Session[]>([])
  const [currentSession, setCurrentSession] = React.useState<Session | null>(null)
  const [isLoading, setIsLoading] = React.useState(false)

  // Load sessions from localStorage on mount
  React.useEffect(() => {
    const savedSessions = localStorage.getItem('impact-langflow-sessions')
    if (savedSessions) {
      try {
        const parsedSessions = JSON.parse(savedSessions)
        setSessions(parsedSessions)

        // Set the most recent session as current
        if (parsedSessions.length > 0) {
          const mostRecent = parsedSessions.sort((a: Session, b: Session) =>
            new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
          )[0]
          setCurrentSession(mostRecent)
        }
      } catch (error) {
        console.error('Failed to load sessions from localStorage:', error)
      }
    }
  }, [])

  // Save sessions to localStorage whenever sessions change
  React.useEffect(() => {
    localStorage.setItem('impact-langflow-sessions', JSON.stringify(sessions))
  }, [sessions])

  const createSession = React.useCallback((agentType: string, title?: string): string => {
    const sessionId = generateId()
    const now = new Date().toISOString()

    const newSession: Session = {
      id: sessionId,
      title: title || `New ${agentType} conversation`,
      agentType,
      messages: [],
      createdAt: now,
      updatedAt: now,
      status: 'active',
    }

    setSessions(prev => [newSession, ...prev])
    setCurrentSession(newSession)

    return sessionId
  }, [])

  const selectSession = React.useCallback((sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId)
    if (session) {
      setCurrentSession(session)
    }
  }, [sessions])

  const addMessage = React.useCallback((sessionId: string, message: Omit<Message, 'id'>) => {
    const messageWithId: Message = {
      ...message,
      id: generateId(),
    }

    setSessions(prev => prev.map(session => {
      if (session.id === sessionId) {
        const updatedSession = {
          ...session,
          messages: [...session.messages, messageWithId],
          updatedAt: new Date().toISOString(),
        }

        // Update current session if it's the same
        if (currentSession?.id === sessionId) {
          setCurrentSession(updatedSession)
        }

        return updatedSession
      }
      return session
    }))
  }, [currentSession])

  const updateSession = React.useCallback((sessionId: string, updates: Partial<Session>) => {
    setSessions(prev => prev.map(session => {
      if (session.id === sessionId) {
        const updatedSession = {
          ...session,
          ...updates,
          updatedAt: new Date().toISOString(),
        }

        // Update current session if it's the same
        if (currentSession?.id === sessionId) {
          setCurrentSession(updatedSession)
        }

        return updatedSession
      }
      return session
    }))
  }, [currentSession])

  const deleteSession = React.useCallback((sessionId: string) => {
    setSessions(prev => prev.filter(session => session.id !== sessionId))

    // Clear current session if it was deleted
    if (currentSession?.id === sessionId) {
      setCurrentSession(null)
    }
  }, [currentSession])

  const value = React.useMemo(() => ({
    sessions,
    currentSession,
    isLoading,
    createSession,
    selectSession,
    addMessage,
    updateSession,
    deleteSession,
  }), [
    sessions,
    currentSession,
    isLoading,
    createSession,
    selectSession,
    addMessage,
    updateSession,
    deleteSession,
  ])

  return (
    <SessionContext.Provider value={value}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  const context = React.useContext(SessionContext)
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider')
  }
  return context
}