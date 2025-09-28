/**
 * MCP Dashboard Page
 * Comprehensive monitoring and management of MCP server integration
 */

'use client'

import * as React from 'react'
import { Button } from '@/components/shared/Button'
import { MCPConnectionStatus } from '@/components/mcp/MCPConnectionStatus'
import { MCPHealthDashboard } from '@/components/mcp/MCPHealthDashboard'
import { ZohoOAuthStatus } from '@/components/mcp/ZohoOAuthStatus'
import { ZohoCRMDataTable } from '@/components/mcp/ZohoCRMDataTable'
import { useMCPZoho, useMCPHealthMonitor, useZohoCRMData } from '@/hooks/useMCPZoho'
import { cn } from '@/lib/utils'
import {
  ArrowLeft,
  Database,
  RefreshCw,
  Settings,
  Users,
  Building,
  UserCheck,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

export default function MCPDashboard() {
  const router = useRouter()
  const [activeTab, setActiveTab] = React.useState<'overview' | 'leads' | 'contacts' | 'accounts' | 'settings'>('overview')

  // MCP integration hooks
  const {
    server,
    isConnected,
    isLoading: mcpLoading,
    error: mcpError,
    oauthStatus,
    healthCheck,
    connect,
    disconnect,
    refreshConnection,
    refreshToken,
    testConnection,
    getUsers
  } = useMCPZoho()

  const { healthStatus, startMonitoring, stopMonitoring, checkHealth } = useMCPHealthMonitor()

  // Zoho CRM data hooks
  const leadsData = useZohoCRMData('Leads')
  const contactsData = useZohoCRMData('Contacts')
  const accountsData = useZohoCRMData('Accounts')

  // Stats
  const stats = React.useMemo(() => [
    {
      label: 'Leads',
      value: leadsData.data.length,
      total: leadsData.totalCount,
      loading: leadsData.isLoading,
      error: leadsData.error,
      icon: Users,
      color: 'text-blue-600'
    },
    {
      label: 'Contacts',
      value: contactsData.data.length,
      total: contactsData.totalCount,
      loading: contactsData.isLoading,
      error: contactsData.error,
      icon: UserCheck,
      color: 'text-green-600'
    },
    {
      label: 'Accounts',
      value: accountsData.data.length,
      total: accountsData.totalCount,
      loading: accountsData.isLoading,
      error: accountsData.error,
      icon: Building,
      color: 'text-purple-600'
    }
  ], [leadsData, contactsData, accountsData])

  // Initialize monitoring on mount
  React.useEffect(() => {
    startMonitoring(30000) // Check every 30 seconds
    return () => stopMonitoring()
  }, [startMonitoring, stopMonitoring])

  // Load data when connected
  React.useEffect(() => {
    if (isConnected && oauthStatus?.isAuthenticated) {
      leadsData.search({})
      contactsData.search({})
      accountsData.search({})
    }
  }, [isConnected, oauthStatus?.isAuthenticated])

  const handleRefreshAll = async () => {
    try {
      await Promise.all([
        refreshConnection(),
        checkHealth(),
        leadsData.refresh(),
        contactsData.refresh(),
        accountsData.refresh()
      ])
      toast.success('Dashboard refreshed successfully')
    } catch (error) {
      toast.error('Failed to refresh dashboard')
    }
  }

  const handleTestConnection = async () => {
    try {
      const result = await testConnection()
      if (result.success) {
        toast.success('Zoho connection test passed')
      } else {
        toast.error('Zoho connection test failed')
      }
    } catch (error) {
      toast.error('Connection test failed')
    }
  }

  const getConnectionStatusIcon = () => {
    if (!server) return <AlertTriangle className="h-5 w-5 text-muted-foreground" />

    if (isConnected && oauthStatus?.isAuthenticated && oauthStatus?.tokenValid) {
      return <CheckCircle className="h-5 w-5 text-green-500" />
    }

    return <AlertTriangle className="h-5 w-5 text-red-500" />
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="icon"
                onClick={() => router.back()}
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div className="flex items-center gap-3">
                {getConnectionStatusIcon()}
                <div>
                  <h1 className="text-2xl font-bold">MCP Dashboard</h1>
                  <p className="text-sm text-muted-foreground">
                    Monitor and manage Zoho MCP server integration
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={handleTestConnection}
                disabled={!isConnected || mcpLoading}
              >
                <Database className="h-4 w-4 mr-2" />
                Test Connection
              </Button>
              <Button
                variant="outline"
                onClick={handleRefreshAll}
                disabled={mcpLoading}
              >
                <RefreshCw className={cn('h-4 w-4 mr-2', mcpLoading && 'animate-spin')} />
                Refresh All
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-6">
        {/* Status Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Connection Status */}
          <MCPConnectionStatus
            server={server}
            healthCheck={healthStatus || healthCheck}
            oauthStatus={oauthStatus}
            onRefresh={refreshConnection}
            onReconnect={connect}
            showDetails={true}
          />

          {/* OAuth Status */}
          <ZohoOAuthStatus
            oauthStatus={oauthStatus}
            onRefreshToken={refreshToken}
          />

          {/* Health Dashboard */}
          <MCPHealthDashboard
            healthCheck={healthStatus || healthCheck}
            isLoading={mcpLoading}
            onRefresh={checkHealth}
          />
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {stats.map((stat) => {
            const Icon = stat.icon
            return (
              <div key={stat.label} className="rounded-lg border bg-card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">
                      {stat.label}
                    </p>
                    <div className="mt-2">
                      {stat.loading ? (
                        <div className="flex items-center gap-2">
                          <RefreshCw className="h-4 w-4 animate-spin" />
                          <span className="text-sm text-muted-foreground">Loading...</span>
                        </div>
                      ) : stat.error ? (
                        <div className="text-sm text-red-600">Error</div>
                      ) : (
                        <div className="text-2xl font-bold">
                          {stat.value.toLocaleString()}
                          {stat.total > stat.value && (
                            <span className="text-sm font-normal text-muted-foreground ml-2">
                              of {stat.total.toLocaleString()}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  <Icon className={cn('h-8 w-8', stat.color)} />
                </div>
                {stat.error && (
                  <div className="mt-2 text-xs text-red-600 bg-red-50 dark:bg-red-950 p-2 rounded">
                    {stat.error}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Navigation Tabs */}
        <div className="flex gap-1 mb-6 p-1 bg-muted rounded-lg w-fit">
          {[
            { key: 'overview', label: 'Overview', icon: Database },
            { key: 'leads', label: 'Leads', icon: Users },
            { key: 'contacts', label: 'Contacts', icon: UserCheck },
            { key: 'accounts', label: 'Accounts', icon: Building },
            { key: 'settings', label: 'Settings', icon: Settings }
          ].map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors',
                  activeTab === tab.key
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recent Leads */}
                <div className="rounded-lg border bg-card p-6">
                  <h3 className="font-semibold text-lg mb-4">Recent Leads</h3>
                  {leadsData.data.slice(0, 5).map((lead) => (
                    <div key={lead.id} className="flex items-center justify-between py-2 border-b last:border-b-0">
                      <div>
                        <div className="font-medium">{lead.firstName} {lead.lastName}</div>
                        <div className="text-sm text-muted-foreground">{lead.company}</div>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {new Date(lead.createdTime).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                  {leadsData.data.length === 0 && !leadsData.isLoading && (
                    <div className="text-center py-4 text-muted-foreground">
                      No leads available
                    </div>
                  )}
                </div>

                {/* Recent Contacts */}
                <div className="rounded-lg border bg-card p-6">
                  <h3 className="font-semibold text-lg mb-4">Recent Contacts</h3>
                  {contactsData.data.slice(0, 5).map((contact) => (
                    <div key={contact.id} className="flex items-center justify-between py-2 border-b last:border-b-0">
                      <div>
                        <div className="font-medium">{contact.firstName} {contact.lastName}</div>
                        <div className="text-sm text-muted-foreground">{contact.accountName}</div>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {new Date(contact.createdTime).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                  {contactsData.data.length === 0 && !contactsData.isLoading && (
                    <div className="text-center py-4 text-muted-foreground">
                      No contacts available
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'leads' && (
            <ZohoCRMDataTable
              module="Leads"
              data={leadsData.data}
              isLoading={leadsData.isLoading}
              onRefresh={leadsData.refresh}
              onRowSelect={(record) => console.log('Selected lead:', record)}
            />
          )}

          {activeTab === 'contacts' && (
            <ZohoCRMDataTable
              module="Contacts"
              data={contactsData.data}
              isLoading={contactsData.isLoading}
              onRefresh={contactsData.refresh}
              onRowSelect={(record) => console.log('Selected contact:', record)}
            />
          )}

          {activeTab === 'accounts' && (
            <ZohoCRMDataTable
              module="Accounts"
              data={accountsData.data}
              isLoading={accountsData.isLoading}
              onRefresh={accountsData.refresh}
              onRowSelect={(record) => console.log('Selected account:', record)}
            />
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6">
              <div className="rounded-lg border bg-card p-6">
                <h3 className="font-semibold text-lg mb-4">MCP Configuration</h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Server URL</label>
                    <div className="mt-1 text-sm text-muted-foreground font-mono">
                      {server?.url || 'Not configured'}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Connection Status</label>
                    <div className="mt-1">
                      <span className={cn(
                        'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                        isConnected
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                      )}>
                        {isConnected ? 'Connected' : 'Disconnected'}
                      </span>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Health Monitoring</label>
                    <div className="mt-1 space-y-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => startMonitoring(30000)}
                      >
                        Start Monitoring
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={stopMonitoring}
                      >
                        Stop Monitoring
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-lg border bg-card p-6">
                <h3 className="font-semibold text-lg mb-4">Dangerous Actions</h3>
                <div className="space-y-4">
                  <div>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={disconnect}
                      disabled={!isConnected}
                    >
                      Disconnect MCP Server
                    </Button>
                    <p className="text-xs text-muted-foreground mt-1">
                      This will disconnect from the MCP server and stop all integrations.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}