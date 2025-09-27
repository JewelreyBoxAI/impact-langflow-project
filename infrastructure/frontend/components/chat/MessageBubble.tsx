'use client'

import * as React from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/shared/Avatar"
import { SmsStatusIcon } from "./SmsStatusIcon"
import { formatTimestamp, cn } from "@/lib/utils"

export interface Message {
  id: string
  content: string
  sender: 'user' | 'agent' | 'system'
  timestamp: string
  smsStatus?: 'delivered' | 'failed' | 'queued' | 'idle'
  senderName?: string
  senderAvatar?: string
}

interface MessageBubbleProps {
  message: Message
  className?: string
}

export function MessageBubble({ message, className }: MessageBubbleProps) {
  const isUser = message.sender === 'user'
  const isSystem = message.sender === 'system'

  return (
    <div className={cn(
      "flex gap-3 p-4 message-enter",
      isUser && "flex-row-reverse",
      className
    )}>
      {/* Avatar */}
      <Avatar className={cn(
        "h-8 w-8 shrink-0",
        isSystem && "hidden"
      )}>
        <AvatarImage src={message.senderAvatar} />
        <AvatarFallback className={cn(
          "text-xs font-medium",
          isUser && "bg-primary text-primary-foreground",
          !isUser && !isSystem && "bg-agent-recruiting text-white"
        )}>
          {isUser ? 'U' : message.senderName?.charAt(0) || 'A'}
        </AvatarFallback>
      </Avatar>

      {/* Message Content */}
      <div className={cn(
        "flex flex-col gap-1 max-w-[70%]",
        isUser && "items-end",
        isSystem && "max-w-full items-center"
      )}>
        {/* Sender Name */}
        {!isUser && !isSystem && (
          <div className="text-xs text-muted-foreground font-medium">
            {message.senderName || 'Katelyn'}
          </div>
        )}

        {/* Message Bubble */}
        <div className={cn(
          "rounded-lg px-3 py-2 text-sm break-words",
          isUser && "message-bubble-user",
          !isUser && !isSystem && "message-bubble-agent",
          isSystem && "message-bubble-system text-center"
        )}>
          {message.content}
        </div>

        {/* Timestamp and SMS Status */}
        <div className={cn(
          "flex items-center gap-2 text-xs text-muted-foreground",
          isUser && "flex-row-reverse",
          isSystem && "justify-center"
        )}>
          <span>{formatTimestamp(message.timestamp)}</span>

          {/* SMS Status Icon */}
          {message.smsStatus && message.smsStatus !== 'idle' && (
            <SmsStatusIcon
              status={message.smsStatus}
              className="ml-1"
            />
          )}
        </div>
      </div>
    </div>
  )
}