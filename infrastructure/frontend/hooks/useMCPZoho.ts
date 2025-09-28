/**
 * React Hooks for MCP Zoho Integration
 * Provides state management and operations for MCP server communication
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { mcpApiClient, mcpUtils } from '@/lib/api/mcp'
import type {
  MCPServer,
  MCPHealthCheck,
  MCPTool,
  ZohoOAuthStatus,
  UseMCPZohoReturn,
  UseMCPHealthMonitorReturn,
  GetZohoUsersRequest,
  GetZohoUsersResponse,
  TestZohoConnectionResponse,
  RefreshTokenResponse,
  SearchZohoCRMRequest,
  SearchZohoCRMResponse,
  CreateZohoCRMRecordRequest,
  CreateZohoCRMRecordResponse,
  UpdateZohoCRMRecordRequest,
  UpdateZohoCRMRecordResponse,
  MCPError
} from '@/lib/types/mcp'

/**
 * Main MCP Zoho integration hook
 */
export const useMCPZoho = (): UseMCPZohoReturn => {
  const [server, setServer] = useState<MCPServer | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [oauthStatus, setOauthStatus] = useState<ZohoOAuthStatus | null>(null)
  const [healthCheck, setHealthCheck] = useState<MCPHealthCheck | null>(null)
  const [availableTools, setAvailableTools] = useState<MCPTool[]>([])

  const connectionTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const healthCheckIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Initialize server state
  const initializeServer = useCallback(() => {
    setServer({
      id: 'zoho-mcp-server',
      name: 'Zoho MCP Server',
      url: 'http://localhost:8001',
      status: 'disconnected',
      capabilities: ['zoho_users', 'zoho_crm', 'oauth_management']
    })
  }, [])

  // Connect to MCP server
  const connect = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      setServer(prev => prev ? { ...prev, status: 'connecting' } : null)

      // Test server reachability
      const isReachable = await mcpUtils.isServerReachable('http://localhost:8001')
      if (!isReachable) {
        throw new Error('MCP server is not reachable')
      }

      // Get server health
      const health = await mcpApiClient.getHealth()
      setHealthCheck(health)

      // Get available tools
      const tools = await mcpApiClient.getTools()
      setAvailableTools(tools)

      // Get OAuth status
      const oauth = await mcpApiClient.getOAuthStatus()
      setOauthStatus(oauth)

      setServer(prev => prev ? {
        ...prev,
        status: 'connected',
        lastPing: new Date().toISOString()
      } : null)

      // Start health monitoring
      startHealthMonitoring()

    } catch (err) {
      const errorMessage = mcpUtils.getErrorMessage(err)
      setError(errorMessage)
      setServer(prev => prev ? {
        ...prev,
        status: 'error',
        error: errorMessage
      } : null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Disconnect from MCP server
  const disconnect = useCallback(() => {
    // Cancel any ongoing requests
    mcpApiClient.cancelRequests()

    // Clear timers
    if (connectionTimeoutRef.current) {
      clearTimeout(connectionTimeoutRef.current)
      connectionTimeoutRef.current = null
    }
    if (healthCheckIntervalRef.current) {
      clearInterval(healthCheckIntervalRef.current)
      healthCheckIntervalRef.current = null
    }

    // Reset state
    setServer(prev => prev ? { ...prev, status: 'disconnected' } : null)
    setError(null)
    setHealthCheck(null)
    setOauthStatus(null)
    setAvailableTools([])
  }, [])

  // Refresh connection
  const refreshConnection = useCallback(async () => {
    disconnect()
    await connect()
  }, [connect, disconnect])

  // Start health monitoring
  const startHealthMonitoring = useCallback(() => {
    if (healthCheckIntervalRef.current) {
      clearInterval(healthCheckIntervalRef.current)
    }

    healthCheckIntervalRef.current = setInterval(async () => {
      try {
        const health = await mcpApiClient.getHealth()
        setHealthCheck(health)

        // Update server status based on health
        if (health.status === 'healthy') {
          setServer(prev => prev ? {
            ...prev,
            status: 'connected',
            lastPing: new Date().toISOString(),
            error: undefined
          } : null)
        } else {
          setServer(prev => prev ? {
            ...prev,
            status: 'error',
            error: 'Server health check failed'
          } : null)
        }
      } catch (err) {
        const errorMessage = mcpUtils.getErrorMessage(err)
        setError(errorMessage)
        setServer(prev => prev ? {
          ...prev,
          status: 'error',
          error: errorMessage
        } : null)
      }
    }, 30000)
  }, [])

  // Refresh OAuth token
  const refreshToken = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await mcpApiClient.refreshToken()

      if (response.success) {
        // Get updated OAuth status
        const newOauthStatus = await mcpApiClient.getOAuthStatus()
        setOauthStatus(newOauthStatus)
      } else {
        throw new Error(response.error || 'Failed to refresh token')
      }
    } catch (err) {
      const errorMessage = mcpUtils.getErrorMessage(err)
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Zoho data operations
  const getUsers = useCallback(async (params: GetZohoUsersRequest = {}): Promise<GetZohoUsersResponse> => {
    try {
      setIsLoading(true)
      setError(null)
      return await mcpApiClient.getZohoUsers(params)
    } catch (err) {
      const errorMessage = mcpUtils.getErrorMessage(err)
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const testConnection = useCallback(async (): Promise<TestZohoConnectionResponse> => {
    try {
      setIsLoading(true)
      setError(null)
      return await mcpApiClient.testZohoConnection()
    } catch (err) {
      const errorMessage = mcpUtils.getErrorMessage(err)
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const searchCRM = useCallback(async (params: SearchZohoCRMRequest): Promise<SearchZohoCRMResponse> => {
    try {
      setIsLoading(true)
      setError(null)
      return await mcpApiClient.searchZohoCRM(params)
    } catch (err) {
      const errorMessage = mcpUtils.getErrorMessage(err)
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const createRecord = useCallback(async (params: CreateZohoCRMRecordRequest): Promise<CreateZohoCRMRecordResponse> => {
    try {
      setIsLoading(true)
      setError(null)
      return await mcpApiClient.createZohoCRMRecord(params)
    } catch (err) {
      const errorMessage = mcpUtils.getErrorMessage(err)
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const updateRecord = useCallback(async (params: UpdateZohoCRMRecordRequest): Promise<UpdateZohoCRMRecordResponse> => {
    try {
      setIsLoading(true)
      setError(null)
      return await mcpApiClient.updateZohoCRMRecord(params)
    } catch (err) {
      const errorMessage = mcpUtils.getErrorMessage(err)
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Initialize on mount
  useEffect(() => {
    initializeServer()
    return () => {
      disconnect()
    }
  }, [initializeServer, disconnect])

  // Compute derived state
  const isConnected = server?.status === 'connected'

  return {
    server,
    isConnected,
    isLoading,
    error,
    oauthStatus,
    healthCheck,
    availableTools,
    connect,
    disconnect,
    refreshConnection,
    refreshToken,
    getUsers,
    testConnection,
    searchCRM,
    createRecord,
    updateRecord
  }
}

/**
 * Health monitoring specific hook
 */
export const useMCPHealthMonitor = (): UseMCPHealthMonitorReturn => {
  const [healthStatus, setHealthStatus] = useState<MCPHealthCheck | null>(null)
  const [isMonitoring, setIsMonitoring] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  const checkHealth = useCallback(async () => {
    try {
      setError(null)
      const health = await mcpApiClient.getHealth()
      setHealthStatus(health)
    } catch (err) {
      const errorMessage = mcpUtils.getErrorMessage(err)
      setError(errorMessage)
    }
  }, [])

  const startMonitoring = useCallback((intervalMs = 30000) => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }

    setIsMonitoring(true)

    // Initial check
    checkHealth()

    // Set up interval
    intervalRef.current = setInterval(checkHealth, intervalMs)
  }, [checkHealth])

  const stopMonitoring = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setIsMonitoring(false)
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopMonitoring()
    }
  }, [stopMonitoring])

  return {
    healthStatus,
    isMonitoring,
    error,
    startMonitoring,
    stopMonitoring,
    checkHealth
  }
}

/**
 * Zoho CRM data management hook
 */
export const useZohoCRMData = (module: 'Leads' | 'Contacts' | 'Accounts') => {
  const [data, setData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)

  const search = useCallback(async (params: Omit<SearchZohoCRMRequest, 'module'>) => {
    try {
      setIsLoading(true)
      setError(null)
      setCurrentPage(1)

      const response = await mcpApiClient.searchZohoCRM({
        ...params,
        module,
        page: 1
      })

      if (response.success && response.data) {
        setData(response.data)
        setTotalCount(response.totalCount || 0)
        setHasMore(response.hasMore || false)
      } else {
        throw new Error(response.error || 'Failed to search records')
      }
    } catch (err) {
      const errorMessage = mcpUtils.getErrorMessage(err)
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }, [module])

  const loadMore = useCallback(async (filters: Omit<SearchZohoCRMRequest, 'module' | 'page'> = {}) => {
    if (!hasMore || isLoading) return

    try {
      setIsLoading(true)
      const nextPage = currentPage + 1

      const response = await mcpApiClient.searchZohoCRM({
        ...filters,
        module,
        page: nextPage
      })

      if (response.success && response.data) {
        setData(prev => [...prev, ...response.data])
        setCurrentPage(nextPage)
        setHasMore(response.hasMore || false)
      }
    } catch (err) {
      const errorMessage = mcpUtils.getErrorMessage(err)
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }, [module, hasMore, isLoading, currentPage])

  const refresh = useCallback(async () => {
    setCurrentPage(1)
    await search({})
  }, [search])

  const create = useCallback(async (recordData: any) => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await mcpApiClient.createZohoCRMRecord({
        module,
        data: recordData
      })

      if (response.success && response.data) {
        setData(prev => [response.data, ...prev])
        setTotalCount(prev => prev + 1)
        return response.data
      } else {
        throw new Error(response.error || 'Failed to create record')
      }
    } catch (err) {
      const errorMessage = mcpUtils.getErrorMessage(err)
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [module])

  const update = useCallback(async (id: string, recordData: any) => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await mcpApiClient.updateZohoCRMRecord({
        module,
        id,
        data: recordData
      })

      if (response.success && response.data) {
        setData(prev => prev.map(item => item.id === id ? response.data : item))
        return response.data
      } else {
        throw new Error(response.error || 'Failed to update record')
      }
    } catch (err) {
      const errorMessage = mcpUtils.getErrorMessage(err)
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [module])

  const remove = useCallback(async (id: string) => {
    try {
      setIsLoading(true)
      setError(null)

      await mcpApiClient.deleteZohoCRMRecord(module, id)
      setData(prev => prev.filter(item => item.id !== id))
      setTotalCount(prev => prev - 1)
    } catch (err) {
      const errorMessage = mcpUtils.getErrorMessage(err)
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [module])

  return {
    data,
    isLoading,
    error,
    totalCount,
    hasMore,
    currentPage,
    search,
    loadMore,
    refresh,
    create,
    update,
    remove
  }
}