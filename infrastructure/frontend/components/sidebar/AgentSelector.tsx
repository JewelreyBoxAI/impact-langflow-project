'use client'

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Users,
  UserCheck,
  Settings,
  BarChart3,
  ChevronDown
} from "lucide-react"
import { Badge } from "@/components/shared/Badge"
import { cn } from "@/lib/utils"

interface Agent {
  id: string
  name: string
  path: string
  icon: React.ElementType
  color: string
  isActive?: boolean
  badge?: string
}

const agents: Agent[] = [
  {
    id: 'recruiting',
    name: 'Recruiting',
    path: '/agents/recruiting',
    icon: Users,
    color: 'text-agent-recruiting',
    isActive: true,
  },
  {
    id: 'supervisor',
    name: 'Supervisor',
    path: '/agents/supervisor',
    icon: UserCheck,
    color: 'text-purple-600',
    badge: 'Soon',
  },
  {
    id: 'admin',
    name: 'Admin',
    path: '/agents/admin',
    icon: Settings,
    color: 'text-red-600',
    badge: 'Soon',
  },
  {
    id: 'operations',
    name: 'Operations',
    path: '/agents/operations',
    icon: BarChart3,
    color: 'text-emerald-600',
    badge: 'Soon',
  },
]

interface AgentSelectorProps {
  isCollapsed?: boolean
  className?: string
}

export function AgentSelector({ isCollapsed = false, className }: AgentSelectorProps) {
  const pathname = usePathname()

  return (
    <div className={cn("space-y-1", className)}>
      <div className={cn(
        "px-3 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider",
        isCollapsed && "text-center"
      )}>
        {isCollapsed ? "A" : "Agents"}
      </div>

      {agents.map((agent) => {
        const Icon = agent.icon
        const isActive = pathname.startsWith(agent.path)

        return (
          <Link
            key={agent.id}
            href={agent.path}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              isActive && "bg-primary text-primary-foreground",
              !agent.isActive && "opacity-60 cursor-not-allowed pointer-events-none",
              isCollapsed && "justify-center px-2"
            )}
          >
            <Icon className={cn("h-4 w-4 shrink-0", !isActive && agent.color)} />

            {!isCollapsed && (
              <>
                <span className="flex-1">{agent.name}</span>
                {agent.badge && (
                  <Badge
                    variant="secondary"
                    className="text-xs px-2 py-0.5"
                  >
                    {agent.badge}
                  </Badge>
                )}
              </>
            )}
          </Link>
        )
      })}
    </div>
  )
}