'use client'

import * as React from "react"
import { Button } from "@/components/shared/Button"
import { Badge } from "@/components/shared/Badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/shared/Avatar"
import {
  Calendar,
  Clock,
  Phone,
  Video,
  MapPin,
  User,
  Mail,
  Plus,
  Edit3,
  Trash2,
  CheckCircle,
  XCircle,
  AlertCircle
} from "lucide-react"
import { cn, formatTimestamp } from "@/lib/utils"
import { format, parseISO, isToday, isTomorrow, isBefore, isAfter } from "date-fns"

interface Interview {
  id: string
  candidateName: string
  candidateEmail?: string
  candidatePhone?: string
  candidateAvatar?: string
  position: string
  scheduledTime: string
  type: 'phone' | 'video' | 'in-person'
  status: 'upcoming' | 'in-progress' | 'completed' | 'cancelled' | 'rescheduled'
  location?: string
  duration: number // minutes
  interviewerName: string
  interviewerEmail?: string
  notes?: string
  meetingLink?: string
  feedback?: {
    rating: number // 1-5
    notes: string
    recommendation: 'hire' | 'no-hire' | 'continue' | 'hold'
  }
  createdAt: string
  updatedAt: string
}

interface InterviewSchedulerProps {
  interviews: Interview[]
  onScheduleInterview?: (interview: Partial<Interview>) => void
  onUpdateInterview?: (id: string, updates: Partial<Interview>) => void
  onCancelInterview?: (id: string) => void
  onStartInterview?: (id: string) => void
  onCompleteInterview?: (id: string, feedback: Interview['feedback']) => void
  className?: string
  compact?: boolean
}

