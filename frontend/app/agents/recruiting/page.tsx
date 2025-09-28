'use client'

import * as React from "react"
import Image from "next/image"
import { ChatInterface } from "@/components/chat/ChatInterface"
import { RecruitingSidebar } from "@/components/sidebar/RecruitingSidebar"
import { ZohoProspectCard } from "@/components/recruiting/ZohoProspectCard"
import { ThemeToggle } from "@/components/shared/ThemeToggle"
import { Button } from "@/components/shared/Button"
import { Badge } from "@/components/shared/Badge"
import { useChat } from "@/hooks/useChat"
import { useSession } from "@/hooks/useSession"
import { useAgent } from "@/context/AgentContext"
import { useRecruitingFlow, useRecruitingAnalytics, useMCPStatus } from "@/hooks/useRecruiting"
import { useZohoLeads, useZohoContacts, useZohoActivities } from "@/hooks/useZohoCRM"
import { AGENT_CONFIGS } from "@/lib/constants"
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
  Activity,
  Zap,
  TrendingUp
} from "lucide-react"
import toast from "react-hot-toast"

export default function RecruitingPage() {
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false)
  const [isMetadataPanelOpen, setIsMetadataPanelOpen] = React.useState(false)
  const [selectedProspectId, setSelectedProspectId] = React.useState<string | null>(null)

  const { setCurrentAgent } = useAgent()
  const { sessions, currentSession, createSession, selectSession } = useSession()
  const { messages, isLoading, sendMessage } = useChat({
    onError: (error) => {
      toast.error(error.message || 'Failed to send message')
    }
  })

  // Recruiting-specific hooks
  const { executeFlow, uploadProspects, isLoading: flowLoading, error: flowError } = useRecruitingFlow()
  const { analytics, isLoading: analyticsLoading } = useRecruitingAnalytics()
  const { serverStatus, isLoading: mcpLoading } = useMCPStatus()

  // Zoho CRM hooks
  const {
    leads,
    isLoading: leadsLoading,
    searchLeads,
    refreshLeads
  } = useZohoLeads({
    rating: ['Hot', 'Warm'],
    leadStatus: ['New', 'Contacted', 'Qualified']
  })

  const {
    contacts,
    isLoading: contactsLoading,
    searchContacts,
    refreshContacts
  } = useZohoContacts()

  const {
    activities,
    isLoading: activitiesLoading,
    getActivitiesForRecord
  } = useZohoActivities()

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

  // Load initial data
  React.useEffect(() => {
    // Refresh Zoho data on component mount
    refreshLeads()
    refreshContacts()
  }, [refreshLeads, refreshContacts])

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

  const handleProspectSelect = (prospectId: string) => {
    setSelectedProspectId(prospectId)
    setIsMetadataPanelOpen(true)
    // Load activities for the selected prospect
    const prospect = leads.find(l => l.id === prospectId) || contacts.find(c => c.id === prospectId)
    if (prospect) {
      const module = leads.find(l => l.id === prospectId) ? 'Leads' : 'Contacts'
      getActivitiesForRecord(module, prospectId)
    }
  }

  const handleInterviewSelect = (interviewId: string) => {
    // TODO: Implement interview selection logic
    toast(`Interview ${interviewId} selected`)
  }

  const handleContactAction = async (action: 'call' | 'email' | 'sms' | 'meeting', data: any) => {
    try {
      switch (action) {
        case 'call':
          toast(`Initiating call to ${data.phone}`)
          // TODO: Integrate with voice calling system
          break
        case 'email':
          toast(`Opening email to ${data.email}`)
          // TODO: Integrate with email system
          break
        case 'sms':
          toast(`Sending SMS to ${data.phone}`)
          // TODO: Integrate with SMS system
          break
        case 'meeting':
          toast(`Scheduling meeting with ${data.name}`)
          // TODO: Integrate with calendar system
          break
      }
    } catch (error) {
      toast.error(`Failed to ${action}: ${error}`)
    }
  }

  // Transform data for recruiting sidebar
  const pastConversations = sessions
    .filter(session => session.agentType === 'recruiting')
    .map(session => ({
      id: session.id,
      title: session.title,
      participantName: 'User',
      participantAvatar: undefined,
      lastMessage: session.messages[session.messages.length - 1]?.content || 'No messages yet',
      timestamp: session.updatedAt,
      messageCount: session.messages.length,
      status: session.status as 'active' | 'archived' | 'paused',
      unreadCount: 0, // TODO: implement unread count logic
      topics: ['recruiting', 'conversation'], // TODO: extract topics from messages
      outcome: undefined, // TODO: determine conversation outcome
    }))

  // Transform Zoho leads/contacts to active prospects
  const activeProspects = [
    ...leads.map(lead => ({
      id: lead.id,
      name: `${lead.firstName} ${lead.lastName}`,
      avatar: undefined,
      email: lead.email,
      phone: lead.phone || lead.mobile || '',
      company: lead.company,
      position: lead.designation,
      leadScore: lead.leadScore || 0,
      lastContact: lead.modifiedTime,
      status: lead.rating?.toLowerCase() as 'hot' | 'warm' | 'cold',
      source: lead.leadSource,
      tags: lead.tags || [],
      nextAction: undefined, // TODO: derive from activities
    })),
    ...contacts.map(contact => ({
      id: contact.id,
      name: `${contact.firstName} ${contact.lastName}`,
      avatar: undefined,
      email: contact.email,
      phone: contact.phone || contact.mobile || '',
      company: contact.accountName,
      position: contact.title,
      leadScore: 75, // Default score for contacts
      lastContact: contact.modifiedTime,
      status: 'qualified' as const,
      source: contact.leadSource || 'Contact',
      tags: contact.tags || [],
      nextAction: undefined, // TODO: derive from activities
    }))
  ]

  // Mock scheduled interviews - TODO: Replace with real data
  const scheduledInterviews = [
    {
      id: '1',
      candidateName: 'Sarah Johnson',
      candidateAvatar: undefined,
      position: 'Senior Developer',
      scheduledTime: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours from now
      type: 'video' as const,
      status: 'upcoming' as const,
      duration: 60,
      interviewerName: 'John Smith',
      notes: 'Technical interview'
    },
    {
      id: '2',
      candidateName: 'Mike Chen',
      candidateAvatar: undefined,
      position: 'Product Manager',
      scheduledTime: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // Tomorrow
      type: 'phone' as const,
      status: 'upcoming' as const,
      duration: 45,
      interviewerName: 'Emily Davis',
      notes: 'Initial screening'
    }
  ]

  const selectedProspect = selectedProspectId
    ? leads.find(l => l.id === selectedProspectId) || contacts.find(c => c.id === selectedProspectId)
    : null

  return (
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
        <RecruitingSidebar
          interviews={scheduledInterviews}
          prospects={activeProspects}
          conversations={pastConversations}
          activeConversationId={currentSession?.id}
          onConversationSelect={handleConversationSelect}
          onNewConversation={handleNewConversation}
          onInterviewSelect={handleInterviewSelect}
          onProspectSelect={handleProspectSelect}
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
              <div className="h-10 w-10 rounded-full bg-gradient-primary flex items-center justify-center shrink-0 overflow-hidden">
                <Image
                  src="/favicon-32x32.png"
                  alt="AI Recruiting Assistant"
                  width={24}
                  height={24}
                  className="rounded-full"
                />
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

          {/* Metadata Panel */}
          {isMetadataPanelOpen && (
            <div className="w-80 max-w-[calc(100vw-20rem)] border-l bg-background overflow-y-auto hidden xl:block shrink-0">
              <div className="p-4 space-y-6">
                {/* Selected Prospect Details */}
                {selectedProspect && (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-foreground">Prospect Details</h3>
                      <Button
                        size="icon"
                        variant="outline"
                        onClick={() => setIsMetadataPanelOpen(false)}
                        className="h-6 w-6"
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                    <ZohoProspectCard
                      type={leads.find(l => l.id === selectedProspectId) ? 'lead' : 'contact'}
                      data={selectedProspect}
                      activities={activities}
                      onContactAction={handleContactAction}
                      onEdit={() => toast('Edit prospect functionality coming soon')}
                      onViewDetails={() => toast('View details functionality coming soon')}
                      compact={false}
                    />
                  </div>
                )}

                {/* System Status */}
                <div>
                  <h3 className="font-semibold text-foreground mb-3">System Status</h3>
                  <div className="space-y-3">
                    {/* Agent Status */}
                    <div className="flex items-center gap-2 text-sm">
                      <MessageSquare className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">Agent:</span>
                      <Badge variant="success">Online</Badge>
                    </div>

                    {/* MCP Servers */}
                    <div className="flex items-center gap-2 text-sm">
                      <Database className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">MCP Servers:</span>
                      <Badge variant={mcpLoading ? 'warning' : serverStatus.length > 0 ? 'success' : 'destructive'}>
                        {mcpLoading ? 'Loading...' : `${serverStatus.length} Active`}
                      </Badge>
                    </div>

                    {/* Data Loading Status */}
                    <div className="flex items-center gap-2 text-sm">
                      <Activity className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">Data Sync:</span>
                      <Badge variant={leadsLoading || contactsLoading ? 'warning' : 'success'}>
                        {leadsLoading || contactsLoading ? 'Syncing...' : 'Up to date'}
                      </Badge>
                    </div>

                    {/* Voice/Video Status */}
                    <div className="flex items-center gap-2 text-sm">
                      <Mic className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">Voice:</span>
                      <Badge variant="success">Ready</Badge>
                    </div>
                  </div>
                </div>

                {/* Data Summary */}
                <div>
                  <h3 className="font-semibold text-foreground mb-3">Data Summary</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Active Leads:</span>
                      <span className="font-medium">{leads.length}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Contacts:</span>
                      <span className="font-medium">{contacts.length}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Conversations:</span>
                      <span className="font-medium">{pastConversations.length}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Interviews:</span>
                      <span className="font-medium">{scheduledInterviews.length}</span>
                    </div>
                  </div>
                </div>

                {/* Analytics Preview */}
                {analytics && (
                  <div>
                    <h3 className="font-semibold text-foreground mb-3">Analytics</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Total Prospects:</span>
                        <span className="font-medium">{analytics.total_prospects}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Response Rate:</span>
                        <span className="font-medium">{(analytics.response_rate * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Conversion Rate:</span>
                        <span className="font-medium">{(analytics.conversion_rate * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Agent Capabilities */}
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

                {/* Session Info */}
                <div>
                  <h3 className="font-semibold text-foreground mb-3">Session Info</h3>
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <div>Messages: {messages.length}</div>
                    <div>Started: {currentSession ? new Date(currentSession.createdAt).toLocaleString() : 'N/A'}</div>
                    <div>Last Activity: {currentSession ? new Date(currentSession.updatedAt).toLocaleString() : 'N/A'}</div>
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