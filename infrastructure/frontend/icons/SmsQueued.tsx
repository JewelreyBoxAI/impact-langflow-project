'use client'

import * as React from "react"
import { Clock } from "lucide-react"

interface SmsQueuedProps {
  className?: string
}

export function SmsQueued({ className }: SmsQueuedProps) {
  return (
    <Clock
      className={`text-sms-queued ${className}`}
      size={12}
    />
  )
}