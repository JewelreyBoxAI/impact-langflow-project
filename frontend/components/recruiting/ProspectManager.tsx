'use client'

import * as React from "react"
import { Button } from "@/components/shared/Button"
import { Badge } from "@/components/shared/Badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/shared/Avatar"
import {
  Building2,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Star,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  AlertCircle,
  Filter,
  Search,
  Plus,
  ExternalLink,
  MessageSquare,
  Video,
  UserPlus,
  MoreVertical
} from "lucide-react"
import { cn, formatTimestamp } from "@/lib/utils"
import { format, parseISO, isToday, isTomorrow, subDays, subWeeks } from "date-fns"

interface Prospect {
  id: string
  name: string
  avatar?: string
  email: string
  phone: string
  company?: string
  position?: string
  leadScore: number // 0-100
  lastContact: string
  status: 'hot' | 'warm' | 'cold' | 'qualified' | 'unqualified' | 'converted' | 'lost'
  source: string
  tags: string[]
  pipelineStage: 'new' | 'contacted' | 'qualified' | 'proposal' | 'negotiation' | 'closed-won' | 'closed-lost'
  assignedTo?: {
    name: string
    email: string
    id: string
  }
  nextAction?: {
    type: 'call' | 'email' | 'meeting' | 'follow-up'
    dueDate: string
    description?: string
  }
  notes?: string
  socialProfiles?: {
    linkedin?: string
    twitter?: string
    github?: string
  }
  customFields?: Record<string, any>
  createdAt: string
  updatedAt: string
  lastActivity?: {
    type: string
    description: string
    timestamp: string
  }
}

interface ProspectManagerProps {
  prospects: Prospect[]
  onCreateProspect?: (prospect: Partial<Prospect>) => void
  onUpdateProspect?: (id: string, updates: Partial<Prospect>) => void
  onDeleteProspect?: (id: string) => void
  onContactProspect?: (action: 'call' | 'email' | 'sms' | 'meeting', prospect: Prospect) => void
  onScheduleInterview?: (prospect: Prospect) => void
  onViewDetails?: (prospect: Prospect) => void
  className?: string
  compact?: boolean
}

type SortField = 'name' | 'leadScore' | 'lastContact' | 'createdAt' | 'status'
type SortDirection = 'asc' | 'desc'

