'use client'

import * as React from "react"

export type AgentType = 'recruiting' | 'supervisor' | 'admin' | 'operations'

interface AgentContextType {
  currentAgent: AgentType
  setCurrentAgent: (agent: AgentType) => void
  agentConfig: Record<AgentType, {
    name: string
    displayName: string
    color: string
    isEnabled: boolean
  }>
}

const AgentContext = React.createContext<AgentContextType | undefined>(undefined)

const agentConfig = {
  recruiting: {
    name: 'recruiting',
    displayName: 'Recruiting Agent',
    color: '#1D4ED8',
    isEnabled: true,
  },
  supervisor: {
    name: 'supervisor',
    displayName: 'Supervisor Agent',
    color: '#7c3aed',
    isEnabled: false,
  },
  admin: {
    name: 'admin',
    displayName: 'Admin Agent',
    color: '#dc2626',
    isEnabled: false,
  },
  operations: {
    name: 'operations',
    displayName: 'Operations Agent',
    color: '#059669',
    isEnabled: false,
  },
} as const

interface AgentProviderProps {
  children: React.ReactNode
  initialAgent?: AgentType
}

export function AgentProvider({ children, initialAgent = 'recruiting' }: AgentProviderProps) {
  const [currentAgent, setCurrentAgent] = React.useState<AgentType>(initialAgent)

  const value = React.useMemo(() => ({
    currentAgent,
    setCurrentAgent,
    agentConfig,
  }), [currentAgent])

  return (
    <AgentContext.Provider value={value}>
      {children}
    </AgentContext.Provider>
  )
}

export function useAgent() {
  const context = React.useContext(AgentContext)
  if (context === undefined) {
    throw new Error('useAgent must be used within an AgentProvider')
  }
  return context
}