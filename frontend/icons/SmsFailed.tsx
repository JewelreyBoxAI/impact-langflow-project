'use client'

import * as React from "react"
import { X } from "lucide-react"

interface SmsFailedProps {
  className?: string
}

export function SmsFailed({ className }: SmsFailedProps) {
  return (
    <X
      className={`text-sms-failed ${className}`}
      size={12}
    />
  )
}