'use client'

import * as React from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/shared/Avatar"
import { Badge } from "@/components/shared/Badge"
import { Button } from "@/components/shared/Button"
import {
  Building2,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Star,
  ExternalLink,
  MessageSquare,
  Video,
  Edit3,
  MoreVertical
} from "lucide-react"
import { cn, formatTimestamp } from "@/lib/utils"
import { format, parseISO, isToday, isTomorrow } from "date-fns"

// Zoho CRM data types
interface ZohoLead {
  id: string
  firstName: string
  lastName: string
  email: string
  phone?: string
  mobile?: string
  company?: string
  designation?: string
  leadSource: string
  leadStatus: string
  rating: 'Hot' | 'Warm' | 'Cold'
  leadScore?: number
  street?: string
  city?: string
  state?: string
  zipCode?: string
  country?: string
  website?: string
  industry?: string
  annualRevenue?: number
  employees?: number
  description?: string
  tags?: string[]
  createdTime: string
  modifiedTime: string
  owner: {
    name: string
    email: string
    id: string
  }
  customFields?: Record<string, any>
}

interface ZohoContact {
  id: string
  firstName: string
  lastName: string
  email: string
  phone?: string
  mobile?: string
  title?: string
  department?: string
  mailingStreet?: string
  mailingCity?: string
  mailingState?: string
  mailingZip?: string
  mailingCountry?: string
  accountName?: string
  leadSource?: string
  contactOwner: {
    name: string
    email: string
    id: string
  }
  createdTime: string
  modifiedTime: string
  tags?: string[]
  customFields?: Record<string, any>
}

interface ZohoAccount {
  id: string
  accountName: string
  website?: string
  phone?: string
  industry?: string
  type?: string
  annualRevenue?: number
  employees?: number
  billingStreet?: string
  billingCity?: string
  billingState?: string
  billingZip?: string
  billingCountry?: string
  description?: string
  accountOwner: {
    name: string
    email: string
    id: string
  }
  createdTime: string
  modifiedTime: string
  tags?: string[]
  customFields?: Record<string, any>
}

interface ZohoActivity {
  id: string
  subject: string
  activityType: 'Call' | 'Meeting' | 'Email' | 'Task' | 'Event'
  status: 'Not Started' | 'In Progress' | 'Completed' | 'Cancelled'
  priority: 'High' | 'Medium' | 'Low'
  dueDate?: string
  startDateTime?: string
  endDateTime?: string
  description?: string
  relatedTo: {
    module: 'Leads' | 'Contacts' | 'Accounts'
    id: string
    name: string
  }
  owner: {
    name: string
    email: string
    id: string
  }
  createdTime: string
  modifiedTime: string
}

interface ZohoProspectCardProps {
  type: 'lead' | 'contact' | 'account'
  data: ZohoLead | ZohoContact | ZohoAccount
  activities?: ZohoActivity[]
  onContactAction?: (action: 'call' | 'email' | 'sms' | 'meeting', data: any) => void
  onEdit?: () => void
  onViewDetails?: () => void
  className?: string
  compact?: boolean
}

