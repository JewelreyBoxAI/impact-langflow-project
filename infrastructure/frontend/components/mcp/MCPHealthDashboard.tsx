/**
 * MCP Health Dashboard Component
 * Comprehensive health monitoring and diagnostics for MCP server
 */

'use client'

import * as React from 'react'
import { Badge } from '@/components/shared/Badge'
import { Button } from '@/components/shared/Button'
import { cn } from '@/lib/utils'
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  Key,
  RefreshCw,
  Server,
  Users,
  XCircle,
  Zap
} from 'lucide-react'
import type {
  MCPHealthCheck,
  MCPHealthDashboardProps
} from '@/lib/types/mcp'

export const MCPHealthDashboard: React.FC<MCPHealthDashboardProps> = ({
  healthCheck,
  isLoading = false,
  onRefresh,
  className
}) => {
  const getOverallStatusIcon = () => {
    if (!healthCheck) return <XCircle className="h-5 w-5 text-muted-foreground" />

    switch (healthCheck.status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'degraded':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case 'unhealthy':
        return <XCircle className="h-5 w-5 text-red-500" />
      default:
        return <XCircle className="h-5 w-5 text-muted-foreground" />
    }
  }

  const getOverallStatusColor = () => {
    if (!healthCheck) return 'secondary'

    switch (healthCheck.status) {
      case 'healthy':
        return 'success'
      case 'degraded':
        return 'warning'
      case 'unhealthy':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  const getServiceIcon = (serviceName: string) => {
    switch (serviceName) {
      case 'zoho_oauth':
        return <Key className="h-4 w-4" />
      case 'zoho_api':
        return <Database className="h-4 w-4" />
      case 'mcp_server':
        return <Server className="h-4 w-4" />
      default:
        return <Activity className="h-4 w-4" />
    }
  }

  const getServiceDisplayName = (serviceName: string) => {
    switch (serviceName) {
      case 'zoho_oauth':
        return 'Zoho OAuth'
      case 'zoho_api':
        return 'Zoho API'
      case 'mcp_server':
        return 'MCP Server'
      default:
        return serviceName
    }
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {getOverallStatusIcon()}
          <div>
            <h3 className="font-semibold text-lg">MCP Health Status</h3>
            <p className="text-sm text-muted-foreground">
              Real-time monitoring of MCP server and services
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant={getOverallStatusColor() as any} className="text-sm">
            {healthCheck?.status || 'Unknown'}
          </Badge>
          {onRefresh && (
            <Button
              variant="outline"
              size="icon"
              onClick={onRefresh}
              disabled={isLoading}
              title="Refresh health status"
            >
              <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
            </Button>
          )}
        </div>
      </div>

      {/* Services Status Grid */}
      {healthCheck && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(healthCheck.services).map(([serviceName, isHealthy]) => (
            <div
              key={serviceName}
              className="rounded-lg border bg-card p-4 space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getServiceIcon(serviceName)}
                  <span className="font-medium text-sm">
                    {getServiceDisplayName(serviceName)}
                  </span>
                </div>
                {isHealthy ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-500" />
                )}
              </div>
              <Badge
                variant={isHealthy ? 'success' : 'destructive'}
                className="text-xs"
              >
                {isHealthy ? 'Operational' : 'Failed'}
              </Badge>
            </div>
          ))}
        </div>
      )}

      {/* Details Section */}
      {healthCheck?.details && (
        <div className="rounded-lg border bg-card p-4 space-y-4">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-muted-foreground" />
            <h4 className="font-medium">System Details</h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Zoho Users Count */}
            {healthCheck.details.zoho_users_count !== undefined && (
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Users className="h-3 w-3" />
                  <span>Zoho Users</span>
                </div>
                <div className="text-lg font-semibold">
                  {healthCheck.details.zoho_users_count.toLocaleString()}
                </div>
              </div>
            )}

            {/* OAuth Token Status */}
            {healthCheck.details.oauth_token_valid !== undefined && (
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Key className="h-3 w-3" />
                  <span>OAuth Token</span>
                </div>
                <div className="flex items-center gap-2">
                  {healthCheck.details.oauth_token_valid ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-500" />
                  )}
                  <span className="text-sm font-medium">
                    {healthCheck.details.oauth_token_valid ? 'Valid' : 'Invalid'}
                  </span>
                </div>
              </div>
            )}

            {/* Last API Call */}
            {healthCheck.details.last_api_call && (
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Zap className="h-3 w-3" />
                  <span>Last API Call</span>
                </div>
                <div className="text-sm font-medium">
                  {formatTimestamp(healthCheck.details.last_api_call)}
                </div>
              </div>
            )}

            {/* Check Timestamp */}
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>Last Check</span>
              </div>
              <div className="text-sm font-medium">
                {formatTimestamp(healthCheck.timestamp)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* No Data State */}
      {!healthCheck && !isLoading && (
        <div className="rounded-lg border border-dashed bg-card p-8 text-center space-y-3">
          <AlertTriangle className="h-8 w-8 text-muted-foreground mx-auto" />
          <div>
            <h4 className="font-medium text-lg">No Health Data Available</h4>
            <p className="text-sm text-muted-foreground">
              Unable to retrieve health status from MCP server
            </p>
          </div>
          {onRefresh && (
            <Button onClick={onRefresh} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Check Status
            </Button>
          )}
        </div>
      )}

      {/* Loading State */}
      {isLoading && !healthCheck && (
        <div className="rounded-lg border bg-card p-8 text-center space-y-3">
          <RefreshCw className="h-8 w-8 text-muted-foreground mx-auto animate-spin" />
          <div>
            <h4 className="font-medium text-lg">Checking Health Status</h4>
            <p className="text-sm text-muted-foreground">
              Retrieving status from MCP server...
            </p>
          </div>
        </div>
      )}

      {/* Status Summary */}
      {healthCheck && (
        <div className="rounded-lg bg-muted/50 p-4">
          <div className="flex items-start gap-3">
            <Activity className="h-4 w-4 text-muted-foreground mt-0.5" />
            <div className="space-y-1">
              <h5 className="font-medium text-sm">Health Summary</h5>
              <p className="text-xs text-muted-foreground">
                {healthCheck.status === 'healthy' &&
                  'All systems operational. MCP server is running smoothly and all integrations are working correctly.'
                }
                {healthCheck.status === 'degraded' &&
                  'Some systems are experiencing issues. Basic functionality is available but some features may be limited.'
                }
                {healthCheck.status === 'unhealthy' &&
                  'Critical systems are down. MCP server may not be functioning properly.'
                }
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}