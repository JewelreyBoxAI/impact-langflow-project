/**
 * MCP Context Provider
 * Global state management for MCP integration
 */

'use client'

import * as React from 'react'
import { useMCPZoho, useMCPHealthMonitor } from '@/hooks/useMCPZoho'
import { useMCPErrorHandler } from '@/components/mcp/MCPErrorBoundary'
import type {
  MCPServer,
  MCPHealthCheck,
  ZohoOAuthStatus,
  MCPTool,
  UseMCPZohoReturn
} from '@/lib/types/mcp'
import toast from 'react-hot-toast'

interface MCPContextValue extends UseMCPZohoReturn {
  // Health monitoring
  healthStatus: MCPHealthCheck | null
  isMonitoring: boolean
  startHealthMonitoring: (intervalMs?: number) => void
  stopHealthMonitoring: () => void

  // Error handling
  retryCount: number
  isRetrying: boolean
  canRetry: boolean
  resetErrors: () => void

  // Connection management
  isInitialized: boolean
  connectionHistory: Array<{
    timestamp: string
    status: 'connected' | 'disconnected' | 'error'
    message?: string
  }>
}

const MCPContext = React.createContext<MCPContextValue | null>(null)

interface MCPProviderProps {
  children: React.ReactNode
  autoConnect?: boolean
  healthMonitoringInterval?: number
  enableNotifications?: boolean
}

export const MCPProvider: React.FC<MCPProviderProps> = ({
  children,
  autoConnect = true,
  healthMonitoringInterval = 30000,
  enableNotifications = true
}) => {
  const [isInitialized, setIsInitialized] = React.useState(false)
  const [connectionHistory, setConnectionHistory] = React.useState<MCPContextValue['connectionHistory']>([])

  // Core MCP functionality
  const mcpHook = useMCPZoho()
  const {
    server,
    isConnected,
    error: mcpError,
    connect,
    disconnect,
    refreshConnection
  } = mcpHook

  // Health monitoring
  const {
    healthStatus,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    checkHealth
  } = useMCPHealthMonitor()

  // Error handling
  const {
    handleError,
    retryCount,
    isRetrying,
    canRetry,
    reset: resetErrors
  } = useMCPErrorHandler(3, 1000)

  // Connection status tracking
  React.useEffect(() => {
    const newEntry = {
      timestamp: new Date().toISOString(),
      status: isConnected ? 'connected' as const : 'disconnected' as const,
      message: mcpError || undefined
    }

    setConnectionHistory(prev => [newEntry, ...prev.slice(0, 9)]) // Keep last 10 entries
  }, [isConnected, mcpError])

  // Auto-connect on mount
  React.useEffect(() => {
    if (autoConnect && !isInitialized) {
      const initializeConnection = async () => {
        try {
          await handleError(new Error('Connection initialization'), async () => {
            await connect()
            return true
          })
        } catch (error) {
          console.error('Failed to initialize MCP connection:', error)
          if (enableNotifications) {
            toast.error('Failed to connect to MCP server')
          }
        } finally {
          setIsInitialized(true)
        }
      }

      initializeConnection()
    }
  }, [autoConnect, isInitialized, connect, handleError, enableNotifications])

  // Start health monitoring when connected
  React.useEffect(() => {
    if (isConnected && !isMonitoring) {
      startMonitoring(healthMonitoringInterval)
    } else if (!isConnected && isMonitoring) {
      stopMonitoring()
    }
  }, [isConnected, isMonitoring, startMonitoring, stopMonitoring, healthMonitoringInterval])

  // Connection status notifications
  React.useEffect(() => {
    if (!enableNotifications) return

    if (isConnected && isInitialized) {
      toast.success('MCP server connected successfully')
    }
  }, [isConnected, isInitialized, enableNotifications])

  // Error notifications
  React.useEffect(() => {
    if (mcpError && enableNotifications && !isRetrying) {
      toast.error(`MCP Error: ${mcpError}`)
    }
  }, [mcpError, enableNotifications, isRetrying])

  // Enhanced connection functions with error handling
  const enhancedConnect = React.useCallback(async () => {
    try {
      await handleError(new Error('Connection failed'), async () => {
        await connect()
        return true
      })
    } catch (error) {
      console.error('Enhanced connect failed:', error)
      throw error
    }
  }, [connect, handleError])

  const enhancedRefreshConnection = React.useCallback(async () => {
    try {
      await handleError(new Error('Refresh connection failed'), async () => {
        await refreshConnection()
        return true
      })
    } catch (error) {
      console.error('Enhanced refresh failed:', error)
      throw error
    }
  }, [refreshConnection, handleError])

  // Health monitoring controls
  const startHealthMonitoring = React.useCallback((intervalMs?: number) => {
    startMonitoring(intervalMs || healthMonitoringInterval)
  }, [startMonitoring, healthMonitoringInterval])

  const stopHealthMonitoring = React.useCallback(() => {
    stopMonitoring()
  }, [stopMonitoring])

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      stopMonitoring()
      disconnect()
    }
  }, [stopMonitoring, disconnect])

  const contextValue: MCPContextValue = {
    // Core MCP functionality
    ...mcpHook,
    connect: enhancedConnect,
    refreshConnection: enhancedRefreshConnection,

    // Health monitoring
    healthStatus,
    isMonitoring,
    startHealthMonitoring,
    stopHealthMonitoring,

    // Error handling
    retryCount,
    isRetrying,
    canRetry,
    resetErrors,

    // Connection management
    isInitialized,
    connectionHistory
  }

  return (
    <MCPContext.Provider value={contextValue}>
      {children}
    </MCPContext.Provider>
  )
}

