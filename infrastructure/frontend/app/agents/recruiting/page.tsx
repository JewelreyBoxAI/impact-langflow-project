'use client'

import * as React from "react"
import { ChatInterface } from "@/components/chat/ChatInterface"
import { ConversationSidebar } from "@/components/sidebar/ConversationSidebar"
import { ThemeToggle } from "@/components/shared/ThemeToggle"
import { Button } from "@/components/shared/Button"
import { Badge } from "@/components/shared/Badge"
import { useChat } from "@/hooks/useChat"
import { useSession } from "@/hooks/useSession"
import { useAgent } from "@/context/AgentContext"
import { AGENT_CONFIGS } from "@/lib/constants"
import { useMCPZoho, useZohoCRMData } from "@/hooks/useMCPZoho"
import { MCPConnectionIndicator } from "@/components/mcp/MCPConnectionStatus"
import { ZohoOAuthIndicator } from "@/components/mcp/ZohoOAuthStatus"
import { MCPErrorBoundary } from "@/components/mcp/MCPErrorBoundary"
import { cn } from "@/lib/utils"
import {
  Menu,
  X,
  Phone,
  Mail,
  Calendar,
  Users,
  MessageSquare,
  Mic,
  Video,
  Database,
  Zap,
  RefreshCw,
} from "lucide-react"
import toast from "react-hot-toast"

