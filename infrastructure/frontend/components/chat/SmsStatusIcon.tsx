'use client'

import * as React from "react"
import * as TooltipPrimitive from "@radix-ui/react-tooltip"
import { SmsDelivered } from "@/icons/SmsDelivered"
import { SmsFailed } from "@/icons/SmsFailed"
import { SmsQueued } from "@/icons/SmsQueued"
import { SmsIdle } from "@/icons/SmsIdle"
import { cn } from "@/lib/utils"

const TooltipProvider = TooltipPrimitive.Provider
const Tooltip = TooltipPrimitive.Root
const TooltipTrigger = TooltipPrimitive.Trigger

const TooltipContent = React.forwardRef<
  React.ElementRef<typeof TooltipPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <TooltipPrimitive.Content
    ref={ref}
    sideOffset={sideOffset}
    className={cn(
      "z-50 overflow-hidden rounded-md border bg-popover px-3 py-1.5 text-xs text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
      className
    )}
    {...props}
  />
))
TooltipContent.displayName = TooltipPrimitive.Content.displayName

type SmsStatus = 'delivered' | 'failed' | 'queued' | 'idle'

interface SmsStatusIconProps {
  status: SmsStatus
  className?: string
  showTooltip?: boolean
}

const statusConfig = {
  delivered: {
    icon: SmsDelivered,
    label: 'Message delivered',
    color: 'text-green-500',
  },
  failed: {
    icon: SmsFailed,
    label: 'Message failed',
    color: 'text-red-500',
  },
  queued: {
    icon: SmsQueued,
    label: 'Message queued',
    color: 'text-yellow-500',
  },
  idle: {
    icon: SmsIdle,
    label: 'No SMS status',
    color: 'text-gray-400',
  },
}

export function SmsStatusIcon({ status, className, showTooltip = true }: SmsStatusIconProps) {
  const config = statusConfig[status]
  const IconComponent = config.icon

  const icon = (
    <div className={cn("flex items-center justify-center", className)}>
      <IconComponent className={cn("transition-colors", config.color)} />
    </div>
  )

  if (!showTooltip) {
    return icon
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          {icon}
        </TooltipTrigger>
        <TooltipContent>
          <p>{config.label}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}