export function ProspectManager({
  prospects,
  onCreateProspect,
  onUpdateProspect,
  onDeleteProspect,
  onContactProspect,
  onScheduleInterview,
  onViewDetails,
  className,
  compact = false
}: ProspectManagerProps) {
  const [searchQuery, setSearchQuery] = React.useState("")
  const [selectedStatus, setSelectedStatus] = React.useState<Prospect['status'] | 'all'>('all')
  const [selectedStage, setSelectedStage] = React.useState<Prospect['pipelineStage'] | 'all'>('all')
  const [sortField, setSortField] = React.useState<SortField>('leadScore')
  const [sortDirection, setSortDirection] = React.useState<SortDirection>('desc')
  const [selectedProspect, setSelectedProspect] = React.useState<Prospect | null>(null)

  // Filter prospects based on search and filters
  const filteredProspects = prospects.filter(prospect => {
    const matchesSearch =
      prospect.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      prospect.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      prospect.company?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      prospect.position?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      prospect.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))

    const matchesStatus = selectedStatus === 'all' || prospect.status === selectedStatus
    const matchesStage = selectedStage === 'all' || prospect.pipelineStage === selectedStage

    return matchesSearch && matchesStatus && matchesStage
  })

  // Sort prospects
  const sortedProspects = [...filteredProspects].sort((a, b) => {
    let aValue: any
    let bValue: any

    switch (sortField) {
      case 'name':
        aValue = a.name.toLowerCase()
        bValue = b.name.toLowerCase()
        break
      case 'leadScore':
        aValue = a.leadScore
        bValue = b.leadScore
        break
      case 'lastContact':
        aValue = new Date(a.lastContact).getTime()
        bValue = new Date(b.lastContact).getTime()
        break
      case 'createdAt':
        aValue = new Date(a.createdAt).getTime()
        bValue = new Date(b.createdAt).getTime()
        break
      case 'status':
        aValue = a.status
        bValue = b.status
        break
      default:
        return 0
    }

    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  const getStatusColor = (status: Prospect['status']) => {
    switch (status) {
      case 'hot': return 'destructive'
      case 'warm': return 'warning'
      case 'cold': return 'secondary'
      case 'qualified': return 'success'
      case 'unqualified': return 'secondary'
      case 'converted': return 'success'
      case 'lost': return 'destructive'
      default: return 'secondary'
    }
  }

  const getStageColor = (stage: Prospect['pipelineStage']) => {
    switch (stage) {
      case 'new': return 'secondary'
      case 'contacted': return 'default'
      case 'qualified': return 'warning'
      case 'proposal': return 'warning'
      case 'negotiation': return 'warning'
      case 'closed-won': return 'success'
      case 'closed-lost': return 'destructive'
      default: return 'secondary'
    }
  }

  const getLeadScoreIcon = (score: number) => {
    if (score >= 80) return <TrendingUp className="h-3 w-3 text-green-500" />
    if (score >= 60) return <TrendingUp className="h-3 w-3 text-yellow-500" />
    if (score >= 40) return <TrendingDown className="h-3 w-3 text-orange-500" />
    return <TrendingDown className="h-3 w-3 text-red-500" />
  }

  const getActivityStatus = (lastContact: string) => {
    const date = parseISO(lastContact)
    const now = new Date()

    if (isToday(date)) return { label: 'Today', color: 'success' }
    if (isTomorrow(date)) return { label: 'Tomorrow', color: 'warning' }
    if (date > subDays(now, 7)) return { label: 'This week', color: 'default' }
    if (date > subWeeks(now, 2)) return { label: '2 weeks ago', color: 'warning' }
    return { label: 'Stale', color: 'destructive' }
  }

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  if (compact) {
    return (
      <div className={cn("space-y-4", className)}>
        <div className="flex items-center justify-between">
          <h3 className="font-medium">Top Prospects</h3>
          {onCreateProspect && (
            <Button size="sm" variant="outline" onClick={() => onCreateProspect({})}>
              <Plus className="h-3 w-3 mr-1" />
              Add
            </Button>
          )}
        </div>

        <div className="space-y-2">
          {sortedProspects.slice(0, 5).map((prospect) => {
            const activityStatus = getActivityStatus(prospect.lastContact)

            return (
              <div
                key={prospect.id}
                className="p-3 border rounded-lg hover:shadow-sm transition-shadow cursor-pointer"
                onClick={() => onViewDetails?.(prospect)}
              >
                <div className="flex items-start gap-3">
                  <Avatar className="h-8 w-8 shrink-0">
                    <AvatarImage src={prospect.avatar} />
                    <AvatarFallback className="text-xs">
                      {prospect.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="font-medium text-sm truncate">{prospect.name}</h4>
                      <div className="flex items-center gap-1">
                        {getLeadScoreIcon(prospect.leadScore)}
                        <span className="text-xs font-medium text-primary">{prospect.leadScore}</span>
                      </div>
                    </div>

                    {prospect.company && (
                      <p className="text-xs text-muted-foreground truncate mt-1">{prospect.company}</p>
                    )}

                    <div className="flex items-center justify-between mt-2">
                      <Badge variant={getStatusColor(prospect.status)} className="text-xs px-1.5 py-0.5">
                        {prospect.status}
                      </Badge>
                      <Badge variant={activityStatus.color as any} className="text-xs px-1.5 py-0.5">
                        {activityStatus.label}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Prospect Manager</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {filteredProspects.length} of {prospects.length} prospects
          </p>
        </div>
        {onCreateProspect && (
          <Button onClick={() => onCreateProspect({})}>
            <Plus className="h-4 w-4 mr-2" />
            Add Prospect
          </Button>
        )}
      </div>

      {/* Filters and Search */}
      <div className="space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search prospects by name, email, company..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          />
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Status:</span>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value as any)}
              className="px-3 py-1 border border-input rounded text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="all">All Status</option>
              <option value="hot">Hot</option>
              <option value="warm">Warm</option>
              <option value="cold">Cold</option>
              <option value="qualified">Qualified</option>
              <option value="unqualified">Unqualified</option>
              <option value="converted">Converted</option>
              <option value="lost">Lost</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Stage:</span>
            <select
              value={selectedStage}
              onChange={(e) => setSelectedStage(e.target.value as any)}
              className="px-3 py-1 border border-input rounded text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="all">All Stages</option>
              <option value="new">New</option>
              <option value="contacted">Contacted</option>
              <option value="qualified">Qualified</option>
              <option value="proposal">Proposal</option>
              <option value="negotiation">Negotiation</option>
              <option value="closed-won">Closed Won</option>
              <option value="closed-lost">Closed Lost</option>
            </select>
          </div>
        </div>

        {/* Sort Controls */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Sort by:</span>
          {(['name', 'leadScore', 'lastContact', 'createdAt'] as SortField[]).map((field) => (
            <Button
              key={field}
              size="sm"
              variant={sortField === field ? 'default' : 'outline'}
              onClick={() => handleSort(field)}
              className="text-xs"
            >
              {field.replace(/([A-Z])/g, ' $1').toLowerCase()}
              {sortField === field && (
                <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
              )}
            </Button>
          ))}
        </div>
      </div>

      {/* Prospects Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {sortedProspects.map((prospect) => {
          const activityStatus = getActivityStatus(prospect.lastContact)

          return (
            <div key={prospect.id} className="p-4 border rounded-lg space-y-4 hover:shadow-md transition-shadow">
              {/* Prospect Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <Avatar className="h-10 w-10 shrink-0">
                    <AvatarImage src={prospect.avatar} />
                    <AvatarFallback>
                      {prospect.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>

                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold truncate">{prospect.name}</h3>
                    {prospect.position && (
                      <p className="text-sm text-muted-foreground truncate">{prospect.position}</p>
                    )}
                    {prospect.company && (
                      <div className="flex items-center gap-1 text-sm text-muted-foreground mt-1">
                        <Building2 className="h-3 w-3" />
                        <span className="truncate">{prospect.company}</span>
                      </div>
                    )}
                  </div>
                </div>

                <Button size="icon" variant="outline" className="h-8 w-8">
                  <MoreVertical className="h-3 w-3" />
                </Button>
              </div>

              {/* Lead Score and Status */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getLeadScoreIcon(prospect.leadScore)}
                  <span className="text-lg font-bold text-primary">{prospect.leadScore}</span>
                  <span className="text-sm text-muted-foreground">score</span>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant={getStatusColor(prospect.status)} className="text-xs px-2 py-1">
                    {prospect.status}
                  </Badge>
                  <Badge variant={getStageColor(prospect.pipelineStage)} className="text-xs px-2 py-1">
                    {prospect.pipelineStage}
                  </Badge>
                </div>
              </div>

              {/* Contact Info */}
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <Mail className="h-3 w-3 text-muted-foreground" />
                  <span className="truncate">{prospect.email}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Phone className="h-3 w-3 text-muted-foreground" />
                  <span>{prospect.phone}</span>
                </div>
              </div>

              {/* Activity Status */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Last contact:</span>
                <Badge variant={activityStatus.color as any} className="text-xs px-2 py-1">
                  {activityStatus.label}
                </Badge>
              </div>

              {/* Next Action */}
              {prospect.nextAction && (
                <div className="p-2 bg-muted rounded text-sm">
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    <span className="font-medium capitalize">{prospect.nextAction.type}</span>
                    <span className="text-muted-foreground">
                      due {format(parseISO(prospect.nextAction.dueDate), 'MMM d')}
                    </span>
                  </div>
                  {prospect.nextAction.description && (
                    <p className="text-muted-foreground">{prospect.nextAction.description}</p>
                  )}
                </div>
              )}

              {/* Tags */}
              {prospect.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {prospect.tags.slice(0, 3).map((tag, index) => (
                    <Badge key={index} variant="secondary" className="text-xs px-1.5 py-0.5">
                      {tag}
                    </Badge>
                  ))}
                  {prospect.tags.length > 3 && (
                    <span className="text-xs text-muted-foreground">+{prospect.tags.length - 3}</span>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center gap-1 pt-2 border-t">
                {onContactProspect && (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onContactProspect('call', prospect)}
                      className="flex-1"
                    >
                      <Phone className="h-3 w-3" />
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onContactProspect('email', prospect)}
                      className="flex-1"
                    >
                      <Mail className="h-3 w-3" />
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onContactProspect('sms', prospect)}
                      className="flex-1"
                    >
                      <MessageSquare className="h-3 w-3" />
                    </Button>
                  </>
                )}

                {onScheduleInterview && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onScheduleInterview(prospect)}
                    className="flex-1"
                  >
                    <Calendar className="h-3 w-3" />
                  </Button>
                )}

                {onViewDetails && (
                  <Button
                    size="sm"
                    onClick={() => onViewDetails(prospect)}
                    className="flex-1"
                  >
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Empty State */}
      {sortedProspects.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <UserPlus className="h-12 w-12 mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No prospects found</h3>
          <p className="text-sm mb-4">
            {searchQuery || selectedStatus !== 'all' || selectedStage !== 'all'
              ? 'Try adjusting your search or filters'
              : 'Start by adding your first prospect'
            }
          </p>
          {onCreateProspect && (
            <Button onClick={() => onCreateProspect({})}>
              <Plus className="h-4 w-4 mr-2" />
              Add Prospect
            </Button>
          )}
        </div>
      )}
    </div>
  )
}