export default function RecruitingPage() {
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false)
  const [isMetadataPanelOpen, setIsMetadataPanelOpen] = React.useState(false)
  const [showMCPPanel, setShowMCPPanel] = React.useState(false)

  const { setCurrentAgent } = useAgent()
  const { sessions, currentSession, createSession, selectSession } = useSession()
  const { messages, isLoading, sendMessage } = useChat({
    onError: (error) => {
      toast.error(error.message || 'Failed to send message')
    }
  })

  // MCP Zoho integration
  const {
    server,
    isConnected,
    isLoading: mcpLoading,
    error: mcpError,
    oauthStatus,
    healthCheck,
    connect: connectMCP,
    disconnect: disconnectMCP,
    refreshConnection,
    refreshToken,
    getUsers,
    testConnection
  } = useMCPZoho()

  // Zoho CRM data hooks
  const leadsData = useZohoCRMData('Leads')
  const contactsData = useZohoCRMData('Contacts')

  // Set current agent to recruiting on mount
  React.useEffect(() => {
    setCurrentAgent('recruiting')
  }, [setCurrentAgent])

  // Create initial session if none exists
  React.useEffect(() => {
    if (sessions.length === 0) {
      createSession('recruiting', 'Welcome to Recruiting Agent')
    }
  }, [sessions.length, createSession])

  // Initialize MCP connection
  React.useEffect(() => {
    connectMCP().catch((error) => {
      console.error('Failed to connect to MCP server:', error)
    })
  }, [connectMCP])

  // MCP connection status effect
  React.useEffect(() => {
    if (mcpError) {
      toast.error(`MCP Error: ${mcpError}`)
    }
  }, [mcpError])

  // Test Zoho connection when MCP connects
  React.useEffect(() => {
    if (isConnected && oauthStatus?.isAuthenticated) {
      testConnection().then(() => {
        // Load initial data
        leadsData.search({})
        contactsData.search({})
      }).catch((error) => {
        console.error('Zoho connection test failed:', error)
      })
    }
  }, [isConnected, oauthStatus?.isAuthenticated, testConnection, leadsData, contactsData])

  const agentConfig = AGENT_CONFIGS.recruiting

  const handleNewConversation = () => {
    const sessionId = createSession('recruiting', `Chat ${new Date().toLocaleTimeString()}`)
    toast.success('New conversation started')
    setIsSidebarOpen(false)
  }

  const handleConversationSelect = (conversationId: string) => {
    selectSession(conversationId)
    setIsSidebarOpen(false)
  }

  const conversationSummaries = sessions
    .filter(session => session.agentType === 'recruiting')
    .map(session => ({
      id: session.id,
      title: session.title,
      lastMessage: session.messages[session.messages.length - 1]?.content || 'No messages yet',
      timestamp: session.updatedAt,
      status: session.status,
      unreadCount: 0, // TODO: implement unread count logic
      participant: {
        name: 'User',
        avatar: undefined,
      },
    }))

  return (
    <MCPErrorBoundary
      onError={(error, errorInfo) => {
        console.error('MCP Error in recruiting page:', error, errorInfo)
        toast.error(`MCP Integration Error: ${error.message}`)
      }}
    >
      <div className="h-screen flex bg-background overflow-hidden">
      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        "fixed inset-y-0 left-0 z-50 w-80 max-w-[calc(100vw-4rem)] bg-background border-r transform transition-transform duration-200 ease-in-out lg:relative lg:translate-x-0 lg:w-80 lg:max-w-none",
        isSidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <ConversationSidebar
          conversations={conversationSummaries}
          activeConversationId={currentSession?.id}
          onConversationSelect={handleConversationSelect}
          onNewConversation={handleNewConversation}
          className="h-full"
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 shrink-0">
          <div className="flex items-center gap-3 min-w-0 flex-1">
            {/* Mobile Menu Button */}
            <Button
              variant="outline"
              size="icon"
              className="lg:hidden shrink-0"
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            >
              {isSidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </Button>

            {/* Agent Info */}
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <div className="h-10 w-10 rounded-full bg-gradient-primary flex items-center justify-center text-white font-medium shrink-0">
                R
              </div>
              <div className="min-w-0 flex-1">
                <h1 className="font-semibold text-foreground truncate">{agentConfig.name}</h1>
                <p className="text-sm text-muted-foreground truncate">{agentConfig.description}</p>
              </div>
            </div>

            {/* Features */}
            <div className="hidden xl:flex items-center gap-2 shrink-0">
              {agentConfig.features.slice(0, 3).map((feature) => (
                <Badge key={feature} variant="secondary" className="text-xs">
                  {feature}
                </Badge>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {/* Quick Actions */}
            <div className="hidden md:flex items-center gap-1">
              <Button variant="outline" size="icon" title="Voice call">
                <Phone className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon" title="Video call">
                <Video className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon" title="Schedule meeting">
                <Calendar className="h-4 w-4" />
              </Button>
            </div>

            {/* MCP Status Indicators */}
            <MCPConnectionIndicator
              server={server}
              onClick={() => setShowMCPPanel(!showMCPPanel)}
            />
            <ZohoOAuthIndicator
              oauthStatus={oauthStatus}
              onClick={() => setShowMCPPanel(!showMCPPanel)}
            />

            {/* Metadata Panel Toggle */}
            <Button
              variant="outline"
              size="icon"
              onClick={() => setIsMetadataPanelOpen(!isMetadataPanelOpen)}
              className="hidden xl:flex"
              title="Toggle agent details"
            >
              <Users className="h-4 w-4" />
            </Button>

            {/* MCP Panel Toggle */}
            <Button
              variant="outline"
              size="icon"
              onClick={() => setShowMCPPanel(!showMCPPanel)}
              className="hidden lg:flex"
              title="Toggle MCP dashboard"
            >
              <Database className="h-4 w-4" />
            </Button>

            <ThemeToggle />
          </div>
        </div>

        {/* Chat Content */}
        <div className="flex-1 flex min-h-0 overflow-hidden">
          {/* Chat Interface */}
          <div className="flex-1 min-w-0 overflow-hidden">
            <ChatInterface
              messages={messages}
              onSendMessage={sendMessage}
              isLoading={isLoading}
            />
          </div>

          {/* Right Panels */}
          {(isMetadataPanelOpen || showMCPPanel) && (
            <div className="w-80 max-w-[calc(100vw-20rem)] border-l bg-background overflow-y-auto hidden xl:block shrink-0">
              <div className="p-4">
                {/* Panel Tabs */}
                <div className="flex gap-1 mb-4 p-1 bg-muted rounded-lg">
                  <button
                    onClick={() => {
                      setIsMetadataPanelOpen(true)
                      setShowMCPPanel(false)
                    }}
                    className={cn(
                      'flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors',
                      isMetadataPanelOpen && !showMCPPanel
                        ? 'bg-background text-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                    )}
                  >
                    Agent
                  </button>
                  <button
                    onClick={() => {
                      setShowMCPPanel(true)
                      setIsMetadataPanelOpen(false)
                    }}
                    className={cn(
                      'flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors',
                      showMCPPanel
                        ? 'bg-background text-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                    )}
                  >
                    <div className="flex items-center justify-center gap-2">
                      <Database className="h-3 w-3" />
                      MCP
                    </div>
                  </button>
                </div>

                {/* Agent Panel */}
                {isMetadataPanelOpen && !showMCPPanel && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="font-semibold text-foreground mb-3">Agent Details</h3>
                      <div className="space-y-3">
                        <div className="flex items-center gap-2 text-sm">
                          <MessageSquare className="h-4 w-4 text-muted-foreground" />
                          <span className="text-muted-foreground">Status:</span>
                          <Badge variant="success">Online</Badge>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <Users className="h-4 w-4 text-muted-foreground" />
                          <span className="text-muted-foreground">Type:</span>
                          <span>Recruiting Assistant</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <Mic className="h-4 w-4 text-muted-foreground" />
                          <span className="text-muted-foreground">Voice:</span>
                          <span>Enabled</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <Database className="h-4 w-4 text-muted-foreground" />
                          <span className="text-muted-foreground">MCP:</span>
                          <Badge variant={isConnected ? "success" : "secondary"}>
                            {isConnected ? "Connected" : "Disconnected"}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <Zap className="h-4 w-4 text-muted-foreground" />
                          <span className="text-muted-foreground">Zoho:</span>
                          <Badge variant={oauthStatus?.isAuthenticated ? "success" : "secondary"}>
                            {oauthStatus?.isAuthenticated ? "Authenticated" : "Not Connected"}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold text-foreground mb-3">Capabilities</h3>
                      <div className="space-y-2">
                        {agentConfig.features.map((feature) => (
                          <div key={feature} className="flex items-center gap-2 text-sm">
                            <div className="h-2 w-2 rounded-full bg-green-500 shrink-0" />
                            <span className="break-words">{feature}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold text-foreground mb-3">Session Info</h3>
                      <div className="space-y-2 text-sm text-muted-foreground">
                        <div>Messages: {messages.length}</div>
                        <div>Started: {currentSession ? new Date(currentSession.createdAt).toLocaleString() : 'N/A'}</div>
                        <div>Last Activity: {currentSession ? new Date(currentSession.updatedAt).toLocaleString() : 'N/A'}</div>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold text-foreground mb-3">Zoho Data</h3>
                      <div className="space-y-2 text-sm text-muted-foreground">
                        <div>Leads: {leadsData.data.length} loaded</div>
                        <div>Contacts: {contactsData.data.length} loaded</div>
                        <div>Status: {isConnected ? 'Synced' : 'Offline'}</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* MCP Panel */}
                {showMCPPanel && (
                  <div className="space-y-4">
                    {/* MCP Connection Status */}
                    <div>
                      <h3 className="font-semibold text-foreground mb-3">MCP Connection</h3>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Server:</span>
                          <Badge variant={isConnected ? "success" : "secondary"}>
                            {isConnected ? "Connected" : "Disconnected"}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">URL:</span>
                          <span className="text-xs font-mono">{server?.url || 'N/A'}</span>
                        </div>
                        {server?.lastPing && (
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Last Ping:</span>
                            <span className="text-xs">{new Date(server.lastPing).toLocaleTimeString()}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* OAuth Status */}
                    <div>
                      <h3 className="font-semibold text-foreground mb-3">Zoho OAuth</h3>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Status:</span>
                          <Badge variant={oauthStatus?.isAuthenticated ? "success" : "secondary"}>
                            {oauthStatus?.isAuthenticated ? "Authenticated" : "Not Connected"}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Token:</span>
                          <Badge variant={oauthStatus?.tokenValid ? "success" : "destructive"}>
                            {oauthStatus?.tokenValid ? "Valid" : "Invalid"}
                          </Badge>
                        </div>
                        {oauthStatus?.mfaBypass && (
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">MFA:</span>
                            <Badge variant="success">Bypassed</Badge>
                          </div>
                        )}
                        {oauthStatus?.expiresAt && (
                          <div className="text-xs text-muted-foreground">
                            Expires: {new Date(oauthStatus.expiresAt).toLocaleString()}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Health Status */}
                    {healthCheck && (
                      <div>
                        <h3 className="font-semibold text-foreground mb-3">Health Status</h3>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Overall:</span>
                            <Badge variant={
                              healthCheck.status === 'healthy' ? 'success' :
                              healthCheck.status === 'degraded' ? 'warning' : 'destructive'
                            }>
                              {healthCheck.status}
                            </Badge>
                          </div>
                          {healthCheck.services && Object.entries(healthCheck.services).map(([service, isHealthy]) => (
                            <div key={service} className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground capitalize">
                                {service.replace('_', ' ')}:
                              </span>
                              <Badge variant={isHealthy ? "success" : "destructive"}>
                                {isHealthy ? "OK" : "Failed"}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Quick Actions */}
                    <div>
                      <h3 className="font-semibold text-foreground mb-3">Quick Actions</h3>
                      <div className="space-y-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => refreshConnection()}
                          disabled={mcpLoading}
                          className="w-full"
                        >
                          <RefreshCw className={cn('h-3 w-3 mr-2', mcpLoading && 'animate-spin')} />
                          Refresh Connection
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => refreshToken()}
                          disabled={!oauthStatus?.isAuthenticated || mcpLoading}
                          className="w-full"
                        >
                          <Zap className="h-3 w-3 mr-2" />
                          Refresh Token
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            leadsData.refresh()
                            contactsData.refresh()
                          }}
                          disabled={!isConnected || leadsData.isLoading || contactsData.isLoading}
                          className="w-full"
                        >
                          <Database className="h-3 w-3 mr-2" />
                          Sync Data
                        </Button>
                      </div>
                    </div>

                    {/* Error Display */}
                    {mcpError && (
                      <div className="rounded-lg bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 p-3">
                        <div className="text-sm text-red-800 dark:text-red-200 font-medium mb-1">
                          MCP Error
                        </div>
                        <div className="text-xs text-red-600 dark:text-red-300">
                          {mcpError}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      </div>
    </MCPErrorBoundary>
  )
}