export function ZohoProspectCard({
  type,
  data,
  activities = [],
  onContactAction,
  onEdit,
  onViewDetails,
  className,
  compact = false
}: ZohoProspectCardProps) {
  const [showFullDescription, setShowFullDescription] = React.useState(false)

  // Helper functions to get unified data
  const getName = () => {
    if (type === 'account') {
      return (data as ZohoAccount).accountName
    }
    const person = data as ZohoLead | ZohoContact
    return `${person.firstName} ${person.lastName}`
  }

  const getEmail = () => {
    return 'email' in data ? data.email : undefined
  }

  const getPhone = () => {
    if ('phone' in data) return data.phone
    if ('mobile' in data) return data.mobile
    return undefined
  }

  const getCompany = () => {
    if (type === 'account') return (data as ZohoAccount).accountName
    if (type === 'contact') return (data as ZohoContact).accountName
    if (type === 'lead') return (data as ZohoLead).company
    return undefined
  }

  const getLocation = () => {
    if (type === 'account') {
      const acc = data as ZohoAccount
      const parts = [acc.billingCity, acc.billingState, acc.billingCountry].filter(Boolean)
      return parts.join(', ')
    } else {
      const person = data as ZohoLead | ZohoContact
      if ('city' in person) {
        const parts = [person.city, person.state, person.country].filter(Boolean)
        return parts.join(', ')
      }
      if ('mailingCity' in person) {
        const parts = [person.mailingCity, person.mailingState, person.mailingCountry].filter(Boolean)
        return parts.join(', ')
      }
    }
    return undefined
  }

  const getLeadScore = () => {
    if (type === 'lead') {
      return (data as ZohoLead).leadScore
    }
    return undefined
  }

  const getRating = () => {
    if (type === 'lead') {
      return (data as ZohoLead).rating
    }
    return undefined
  }

  const getStatus = () => {
    if (type === 'lead') {
      return (data as ZohoLead).leadStatus
    }
    return undefined
  }

  const getOwner = () => {
    if (type === 'account') return (data as ZohoAccount).accountOwner
    if (type === 'contact') return (data as ZohoContact).contactOwner
    if (type === 'lead') return (data as ZohoLead).owner
    return undefined
  }

  const getDescription = () => {
    return 'description' in data ? data.description : undefined
  }

  const getRatingColor = (rating?: string) => {
    switch (rating?.toLowerCase()) {
      case 'hot': return 'destructive'
      case 'warm': return 'warning'
      case 'cold': return 'secondary'
      default: return 'secondary'
    }
  }

  const getActivityStatusColor = (status: string) => {
    switch (status) {
      case 'Completed': return 'success'
      case 'In Progress': return 'warning'
      case 'Cancelled': return 'destructive'
      default: return 'secondary'
    }
  }

  const upcomingActivities = activities
    .filter(activity =>
      activity.status !== 'Completed' &&
      activity.status !== 'Cancelled' &&
      activity.dueDate
    )
    .sort((a, b) => new Date(a.dueDate!).getTime() - new Date(b.dueDate!).getTime())
    .slice(0, 3)

  const formatActivityDate = (dateString: string) => {
    const date = parseISO(dateString)
    if (isToday(date)) {
      return `Today ${format(date, 'h:mm a')}`
    } else if (isTomorrow(date)) {
      return `Tomorrow ${format(date, 'h:mm a')}`
    } else {
      return format(date, 'MMM d, h:mm a')
    }
  }

  if (compact) {
    return (
      <div className={cn("p-3 border rounded-lg bg-card hover:shadow-sm transition-shadow", className)}>
        <div className="flex items-start gap-3">
          <Avatar className="h-8 w-8 shrink-0">
            <AvatarFallback className="text-xs">
              {getName().split(' ').map(n => n[0]).join('').slice(0, 2)}
            </AvatarFallback>
          </Avatar>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h4 className="font-medium text-sm truncate">{getName()}</h4>
              <div className="flex items-center gap-1">
                {getRating() && (
                  <Badge variant={getRatingColor(getRating())} className="text-xs px-1.5 py-0.5">
                    {getRating()}
                  </Badge>
                )}
                {getLeadScore() && (
                  <span className="text-xs font-medium text-primary">{getLeadScore()}</span>
                )}
              </div>
            </div>

            {getCompany() && (
              <p className="text-xs text-muted-foreground truncate mt-1">{getCompany()}</p>
            )}

            <div className="flex items-center justify-between mt-2">
              <span className="text-xs text-muted-foreground">
                {formatTimestamp(data.modifiedTime)}
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={onViewDetails}
                className="h-6 px-2 text-xs"
              >
                View
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("p-4 border rounded-lg bg-card space-y-4", className)}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <Avatar className="h-12 w-12 shrink-0">
            <AvatarFallback className="text-sm">
              {getName().split(' ').map(n => n[0]).join('').slice(0, 2)}
            </AvatarFallback>
          </Avatar>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold text-base truncate">{getName()}</h3>
              <Badge variant="outline" className="text-xs px-2 py-0.5">
                {type}
              </Badge>
            </div>

            {getCompany() && type !== 'account' && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                <Building2 className="h-3 w-3 shrink-0" />
                <span className="truncate">{getCompany()}</span>
              </div>
            )}

            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              {getEmail() && (
                <div className="flex items-center gap-1">
                  <Mail className="h-3 w-3" />
                  <span className="truncate">{getEmail()}</span>
                </div>
              )}
              {getPhone() && (
                <div className="flex items-center gap-1">
                  <Phone className="h-3 w-3" />
                  <span>{getPhone()}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {onEdit && (
            <Button size="icon" variant="outline" onClick={onEdit} className="h-8 w-8">
              <Edit3 className="h-3 w-3" />
            </Button>
          )}
          <Button size="icon" variant="outline" className="h-8 w-8">
            <MoreVertical className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Status and Score */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {getStatus() && (
            <Badge variant="outline" className="text-xs px-2 py-1">
              {getStatus()}
            </Badge>
          )}
          {getRating() && (
            <Badge variant={getRatingColor(getRating())} className="text-xs px-2 py-1">
              <Star className="h-3 w-3 mr-1" />
              {getRating()}
            </Badge>
          )}
          {data.tags && data.tags.length > 0 && (
            <div className="flex items-center gap-1">
              {data.tags.slice(0, 2).map((tag, index) => (
                <Badge key={index} variant="secondary" className="text-xs px-1.5 py-0.5">
                  {tag}
                </Badge>
              ))}
              {data.tags.length > 2 && (
                <span className="text-xs text-muted-foreground">+{data.tags.length - 2}</span>
              )}
            </div>
          )}
        </div>

        {getLeadScore() && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Score:</span>
            <span className="text-lg font-bold text-primary">{getLeadScore()}</span>
          </div>
        )}
      </div>

      {/* Location and Additional Info */}
      {(getLocation() || (type === 'account' && (data as ZohoAccount).website)) && (
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          {getLocation() && (
            <div className="flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              <span>{getLocation()}</span>
            </div>
          )}
          {type === 'account' && (data as ZohoAccount).website && (
            <div className="flex items-center gap-1">
              <ExternalLink className="h-3 w-3" />
              <a
                href={(data as ZohoAccount).website}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-primary transition-colors"
              >
                Website
              </a>
            </div>
          )}
        </div>
      )}

      {/* Description */}
      {getDescription() && (
        <div>
          <p className={cn(
            "text-sm text-muted-foreground",
            !showFullDescription && "line-clamp-2"
          )}>
            {getDescription()}
          </p>
          {getDescription()!.length > 150 && (
            <button
              onClick={() => setShowFullDescription(!showFullDescription)}
              className="text-xs text-primary hover:underline mt-1"
            >
              {showFullDescription ? 'Show less' : 'Show more'}
            </button>
          )}
        </div>
      )}

      {/* Upcoming Activities */}
      {upcomingActivities.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">Upcoming Activities</h4>
          <div className="space-y-2">
            {upcomingActivities.map((activity) => (
              <div key={activity.id} className="flex items-center justify-between text-sm p-2 bg-muted rounded">
                <div className="flex items-center gap-2">
                  <Calendar className="h-3 w-3 text-muted-foreground" />
                  <span className="font-medium">{activity.subject}</span>
                  <Badge variant={getActivityStatusColor(activity.status)} className="text-xs px-1.5 py-0.5">
                    {activity.activityType}
                  </Badge>
                </div>
                <span className="text-xs text-muted-foreground">
                  {formatActivityDate(activity.dueDate!)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center gap-2 pt-2 border-t">
        {onContactAction && getPhone() && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onContactAction('call', { phone: getPhone(), name: getName() })}
            className="flex-1"
          >
            <Phone className="h-4 w-4 mr-2" />
            Call
          </Button>
        )}

        {onContactAction && getEmail() && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onContactAction('email', { email: getEmail(), name: getName() })}
            className="flex-1"
          >
            <Mail className="h-4 w-4 mr-2" />
            Email
          </Button>
        )}

        {onContactAction && getPhone() && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onContactAction('sms', { phone: getPhone(), name: getName() })}
            className="flex-1"
          >
            <MessageSquare className="h-4 w-4 mr-2" />
            SMS
          </Button>
        )}

        {onContactAction && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onContactAction('meeting', { email: getEmail(), name: getName() })}
            className="flex-1"
          >
            <Video className="h-4 w-4 mr-2" />
            Meet
          </Button>
        )}

        {onViewDetails && (
          <Button
            size="sm"
            onClick={onViewDetails}
            className="flex-1"
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Details
          </Button>
        )}
      </div>

      {/* Owner Info */}
      {getOwner() && (
        <div className="text-xs text-muted-foreground pt-2 border-t">
          <span>Owner: {getOwner()!.name}</span>
          <span className="mx-2">•</span>
          <span>Modified: {formatTimestamp(data.modifiedTime)}</span>
        </div>
      )}
    </div>
  )
}