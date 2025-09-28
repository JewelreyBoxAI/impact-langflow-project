'use client'

import * as React from "react"
import { MessageBubble, type Message } from "./MessageBubble"
import { ComposeBar } from "./ComposeBar"
import { cn } from "@/lib/utils"

interface ChatInterfaceProps {
  messages: Message[]
  onSendMessage: (content: string) => void
  isLoading?: boolean
  className?: string
}

export function ChatInterface({
  messages,
  onSendMessage,
  isLoading = false,
  className
}: ChatInterfaceProps) {
  const [inputValue, setInputValue] = React.useState("")
  const [isVoiceActive, setIsVoiceActive] = React.useState(false)
  const messagesEndRef = React.useRef<HTMLDivElement>(null)
  const messagesContainerRef = React.useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim())
      setInputValue("")
    }
  }

  const handleVoiceToggle = () => {
    setIsVoiceActive(!isVoiceActive)
    // TODO: bind to voice SDK
  }

  return (
    <div className={cn("chat-container", className)}>
      {/* Messages Container */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto scroll-smooth"
      >
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-muted-foreground">
              <div className="text-lg font-medium mb-2">Welcome to Recruiting Agent</div>
              <div className="text-sm">Your AI recruiting assistant is ready to help!</div>
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
              />
            ))}
            {/* Typing indicator */}
            {isLoading && (
              <div className="flex gap-3 p-4">
                <div className="h-8 w-8 rounded-full bg-agent-recruiting flex items-center justify-center">
                  <span className="text-white text-xs font-medium">R</span>
                </div>
                <div className="flex flex-col gap-1">
                  <div className="text-xs text-muted-foreground font-medium">
                    Recruiting Agent
                  </div>
                  <div className="bg-muted rounded-lg px-3 py-2 text-sm typing-indicator">
                    <div className="flex space-x-1">
                      <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce"></div>
                      <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                      <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Compose Bar */}
      <ComposeBar
        value={inputValue}
        onChange={setInputValue}
        onSend={handleSend}
        onVoiceToggle={handleVoiceToggle}
        isVoiceActive={isVoiceActive}
        isLoading={isLoading}
      />
    </div>
  )
}