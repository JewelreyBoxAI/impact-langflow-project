'use client'

import * as React from "react"
import { Circle } from "lucide-react"

interface SmsIdleProps {
  className?: string
}

export function SmsIdle({ className }: SmsIdleProps) {
  return (
    <Circle
      className={`text-sms-idle fill-current ${className}`}
      size={8}
    />
  )
}