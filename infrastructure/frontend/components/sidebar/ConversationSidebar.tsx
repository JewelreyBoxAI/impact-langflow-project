'use client'

import * as React from "react"
import { Plus, Search, MoreVertical, MessageSquare } from "lucide-react"
import { Button } from "@/components/shared/Button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/shared/Avatar"
import { Badge } from "@/components/shared/Badge"
import { formatTimestamp, truncateText, cn } from "@/lib/utils"

interface Conversation {
  id: string
  title: string
  lastMessage: string
  timestamp: string
  unreadCount?: number
  status: 'active' | 'archived' | 'paused'
  participant?: {
    name: string
    avatar?: string
  }
}

interface ConversationSidebarProps {
  conversations: Conversation[]
  activeConversationId?: string
  onConversationSelect: (conversationId: string) => void
  onNewConversation: () => void
  isCollapsed?: boolean
  className?: string
}

export function ConversationSidebar({
  conversations,
  activeConversationId,
  onConversationSelect,
  onNewConversation,
  isCollapsed = false,
  className
}: ConversationSidebarProps) {
  const [searchQuery, setSearchQuery] = React.useState("")

  const filteredConversations = conversations.filter(conversation =>
    conversation.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conversation.lastMessage.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conversation.participant?.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (isCollapsed) {
    return (
      <div className={cn("flex flex-col gap-2 p-2", className)}>
        {/* New Conversation Button */}
        <Button
          size="icon"
          onClick={onNewConversation}
          className="h-10 w-10"
          title="New conversation"
        >
          <Plus className="h-4 w-4" />
        </Button>

        {/* Conversations */}
        <div className="space-y-1">
          {filteredConversations.slice(0, 8).map((conversation) => (
            <button
              key={conversation.id}
              onClick={() => onConversationSelect(conversation.id)}
              className={cn(
                "relative flex h-10 w-10 items-center justify-center rounded-lg transition-colors",
                "hover:bg-accent",
                activeConversationId === conversation.id && "bg-primary text-primary-foreground"
              )}
              title={conversation.title}
            >
              {conversation.participant?.avatar ? (
                <Avatar className="h-6 w-6">
                  <AvatarImage src={conversation.participant.avatar} />
                  <AvatarFallback className="text-xs">
                    {conversation.participant.name.charAt(0)}
                  </AvatarFallback>
                </Avatar>
              ) : (
                <MessageSquare className="h-4 w-4" />
              )}

              {conversation.unreadCount && conversation.unreadCount > 0 && (
                <div className="absolute -right-1 -top-1 h-4 w-4 rounded-full bg-destructive text-destructive-foreground flex items-center justify-center text-xs font-medium">
                  {conversation.unreadCount > 9 ? '9+' : conversation.unreadCount}
                </div>
              )}
            </button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="font-semibold text-foreground">Conversations</h2>
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
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm bg-muted border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          />
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {filteredConversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-center text-muted-foreground">
            <MessageSquare className="h-8 w-8 mb-2" />
            <div className="text-sm">
              {searchQuery ? 'No conversations found' : 'No conversations yet'}
            </div>
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {filteredConversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() => onConversationSelect(conversation.id)}
                className={cn(
                  "w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors",
                  "hover:bg-accent",
                  activeConversationId === conversation.id && "bg-primary text-primary-foreground"
                )}
              >
                {/* Avatar */}
                <Avatar className="h-10 w-10 shrink-0">
                  <AvatarImage src={conversation.participant?.avatar} />
                  <AvatarFallback className="text-sm">
                    {conversation.participant?.name?.charAt(0) || 'U'}
                  </AvatarFallback>
                </Avatar>

                {/* Content */}
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
                    <span className="text-xs text-muted-foreground">
                      {formatTimestamp(conversation.timestamp)}
                    </span>

                    <Badge
                      variant={
                        conversation.status === 'active' ? 'success' :
                        conversation.status === 'paused' ? 'warning' : 'secondary'
                      }
                      className="text-xs px-2 py-0.5"
                    >
                      {conversation.status}
                    </Badge>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}