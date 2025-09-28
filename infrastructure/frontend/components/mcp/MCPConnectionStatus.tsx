/**
 * MCP Connection Status Component
 * Displays real-time connection status and health information
 */

'use client'

import * as React from 'react'
import { Badge } from '@/components/shared/Badge'
import { Button } from '@/components/shared/Button'
import { cn } from '@/lib/utils'
import {
  Wifi,
  WifiOff,
  AlertTriangle,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Info
} from 'lucide-react'
import type {
  MCPServer,
  MCPHealthCheck,
  ZohoOAuthStatus,
  MCPConnectionStatusProps
} from '@/lib/types/mcp'

interface ExtendedMCPConnectionStatusProps extends MCPConnectionStatusProps {
  healthCheck?: MCPHealthCheck | null
  oauthStatus?: ZohoOAuthStatus | null
  onRefresh?: () => void
  onReconnect?: () => void
}

export const MCPConnectionStatus: React.FC<ExtendedMCPConnectionStatusProps> = ({
  server,
  healthCheck,
  oauthStatus,
  onRefresh,
  onReconnect,
  className,
  showDetails = false
}) => {
  const getStatusIcon = () => {
    if (!server) return <WifiOff className="h-4 w-4 text-muted-foreground" />

    switch (server.status) {
      case 'connected':
        return <Wifi className="h-4 w-4 text-green-500" />
      case 'connecting':
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'disconnected':
      default:
        return <WifiOff className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getStatusText = () => {
    if (!server) return 'No Server'

    switch (server.status) {
      case 'connected':
        return 'Connected'
      case 'connecting':
        return 'Connecting...'
      case 'error':
        return 'Error'
      case 'disconnected':
      default:
        return 'Disconnected'
    }
  }

  const getStatusColor = () => {
    if (!server) return 'secondary'

    switch (server.status) {
      case 'connected':
        return 'success'
      case 'connecting':
        return 'info'
      case 'error':
        return 'destructive'
      case 'disconnected':
      default:
        return 'secondary'
    }
  }

  const getHealthIcon = () => {
    if (!healthCheck) return <AlertTriangle className="h-3 w-3 text-muted-foreground" />

    switch (healthCheck.status) {
      case 'healthy':
        return <CheckCircle className="h-3 w-3 text-green-500" />
      case 'degraded':
        return <AlertTriangle className="h-3 w-3 text-yellow-500" />
      case 'unhealthy':
        return <XCircle className="h-3 w-3 text-red-500" />
      default:
        return <AlertTriangle className="h-3 w-3 text-muted-foreground" />
    }
  }

  const getOAuthIcon = () => {
    if (!oauthStatus) return <XCircle className="h-3 w-3 text-muted-foreground" />

    if (oauthStatus.isAuthenticated && oauthStatus.tokenValid) {
      return <CheckCircle className="h-3 w-3 text-green-500" />
    }

    return <XCircle className="h-3 w-3 text-red-500" />
  }

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'Never'
    return new Date(timestamp).toLocaleTimeString()
  }

  return (
    <div className={cn('rounded-lg border bg-card p-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className="font-medium text-sm">MCP Server</span>
          <Badge variant={getStatusColor() as any} className="text-xs">
            {getStatusText()}
          </Badge>
        </div>

        <div className="flex items-center gap-1">
          {onRefresh && (
            <Button
              variant="outline"
              size="icon"
              className="h-6 w-6"
              onClick={onRefresh}
              title="Refresh status"
            >
              <RefreshCw className="h-3 w-3" />
            </Button>
          )}
          {onReconnect && server?.status !== 'connected' && (
            <Button
              variant="outline"
              size="icon"
              className="h-6 w-6"
              onClick={onReconnect}
              title="Reconnect"
            >
              <Wifi className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>

      {/* Server Info */}
      {server && (
        <div className="space-y-2 text-xs text-muted-foreground">
          <div className="flex justify-between">
            <span>URL:</span>
            <span className="font-mono">{server.url}</span>
          </div>
          {server.lastPing && (
            <div className="flex justify-between">
              <span>Last Ping:</span>
              <span>{formatTimestamp(server.lastPing)}</span>
            </div>
          )}
          {server.error && (
            <div className="text-red-500 text-xs bg-red-50 dark:bg-red-950 p-2 rounded">
              {server.error}
            </div>
          )}
        </div>
      )}

      {/* Detailed Status */}
      {showDetails && (
        <div className="mt-4 space-y-3 border-t pt-3">
          {/* Health Status */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {getHealthIcon()}
              <span className="font-medium text-xs">Health Check</span>
              {healthCheck && (
                <Badge variant="outline" className="text-xs">
                  {healthCheck.status}
                </Badge>
              )}
            </div>

            {healthCheck && (
              <div className="ml-5 space-y-1 text-xs text-muted-foreground">
                <div className="flex justify-between">
                  <span>Zoho OAuth:</span>
                  <span className={healthCheck.services.zoho_oauth ? 'text-green-500' : 'text-red-500'}>
                    {healthCheck.services.zoho_oauth ? 'OK' : 'Failed'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Zoho API:</span>
                  <span className={healthCheck.services.zoho_api ? 'text-green-500' : 'text-red-500'}>
                    {healthCheck.services.zoho_api ? 'OK' : 'Failed'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>MCP Server:</span>
                  <span className={healthCheck.services.mcp_server ? 'text-green-500' : 'text-red-500'}>
                    {healthCheck.services.mcp_server ? 'OK' : 'Failed'}
                  </span>
                </div>
                {healthCheck.details?.zoho_users_count !== undefined && (
                  <div className="flex justify-between">
                    <span>Zoho Users:</span>
                    <span>{healthCheck.details.zoho_users_count}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span>Checked:</span>
                  <span>{formatTimestamp(healthCheck.timestamp)}</span>
                </div>
              </div>
            )}
          </div>

          {/* OAuth Status */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {getOAuthIcon()}
              <span className="font-medium text-xs">OAuth Status</span>
              {oauthStatus && (
                <div className="flex gap-1">
                  <Badge variant="outline" className="text-xs">
                    {oauthStatus.isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
                  </Badge>
                  {oauthStatus.mfaBypass && (
                    <Badge variant="success" className="text-xs">
                      MFA Bypass
                    </Badge>
                  )}
                </div>
              )}
            </div>

            {oauthStatus && (
              <div className="ml-5 space-y-1 text-xs text-muted-foreground">
                <div className="flex justify-between">
                  <span>Token Valid:</span>
                  <span className={oauthStatus.tokenValid ? 'text-green-500' : 'text-red-500'}>
                    {oauthStatus.tokenValid ? 'Yes' : 'No'}
                  </span>
                </div>
                {oauthStatus.expiresAt && (
                  <div className="flex justify-between">
                    <span>Expires:</span>
                    <span>{new Date(oauthStatus.expiresAt).toLocaleString()}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span>Scopes:</span>
                  <span className="text-right max-w-32 truncate" title={oauthStatus.scopes.join(', ')}>
                    {oauthStatus.scopes.length} granted
                  </span>
                </div>
                {oauthStatus.error && (
                  <div className="text-red-500 text-xs bg-red-50 dark:bg-red-950 p-2 rounded mt-1">
                    {oauthStatus.error}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Capabilities */}
          {server?.capabilities && server.capabilities.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Info className="h-3 w-3 text-muted-foreground" />
                <span className="font-medium text-xs">Capabilities</span>
              </div>
              <div className="ml-5 flex flex-wrap gap-1">
                {server.capabilities.map((capability) => (
                  <Badge key={capability} variant="outline" className="text-xs">
                    {capability}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Compact connection status indicator for headers/toolbars
 */
export const MCPConnectionIndicator: React.FC<{
  server: MCPServer | null
  onClick?: () => void
  className?: string
}> = ({ server, onClick, className }) => {
  const getStatusColor = () => {
    if (!server) return 'bg-gray-400'

    switch (server.status) {
      case 'connected':
        return 'bg-green-500'
      case 'connecting':
        return 'bg-blue-500'
      case 'error':
        return 'bg-red-500'
      case 'disconnected':
      default:
        return 'bg-gray-400'
    }
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-2 px-2 py-1 rounded-md border bg-background hover:bg-accent transition-colors',
        className
      )}
      title={`MCP Server: ${server?.status || 'Unknown'}`}
    >
      <div className={cn('h-2 w-2 rounded-full', getStatusColor())} />
      <span className="text-xs text-muted-foreground">MCP</span>
    </button>
  )
}