/**
 * Hook to use MCP context
 */
export const useMCP = (): MCPContextValue => {
  const context = React.useContext(MCPContext)
  if (!context) {
    throw new Error('useMCP must be used within an MCPProvider')
  }
  return context
}

/**
 * Hook to use MCP connection status only
 */
export const useMCPConnection = () => {
  const { server, isConnected, connectionHistory } = useMCP()
  return { server, isConnected, connectionHistory }
}

/**
 * Hook to use MCP health status only
 */
export const useMCPHealth = () => {
  const { healthStatus, isMonitoring, startHealthMonitoring, stopHealthMonitoring } = useMCP()
  return { healthStatus, isMonitoring, startHealthMonitoring, stopHealthMonitoring }
}

/**
 * Hook to use Zoho OAuth status only
 */
export const useMCPOAuth = () => {
  const { oauthStatus, refreshToken } = useMCP()
  return { oauthStatus, refreshToken }
}

/**
 * Connection status indicator hook with automatic reconnection
 */
export const useMCPAutoReconnect = (
  enabled = true,
  maxAttempts = 5,
  reconnectDelay = 5000
) => {
  const { isConnected, connect, retryCount } = useMCP()
  const [autoReconnectAttempts, setAutoReconnectAttempts] = React.useState(0)
  const reconnectTimeoutRef = React.useRef<NodeJS.Timeout | null>(null)

  React.useEffect(() => {
    if (
      enabled &&
      !isConnected &&
      autoReconnectAttempts < maxAttempts &&
      retryCount === 0 // Only auto-reconnect if not already retrying
    ) {
      reconnectTimeoutRef.current = setTimeout(async () => {
        try {
          setAutoReconnectAttempts(prev => prev + 1)
          await connect()
          setAutoReconnectAttempts(0) // Reset on successful connection
        } catch (error) {
          console.error('Auto-reconnect failed:', error)
        }
      }, reconnectDelay)
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [enabled, isConnected, maxAttempts, reconnectDelay, connect, autoReconnectAttempts, retryCount])

  // Reset counter when connection is restored
  React.useEffect(() => {
    if (isConnected) {
      setAutoReconnectAttempts(0)
    }
  }, [isConnected])

  return {
    autoReconnectAttempts,
    maxAttempts,
    isAutoReconnecting: autoReconnectAttempts > 0 && autoReconnectAttempts < maxAttempts
  }
}