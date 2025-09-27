'use client'

import * as React from "react"
import { Mic, MicOff } from "lucide-react"
import { Button } from "./Button"
import { cn } from "@/lib/utils"

interface VoiceToggleProps {
  isActive: boolean
  onToggle: () => void
  disabled?: boolean
  className?: string
}

export function VoiceToggle({ isActive, onToggle, disabled = false, className }: VoiceToggleProps) {
  return (
    <Button
      variant={isActive ? "default" : "outline"}
      size="icon"
      onClick={onToggle}
      disabled={disabled}
      className={cn(
        "transition-all duration-200",
        isActive && "bg-primary text-primary-foreground animate-pulse-soft",
        className
      )}
      title={isActive ? "Stop voice input" : "Start voice input"}
    >
      {isActive ? (
        <MicOff className="h-4 w-4" />
      ) : (
        <Mic className="h-4 w-4" />
      )}
    </Button>
  )
}