export function InterviewScheduler({
  interviews,
  onScheduleInterview,
  onUpdateInterview,
  onCancelInterview,
  onStartInterview,
  onCompleteInterview,
  className,
  compact = false
}: InterviewSchedulerProps) {
  const [selectedInterview, setSelectedInterview] = React.useState<Interview | null>(null)
  const [filter, setFilter] = React.useState<'all' | 'upcoming' | 'today' | 'completed'>('all')

  const now = new Date()

  // Filter interviews based on selected filter
  const filteredInterviews = interviews.filter(interview => {
    const interviewDate = parseISO(interview.scheduledTime)

    switch (filter) {
      case 'upcoming':
        return interview.status === 'upcoming' && isAfter(interviewDate, now)
      case 'today':
        return isToday(interviewDate)
      case 'completed':
        return interview.status === 'completed' || interview.status === 'cancelled'
      default:
        return true
    }
  })

  // Sort interviews by scheduled time
  const sortedInterviews = [...filteredInterviews].sort((a, b) =>
    new Date(a.scheduledTime).getTime() - new Date(b.scheduledTime).getTime()
  )

  const getStatusColor = (status: Interview['status']) => {
    switch (status) {
      case 'upcoming': return 'default'
      case 'in-progress': return 'warning'
      case 'completed': return 'success'
      case 'cancelled': return 'destructive'
      case 'rescheduled': return 'secondary'
      default: return 'secondary'
    }
  }

  const getStatusIcon = (status: Interview['status']) => {
    switch (status) {
      case 'upcoming': return <Clock className="h-3 w-3" />
      case 'in-progress': return <AlertCircle className="h-3 w-3" />
      case 'completed': return <CheckCircle className="h-3 w-3" />
      case 'cancelled': return <XCircle className="h-3 w-3" />
      case 'rescheduled': return <Calendar className="h-3 w-3" />
      default: return <Clock className="h-3 w-3" />
    }
  }

  const getInterviewTypeIcon = (type: Interview['type']) => {
    switch (type) {
      case 'phone': return <Phone className="h-4 w-4" />
      case 'video': return <Video className="h-4 w-4" />
      case 'in-person': return <MapPin className="h-4 w-4" />
      default: return <Calendar className="h-4 w-4" />
    }
  }

  const formatInterviewTime = (dateString: string) => {
    const date = parseISO(dateString)
    if (isToday(date)) {
      return `Today ${format(date, 'h:mm a')}`
    } else if (isTomorrow(date)) {
      return `Tomorrow ${format(date, 'h:mm a')}`
    } else {
      return format(date, 'MMM d, h:mm a')
    }
  }

  const getTimeStatus = (dateString: string, status: Interview['status']) => {
    const date = parseISO(dateString)
    const now = new Date()

    if (status === 'completed' || status === 'cancelled') {
      return null
    }

    if (isBefore(date, now)) {
      return { label: 'Overdue', variant: 'destructive' as const }
    }

    if (isToday(date)) {
      const hoursDiff = (date.getTime() - now.getTime()) / (1000 * 60 * 60)
      if (hoursDiff <= 1) {
        return { label: 'Starting Soon', variant: 'warning' as const }
      }
      return { label: 'Today', variant: 'default' as const }
    }

    return null
  }

  const canStartInterview = (interview: Interview) => {
    const interviewDate = parseISO(interview.scheduledTime)
    const now = new Date()
    const timeDiff = Math.abs(interviewDate.getTime() - now.getTime()) / (1000 * 60) // minutes

    return interview.status === 'upcoming' && timeDiff <= 15 // Can start 15 minutes before/after
  }

  if (compact) {
    return (
      <div className={cn("space-y-2", className)}>
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-sm">Interviews</h3>
          {onScheduleInterview && (
            <Button size="sm" variant="outline" onClick={() => onScheduleInterview({})}>
              <Plus className="h-3 w-3 mr-1" />
              Schedule
            </Button>
          )}
        </div>

        <div className="space-y-2">
          {sortedInterviews.slice(0, 3).map((interview) => {
            const timeStatus = getTimeStatus(interview.scheduledTime, interview.status)

            return (
              <div
                key={interview.id}
                className="p-3 border rounded-lg hover:shadow-sm transition-shadow cursor-pointer"
                onClick={() => setSelectedInterview(interview)}
              >
                <div className="flex items-start gap-3">
                  <Avatar className="h-8 w-8 shrink-0">
                    <AvatarImage src={interview.candidateAvatar} />
                    <AvatarFallback className="text-xs">
                      {interview.candidateName.split(' ').map(n => n[0]).join('').slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="font-medium text-sm truncate">{interview.candidateName}</h4>
                      <div className="flex items-center gap-1">
                        {getInterviewTypeIcon(interview.type)}
                        <Badge variant={getStatusColor(interview.status)} className="text-xs px-1.5 py-0.5">
                          {getStatusIcon(interview.status)}
                        </Badge>
                      </div>
                    </div>

                    <p className="text-xs text-muted-foreground truncate mt-1">{interview.position}</p>

                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs font-medium">{formatInterviewTime(interview.scheduledTime)}</span>
                      {timeStatus && (
                        <Badge variant={timeStatus.variant} className="text-xs px-1.5 py-0.5">
                          {timeStatus.label}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}

          {sortedInterviews.length === 0 && (
            <div className="text-center py-6 text-muted-foreground">
              <Calendar className="h-8 w-8 mx-auto mb-2" />
              <p className="text-sm">No interviews scheduled</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Interview Scheduler</h2>
        {onScheduleInterview && (
          <Button onClick={() => onScheduleInterview({})}>
            <Plus className="h-4 w-4 mr-2" />
            Schedule Interview
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        {(['all', 'upcoming', 'today', 'completed'] as const).map((filterOption) => (
          <Button
            key={filterOption}
            size="sm"
            variant={filter === filterOption ? 'default' : 'outline'}
            onClick={() => setFilter(filterOption)}
          >
            {filterOption.charAt(0).toUpperCase() + filterOption.slice(1)}
          </Button>
        ))}
      </div>

      {/* Interview List */}
      <div className="space-y-3">
        {sortedInterviews.map((interview) => {
          const timeStatus = getTimeStatus(interview.scheduledTime, interview.status)

          return (
            <div key={interview.id} className="p-4 border rounded-lg space-y-4">
              {/* Interview Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <Avatar className="h-12 w-12 shrink-0">
                    <AvatarImage src={interview.candidateAvatar} />
                    <AvatarFallback>
                      {interview.candidateName.split(' ').map(n => n[0]).join('').slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold truncate">{interview.candidateName}</h3>
                      <Badge variant={getStatusColor(interview.status)} className="text-xs px-2 py-0.5">
                        {getStatusIcon(interview.status)}
                        <span className="ml-1">{interview.status}</span>
                      </Badge>
                      {timeStatus && (
                        <Badge variant={timeStatus.variant} className="text-xs px-2 py-0.5">
                          {timeStatus.label}
                        </Badge>
                      )}
                    </div>

                    <div className="text-sm text-muted-foreground space-y-1">
                      <div className="flex items-center gap-4">
                        <span className="font-medium">{interview.position}</span>
                        <span>•</span>
                        <span>{interview.duration} minutes</span>
                      </div>

                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-1">
                          {getInterviewTypeIcon(interview.type)}
                          <span className="capitalize">{interview.type}</span>
                        </div>
                        <span>•</span>
                        <span className="font-medium">{formatInterviewTime(interview.scheduledTime)}</span>
                      </div>

                      <div className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        <span>with {interview.interviewerName}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-1 shrink-0">
                  {canStartInterview(interview) && onStartInterview && (
                    <Button
                      size="sm"
                      onClick={() => onStartInterview(interview.id)}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      Start
                    </Button>
                  )}

                  {interview.status === 'upcoming' && onUpdateInterview && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onUpdateInterview(interview.id, {})}
                    >
                      <Edit3 className="h-3 w-3" />
                    </Button>
                  )}

                  {interview.status === 'upcoming' && onCancelInterview && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onCancelInterview(interview.id)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </div>

              {/* Interview Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                {/* Contact Info */}
                <div className="space-y-2">
                  {interview.candidateEmail && (
                    <div className="flex items-center gap-2">
                      <Mail className="h-3 w-3 text-muted-foreground" />
                      <span>{interview.candidateEmail}</span>
                    </div>
                  )}

                  {interview.candidatePhone && (
                    <div className="flex items-center gap-2">
                      <Phone className="h-3 w-3 text-muted-foreground" />
                      <span>{interview.candidatePhone}</span>
                    </div>
                  )}

                  {interview.location && interview.type === 'in-person' && (
                    <div className="flex items-center gap-2">
                      <MapPin className="h-3 w-3 text-muted-foreground" />
                      <span>{interview.location}</span>
                    </div>
                  )}

                  {interview.meetingLink && interview.type === 'video' && (
                    <div className="flex items-center gap-2">
                      <Video className="h-3 w-3 text-muted-foreground" />
                      <a
                        href={interview.meetingLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        Join Meeting
                      </a>
                    </div>
                  )}
                </div>

                {/* Additional Info */}
                <div className="space-y-2">
                  <div>
                    <span className="text-muted-foreground">Interviewer:</span>
                    <span className="ml-2">{interview.interviewerName}</span>
                  </div>

                  <div>
                    <span className="text-muted-foreground">Created:</span>
                    <span className="ml-2">{formatTimestamp(interview.createdAt)}</span>
                  </div>

                  {interview.updatedAt !== interview.createdAt && (
                    <div>
                      <span className="text-muted-foreground">Updated:</span>
                      <span className="ml-2">{formatTimestamp(interview.updatedAt)}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Notes */}
              {interview.notes && (
                <div className="border-t pt-3">
                  <div className="text-sm">
                    <span className="font-medium text-muted-foreground">Notes:</span>
                    <p className="mt-1">{interview.notes}</p>
                  </div>
                </div>
              )}

              {/* Feedback */}
              {interview.feedback && (
                <div className="border-t pt-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium">Interview Feedback</h4>
                    <div className="flex items-center gap-1">
                      <span className="text-sm text-muted-foreground">Rating:</span>
                      <span className="font-medium">{interview.feedback.rating}/5</span>
                    </div>
                  </div>

                  <div className="text-sm">
                    <Badge
                      variant={
                        interview.feedback.recommendation === 'hire' ? 'success' :
                        interview.feedback.recommendation === 'no-hire' ? 'destructive' :
                        interview.feedback.recommendation === 'continue' ? 'warning' : 'secondary'
                      }
                      className="mb-2"
                    >
                      {interview.feedback.recommendation.replace('-', ' ').toUpperCase()}
                    </Badge>
                    <p>{interview.feedback.notes}</p>
                  </div>
                </div>
              )}
            </div>
          )
        })}

        {sortedInterviews.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <Calendar className="h-12 w-12 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No interviews found</h3>
            <p className="text-sm">
              {filter === 'all'
                ? 'No interviews scheduled yet'
                : `No ${filter} interviews found`
              }
            </p>
          </div>
        )}
      </div>
    </div>
  )
}