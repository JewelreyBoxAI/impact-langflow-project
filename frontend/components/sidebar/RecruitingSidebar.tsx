'use client'

import * as React from "react"
import { Plus, Search, Calendar, Users, MessageSquare, Clock, Phone, Mail, MapPin, Briefcase } from "lucide-react"
import { Button } from "@/components/shared/Button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/shared/Avatar"
import { Badge } from "@/components/shared/Badge"
import { formatTimestamp, truncateText, cn } from "@/lib/utils"
import { format, isToday, isTomorrow, parseISO } from "date-fns"

// Enhanced types for recruiting-specific data
interface Interview {
  id: string
  candidateName: string
  candidateAvatar?: string
  position: string
  scheduledTime: string
  type: 'phone' | 'video' | 'in-person'
  status: 'upcoming' | 'in-progress' | 'completed' | 'cancelled'
  location?: string
  duration: number // minutes
  interviewerName: string
  notes?: string
}

interface ActiveProspect {
  id: string
  name: string
  avatar?: string
  email: string
  phone: string
  company?: string
  position?: string
  leadScore: number // 0-100 from Zoho
  lastContact: string
  status: 'hot' | 'warm' | 'cold' | 'qualified' | 'unqualified'
  source: string
  tags: string[]
  nextAction?: {
    type: 'call' | 'email' | 'meeting'
    dueDate: string
  }
}

interface PastConversation {
  id: string
  title: string
  participantName: string
  participantAvatar?: string
  lastMessage: string
  timestamp: string
  messageCount: number
  status: 'active' | 'archived' | 'paused'
  unreadCount?: number
  topics: string[]
  outcome?: 'qualified' | 'interested' | 'not-interested' | 'follow-up'
}

interface RecruitingSidebarProps {
  interviews: Interview[]
  prospects: ActiveProspect[]
  conversations: PastConversation[]
  activeConversationId?: string
  onConversationSelect: (conversationId: string) => void
  onNewConversation: () => void
  onInterviewSelect?: (interviewId: string) => void
  onProspectSelect?: (prospectId: string) => void
  className?: string
}

