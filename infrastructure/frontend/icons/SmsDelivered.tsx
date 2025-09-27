'use client'

import * as React from "react"
import { Check } from "lucide-react"

interface SmsDeliveredProps {
  className?: string
}

export function SmsDelivered({ className }: SmsDeliveredProps) {
  return (
    <Check
      className={`text-sms-delivered ${className}`}
      size={12}
    />
  )
}