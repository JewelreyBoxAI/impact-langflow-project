'use client'

import * as React from "react"
import { Send, Paperclip } from "lucide-react"
import { Button } from "@/components/shared/Button"
import { VoiceToggle } from "@/components/shared/VoiceToggle"
import { cn } from "@/lib/utils"

interface ComposeBarProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  onVoiceToggle: () => void
  isVoiceActive: boolean
  isLoading?: boolean
  placeholder?: string
  disabled?: boolean
  className?: string
}

export function ComposeBar({
  value,
  onChange,
  onSend,
  onVoiceToggle,
  isVoiceActive,
  isLoading = false,
  placeholder = "Type a message...",
  disabled = false,
  className
}: ComposeBarProps) {
  const [isComposing, setIsComposing] = React.useState(false)
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault()
      if (value.trim() && !isLoading && !disabled) {
        onSend()
      }
    }
  }

  const handleSend = () => {
    if (value.trim() && !isLoading && !disabled) {
      onSend()
    }
  }

  // Auto-resize textarea
  React.useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [value])

  return (
    <div className={cn(
      "flex items-end gap-2 p-4 bg-background border-t",
      className
    )}>
      {/* Voice Toggle */}
      <VoiceToggle
        isActive={isVoiceActive}
        onToggle={onVoiceToggle}
        disabled={disabled}
        className="mb-2"
      />

      {/* Input Container */}
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onCompositionStart={() => setIsComposing(true)}
          onCompositionEnd={() => setIsComposing(false)}
          placeholder={isVoiceActive ? "Listening..." : placeholder}
          disabled={disabled || isVoiceActive}
          className={cn(
            "w-full min-h-[44px] max-h-[120px] px-4 py-3 pr-12",
            "bg-muted border border-input rounded-lg",
            "text-sm placeholder:text-muted-foreground",
            "resize-none focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            isVoiceActive && "animate-pulse-soft"
          )}
          rows={1}
        />

        {/* Attachment Button */}
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8"
          disabled={disabled}
          title="Attach file"
        >
          <Paperclip className="h-4 w-4" />
        </Button>
      </div>

      {/* Send Button */}
      <Button
        onClick={handleSend}
        disabled={!value.trim() || isLoading || disabled}
        className="mb-2 h-11 w-11 p-0"
        title="Send message"
      >
        <Send className="h-4 w-4" />
      </Button>
    </div>
  )
}