export function RecruitingSidebar({
  interviews,
  prospects,
  conversations,
  activeConversationId,
  onConversationSelect,
  onNewConversation,
  onInterviewSelect,
  onProspectSelect,
  className
}: RecruitingSidebarProps) {
  const [searchQuery, setSearchQuery] = React.useState("")
  const [activeSection, setActiveSection] = React.useState<'conversations' | 'prospects' | 'interviews'>('conversations')

  // Filter data based on search
  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.participantName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const filteredProspects = prospects.filter(prospect =>
    prospect.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    prospect.company?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    prospect.position?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const filteredInterviews = interviews.filter(interview =>
    interview.candidateName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    interview.position.toLowerCase().includes(searchQuery.toLowerCase()) ||
    interview.interviewerName.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Sort prospects by lead score (highest first)
  const sortedProspects = [...filteredProspects].sort((a, b) => b.leadScore - a.leadScore)

  // Sort interviews by scheduled time
  const sortedInterviews = [...filteredInterviews].sort((a, b) =>
    new Date(a.scheduledTime).getTime() - new Date(b.scheduledTime).getTime()
  )

  const getProspectStatusColor = (status: ActiveProspect['status']) => {
    switch (status) {
      case 'hot': return 'destructive'
      case 'warm': return 'warning'
      case 'qualified': return 'success'
      case 'cold': return 'secondary'
      case 'unqualified': return 'secondary'
      default: return 'secondary'
    }
  }

  const getInterviewStatusColor = (status: Interview['status']) => {
    switch (status) {
      case 'upcoming': return 'default'
      case 'in-progress': return 'warning'
      case 'completed': return 'success'
      case 'cancelled': return 'destructive'
      default: return 'secondary'
    }
  }

  const formatInterviewTime = (dateString: string) => {
    const date = parseISO(dateString)
    if (isToday(date)) {
      return `Today ${format(date, 'h:mm a')}`
    } else if (isTomorrow(date)) {
      return `Tomorrow ${format(date, 'h:mm a')}`
    } else {
      return format(date, 'MMM d, h:mm a')
    }
  }

  const renderInterviewIcon = (type: Interview['type']) => {
    switch (type) {
      case 'phone': return <Phone className="h-3 w-3" />
      case 'video': return <MessageSquare className="h-3 w-3" />
      case 'in-person': return <MapPin className="h-3 w-3" />
      default: return <Calendar className="h-3 w-3" />
    }
  }

  return (
    <div className={cn("flex flex-col h-full bg-background border-r", className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="font-semibold text-foreground">Recruiting</h2>
        <Button
          size="icon"
          variant="outline"
          onClick={onNewConversation}
          className="h-8 w-8"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* Search */}
      <div className="p-4 border-b">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search conversations, prospects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm bg-muted border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          />
        </div>
      </div>

      {/* Section Tabs */}
      <div className="flex border-b">
        <button
          onClick={() => setActiveSection('conversations')}
          className={cn(
            "flex-1 px-3 py-2 text-sm font-medium transition-colors",
            activeSection === 'conversations'
              ? "text-primary border-b-2 border-primary bg-primary/5"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <div className="flex items-center justify-center gap-2">
            <MessageSquare className="h-4 w-4" />
            <span className="hidden sm:inline">Conversations</span>
          </div>
        </button>

        <button
          onClick={() => setActiveSection('prospects')}
          className={cn(
            "flex-1 px-3 py-2 text-sm font-medium transition-colors",
            activeSection === 'prospects'
              ? "text-primary border-b-2 border-primary bg-primary/5"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <div className="flex items-center justify-center gap-2">
            <Users className="h-4 w-4" />
            <span className="hidden sm:inline">Prospects</span>
          </div>
        </button>

        <button
          onClick={() => setActiveSection('interviews')}
          className={cn(
            "flex-1 px-3 py-2 text-sm font-medium transition-colors",
            activeSection === 'interviews'
              ? "text-primary border-b-2 border-primary bg-primary/5"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <div className="flex items-center justify-center gap-2">
            <Calendar className="h-4 w-4" />
            <span className="hidden sm:inline">Interviews</span>
          </div>
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto">
        {/* Past Conversations (Top) */}
        {activeSection === 'conversations' && (
          <div className="space-y-1 p-2">
            {filteredConversations.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-center text-muted-foreground">
                <MessageSquare className="h-8 w-8 mb-2" />
                <div className="text-sm">
                  {searchQuery ? 'No conversations found' : 'No conversations yet'}
                </div>
              </div>
            ) : (
              filteredConversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => onConversationSelect(conversation.id)}
                  className={cn(
                    "w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors",
                    "hover:bg-accent",
                    activeConversationId === conversation.id && "bg-primary text-primary-foreground"
                  )}
                >
                  <Avatar className="h-10 w-10 shrink-0">
                    <AvatarImage src={conversation.participantAvatar} />
                    <AvatarFallback className="text-sm">
                      {conversation.participantName?.charAt(0) || 'U'}
                    </AvatarFallback>
                  </Avatar>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="font-medium text-sm truncate">
                        {conversation.title}
                      </h3>
                      {conversation.unreadCount && conversation.unreadCount > 0 && (
                        <Badge variant="destructive" className="text-xs px-1.5 py-0.5 h-5">
                          {conversation.unreadCount > 9 ? '9+' : conversation.unreadCount}
                        </Badge>
                      )}
                    </div>

                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {truncateText(conversation.lastMessage, 80)}
                    </p>

                    <div className="flex items-center justify-between mt-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {formatTimestamp(conversation.timestamp)}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {conversation.messageCount} msgs
                        </span>
                      </div>

                      <div className="flex items-center gap-1">
                        {conversation.outcome && (
                          <Badge variant="outline" className="text-xs px-1.5 py-0.5">
                            {conversation.outcome}
                          </Badge>
                        )}
                        <Badge
                          variant={
                            conversation.status === 'active' ? 'success' :
                            conversation.status === 'paused' ? 'warning' : 'secondary'
                          }
                          className="text-xs px-1.5 py-0.5"
                        >
                          {conversation.status}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        )}

        {/* Active Prospects (Middle) */}
        {activeSection === 'prospects' && (
          <div className="space-y-1 p-2">
            {sortedProspects.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-center text-muted-foreground">
                <Users className="h-8 w-8 mb-2" />
                <div className="text-sm">
                  {searchQuery ? 'No prospects found' : 'No active prospects'}
                </div>
              </div>
            ) : (
              sortedProspects.map((prospect) => (
                <button
                  key={prospect.id}
                  onClick={() => onProspectSelect?.(prospect.id)}
                  className="w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors hover:bg-accent"
                >
                  <Avatar className="h-10 w-10 shrink-0">
                    <AvatarImage src={prospect.avatar} />
                    <AvatarFallback className="text-sm">
                      {prospect.name.charAt(0)}
                    </AvatarFallback>
                  </Avatar>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="font-medium text-sm truncate">
                        {prospect.name}
                      </h3>
                      <div className="flex items-center gap-1">
                        <Badge variant={getProspectStatusColor(prospect.status)} className="text-xs px-1.5 py-0.5">
                          {prospect.status}
                        </Badge>
                        <div className="text-xs font-medium text-primary">
                          {prospect.leadScore}
                        </div>
                      </div>
                    </div>

                    <div className="space-y-1 mt-1">
                      {prospect.company && (
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Briefcase className="h-3 w-3" />
                          <span>{prospect.company}</span>
                        </div>
                      )}

                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Mail className="h-3 w-3" />
                        <span className="truncate">{prospect.email}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-muted-foreground">
                        Last: {formatTimestamp(prospect.lastContact)}
                      </span>

                      {prospect.nextAction && (
                        <Badge variant="outline" className="text-xs px-1.5 py-0.5">
                          {prospect.nextAction.type}
                        </Badge>
                      )}
                    </div>

                    {prospect.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {prospect.tags.slice(0, 2).map((tag, index) => (
                          <Badge key={index} variant="secondary" className="text-xs px-1.5 py-0.5">
                            {tag}
                          </Badge>
                        ))}
                        {prospect.tags.length > 2 && (
                          <span className="text-xs text-muted-foreground">
                            +{prospect.tags.length - 2}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        )}

        {/* Scheduled Interviews (Bottom) */}
        {activeSection === 'interviews' && (
          <div className="space-y-1 p-2">
            {sortedInterviews.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-center text-muted-foreground">
                <Calendar className="h-8 w-8 mb-2" />
                <div className="text-sm">
                  {searchQuery ? 'No interviews found' : 'No scheduled interviews'}
                </div>
              </div>
            ) : (
              sortedInterviews.map((interview) => (
                <button
                  key={interview.id}
                  onClick={() => onInterviewSelect?.(interview.id)}
                  className="w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors hover:bg-accent"
                >
                  <Avatar className="h-10 w-10 shrink-0">
                    <AvatarImage src={interview.candidateAvatar} />
                    <AvatarFallback className="text-sm">
                      {interview.candidateName.charAt(0)}
                    </AvatarFallback>
                  </Avatar>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="font-medium text-sm truncate">
                        {interview.candidateName}
                      </h3>
                      <Badge variant={getInterviewStatusColor(interview.status)} className="text-xs px-1.5 py-0.5">
                        {interview.status}
                      </Badge>
                    </div>

                    <div className="space-y-1 mt-1">
                      <div className="text-xs text-muted-foreground truncate">
                        {interview.position}
                      </div>

                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          {renderInterviewIcon(interview.type)}
                          <span>{interview.type}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          <span>{interview.duration}m</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs font-medium text-foreground">
                        {formatInterviewTime(interview.scheduledTime)}
                      </span>

                      <span className="text-xs text-muted-foreground">
                        with {interview.interviewerName}
                      </span>
                    </div>

                    {interview.location && interview.type === 'in-person' && (
                      <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                        <MapPin className="h-3 w-3" />
                        <span className="truncate">{interview.location}</span>
                      </div>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}