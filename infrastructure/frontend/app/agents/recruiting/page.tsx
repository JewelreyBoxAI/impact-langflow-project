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
} from "lucide-react"
import toast from "react-hot-toast"

export default function RecruitingPage() {
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false)
  const [isMetadataPanelOpen, setIsMetadataPanelOpen] = React.useState(false)

  const { setCurrentAgent } = useAgent()
  const { sessions, currentSession, createSession, selectSession } = useSession()
  const { messages, isLoading, sendMessage } = useChat({
    onError: (error) => {
      toast.error(error.message || 'Failed to send message')
    }
  })

  // Set current agent to recruiting on mount
  React.useEffect(() => {
    setCurrentAgent('recruiting')
  }, [setCurrentAgent])

  // Create initial session if none exists
  React.useEffect(() => {
    if (sessions.length === 0) {
      createSession('recruiting', 'Welcome to Katelyn')
    }
  }, [sessions.length, createSession])

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
    <div className="h-screen flex bg-background">
      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        "fixed inset-y-0 left-0 z-50 w-80 bg-background border-r transform transition-transform duration-200 ease-in-out lg:relative lg:translate-x-0",
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
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="flex items-center gap-3">
            {/* Mobile Menu Button */}
            <Button
              variant="outline"
              size="icon"
              className="lg:hidden"
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            >
              {isSidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </Button>

            {/* Agent Info */}
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-gradient-primary flex items-center justify-center text-white font-medium">
                K
              </div>
              <div>
                <h1 className="font-semibold text-foreground">{agentConfig.name}</h1>
                <p className="text-sm text-muted-foreground">{agentConfig.description}</p>
              </div>
            </div>

            {/* Features */}
            <div className="hidden md:flex items-center gap-2">
              {agentConfig.features.map((feature) => (
                <Badge key={feature} variant="secondary" className="text-xs">
                  {feature}
                </Badge>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
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
        <div className="flex-1 flex min-h-0">
          {/* Chat Interface */}
          <div className="flex-1 min-w-0">
            <ChatInterface
              messages={messages}
              onSendMessage={sendMessage}
              isLoading={isLoading}
            />
          </div>

          {/* Metadata Panel */}
          {isMetadataPanelOpen && (
            <div className="w-80 border-l bg-background p-4 overflow-y-auto hidden xl:block">
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
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-foreground mb-3">Capabilities</h3>
                  <div className="space-y-2">
                    {agentConfig.features.map((feature) => (
                      <div key={feature} className="flex items-center gap-2 text-sm">
                        <div className="h-2 w-2 rounded-full bg-green-500" />
                        <span>{feature}</span>
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
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}