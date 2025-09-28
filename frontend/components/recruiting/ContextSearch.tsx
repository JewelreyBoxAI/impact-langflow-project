'use client'

import * as React from "react"
import { Button } from "@/components/shared/Button"
import { Badge } from "@/components/shared/Badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/shared/Avatar"
import {
  Search,
  Database,
  FileText,
  MessageSquare,
  Clock,
  Star,
  Filter,
  RefreshCw,
  ExternalLink,
  Copy,
  Download,
  Brain,
  Zap,
  History
} from "lucide-react"
import { cn, formatTimestamp } from "@/lib/utils"
import { format, parseISO } from "date-fns"

// Context search result types
interface SearchResult {
  id: string
  type: 'conversation' | 'document' | 'prospect' | 'activity' | 'knowledge'
  title: string
  content: string
  snippet: string
  score: number // Similarity score 0-1
  metadata: {
    source: string
    timestamp: string
    author?: string
    tags?: string[]
    prospectId?: string
    prospectName?: string
    conversationId?: string
    documentPath?: string
    activityType?: string
  }
  embedding?: number[] // Vector embedding for debugging
}

interface ContextSource {
  id: string
  name: string
  type: 'faiss' | 'postgresql' | 'zoho' | 'conversations'
  status: 'online' | 'offline' | 'syncing' | 'error'
  lastSync?: string
  recordCount?: number
  description: string
}

interface SearchFilters {
  types: SearchResult['type'][]
  sources: string[]
  dateRange?: {
    from: string
    to: string
  }
  minScore?: number
  tags?: string[]
  prospectId?: string
}

interface ContextSearchProps {
  onSearchResults?: (results: SearchResult[]) => void
  onSelectResult?: (result: SearchResult) => void
  onUseContext?: (context: string) => void
  className?: string
  compact?: boolean
  autoSearch?: boolean
  placeholder?: string
}

export function ContextSearch({
  onSearchResults,
  onSelectResult,
  onUseContext,
  className,
  compact = false,
  autoSearch = false,
  placeholder = "Search conversations, prospects, documents..."
}: ContextSearchProps) {
  const [query, setQuery] = React.useState("")
  const [isSearching, setIsSearching] = React.useState(false)
  const [results, setResults] = React.useState<SearchResult[]>([])
  const [selectedResult, setSelectedResult] = React.useState<SearchResult | null>(null)
  const [filters, setFilters] = React.useState<SearchFilters>({
    types: ['conversation', 'document', 'prospect', 'activity'],
    sources: [],
    minScore: 0.3
  })
  const [showFilters, setShowFilters] = React.useState(false)
  const [searchHistory, setSearchHistory] = React.useState<string[]>([])

  // Mock context sources - TODO: Replace with real API data
  const contextSources: ContextSource[] = [
    {
      id: 'faiss_embeddings',
      name: 'FAISS Embeddings',
      type: 'faiss',
      status: 'online',
      lastSync: new Date().toISOString(),
      recordCount: 15420,
      description: 'Vector embeddings for semantic search'
    },
    {
      id: 'postgresql_data',
      name: 'PostgreSQL Database',
      type: 'postgresql',
      status: 'online',
      lastSync: new Date().toISOString(),
      recordCount: 8932,
      description: 'Structured data and relationships'
    },
    {
      id: 'zoho_crm',
      name: 'Zoho CRM',
      type: 'zoho',
      status: 'syncing',
      lastSync: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
      recordCount: 2156,
      description: 'Lead and contact information'
    },
    {
      id: 'conversations',
      name: 'Chat Conversations',
      type: 'conversations',
      status: 'online',
      lastSync: new Date().toISOString(),
      recordCount: 4823,
      description: 'Past conversation history'
    }
  ]

  // Perform semantic search
  const performSearch = React.useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([])
      return
    }

    setIsSearching(true)

    try {
      // TODO: Replace with real API call to backend search endpoint
      // This would call your FAISS + PostgreSQL search service
      const mockResults: SearchResult[] = [
        {
          id: '1',
          type: 'conversation',
          title: 'Discussion about React Developer Position',
          content: 'Conversation with Sarah Johnson regarding the senior React developer role...',
          snippet: 'Looking for someone with 5+ years React experience, TypeScript knowledge...',
          score: 0.89,
          metadata: {
            source: 'Chat Conversations',
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            author: 'Recruiter',
            conversationId: 'conv_123',
            prospectId: 'prospect_456',
            prospectName: 'Sarah Johnson',
            tags: ['react', 'typescript', 'senior']
          }
        },
        {
          id: '2',
          type: 'prospect',
          title: 'John Smith - Full Stack Developer',
          content: 'Experienced full-stack developer with React and Node.js expertise...',
          snippet: 'Full-stack developer with 6 years experience in React, Node.js, PostgreSQL...',
          score: 0.82,
          metadata: {
            source: 'Zoho CRM',
            timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
            prospectId: 'prospect_789',
            prospectName: 'John Smith',
            tags: ['fullstack', 'react', 'nodejs']
          }
        },
        {
          id: '3',
          type: 'document',
          title: 'React Developer Job Description Template',
          content: 'Template for React developer positions including requirements and responsibilities...',
          snippet: 'Requirements: 3+ years React, Redux experience, TypeScript preferred...',
          score: 0.76,
          metadata: {
            source: 'Knowledge Base',
            timestamp: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
            documentPath: '/templates/react-dev.md',
            tags: ['template', 'react', 'job-description']
          }
        },
        {
          id: '4',
          type: 'activity',
          title: 'Phone Interview with Mike Chen',
          content: 'Technical phone interview notes for product manager role...',
          snippet: 'Strong product sense, good technical background, 4 years at startup...',
          score: 0.71,
          metadata: {
            source: 'Activities',
            timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
            prospectId: 'prospect_101',
            prospectName: 'Mike Chen',
            activityType: 'interview',
            tags: ['interview', 'product-manager']
          }
        }
      ]

      // Filter results based on current filters
      const filteredResults = mockResults.filter(result => {
        if (!filters.types.includes(result.type)) return false
        if (filters.minScore && result.score < filters.minScore) return false
        if (filters.sources.length > 0 && !filters.sources.includes(result.metadata.source)) return false
        return true
      })

      setResults(filteredResults)
      onSearchResults?.(filteredResults)

      // Add to search history
      if (!searchHistory.includes(searchQuery)) {
        setSearchHistory(prev => [searchQuery, ...prev.slice(0, 4)])
      }

    } catch (error) {
      console.error('Search error:', error)
      setResults([])
    } finally {
      setIsSearching(false)
    }
  }, [filters, onSearchResults, searchHistory])

  // Auto-search with debounce
  React.useEffect(() => {
    if (!autoSearch) return

    const timeoutId = setTimeout(() => {
      if (query.length >= 3) {
        performSearch(query)
      } else {
        setResults([])
      }
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [query, autoSearch, performSearch])

  const handleSearch = () => {
    performSearch(query)
  }

  const handleResultSelect = (result: SearchResult) => {
    setSelectedResult(result)
    onSelectResult?.(result)
  }

  const handleUseContext = (result: SearchResult) => {
    const context = `${result.title}: ${result.content}`
    onUseContext?.(context)
  }

  const getResultIcon = (type: SearchResult['type']) => {
    switch (type) {
      case 'conversation': return <MessageSquare className="h-4 w-4" />
      case 'document': return <FileText className="h-4 w-4" />
      case 'prospect': return <Avatar className="h-4 w-4"><AvatarFallback className="text-xs">P</AvatarFallback></Avatar>
      case 'activity': return <Clock className="h-4 w-4" />
      case 'knowledge': return <Brain className="h-4 w-4" />
      default: return <Search className="h-4 w-4" />
    }
  }

  const getSourceStatus = (sourceId: string) => {
    const source = contextSources.find(s => s.id === sourceId)
    if (!source) return { status: 'offline', color: 'destructive' }

    switch (source.status) {
      case 'online': return { status: 'online', color: 'success' }
      case 'syncing': return { status: 'syncing', color: 'warning' }
      case 'error': return { status: 'error', color: 'destructive' }
      default: return { status: 'offline', color: 'secondary' }
    }
  }

  if (compact) {
    return (
      <div className={cn("space-y-3", className)}>
        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder={placeholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full pl-10 pr-12 py-2 text-sm border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          />
          <Button
            size="icon"
            variant="ghost"
            onClick={handleSearch}
            disabled={isSearching}
            className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8"
          >
            {isSearching ? (
              <RefreshCw className="h-3 w-3 animate-spin" />
            ) : (
              <Search className="h-3 w-3" />
            )}
          </Button>
        </div>

        {/* Quick Results */}
        {results.length > 0 && (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {results.slice(0, 3).map((result) => (
              <div
                key={result.id}
                className="p-2 border rounded cursor-pointer hover:bg-accent transition-colors"
                onClick={() => handleResultSelect(result)}
              >
                <div className="flex items-start gap-2">
                  {getResultIcon(result.type)}
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium truncate">{result.title}</h4>
                    <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                      {result.snippet}
                    </p>
                    <div className="flex items-center justify-between mt-2">
                      <Badge variant="secondary" className="text-xs px-1.5 py-0.5">
                        {result.type}
                      </Badge>
                      <span className="text-xs text-primary font-medium">
                        {Math.round(result.score * 100)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Context Search</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Search across conversations, prospects, and documents
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter className="h-4 w-4 mr-2" />
          Filters
        </Button>
      </div>

      {/* Data Sources Status */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {contextSources.map((source) => {
          const status = getSourceStatus(source.id)
          return (
            <div key={source.id} className="p-3 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-sm">{source.name}</h3>
                <Badge variant={status.color as any} className="text-xs px-1.5 py-0.5">
                  {status.status}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mb-2">{source.description}</p>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">
                  {source.recordCount?.toLocaleString()} records
                </span>
                {source.lastSync && (
                  <span className="text-muted-foreground">
                    {formatTimestamp(source.lastSync)}
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Search Input */}
      <div className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder={placeholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full pl-10 pr-20 py-3 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
            <Button
              size="sm"
              onClick={handleSearch}
              disabled={isSearching}
            >
              {isSearching ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Search History */}
        {searchHistory.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <History className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Recent:</span>
            {searchHistory.map((term, index) => (
              <Button
                key={index}
                size="sm"
                variant="outline"
                onClick={() => setQuery(term)}
                className="text-xs h-6 px-2"
              >
                {term}
              </Button>
            ))}
          </div>
        )}
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="p-4 border rounded-lg space-y-4">
          <h3 className="font-medium">Search Filters</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Result Types */}
            <div>
              <label className="text-sm font-medium mb-2 block">Result Types</label>
              <div className="space-y-2">
                {(['conversation', 'document', 'prospect', 'activity', 'knowledge'] as const).map((type) => (
                  <label key={type} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={filters.types.includes(type)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFilters(prev => ({ ...prev, types: [...prev.types, type] }))
                        } else {
                          setFilters(prev => ({ ...prev, types: prev.types.filter(t => t !== type) }))
                        }
                      }}
                      className="rounded"
                    />
                    <span className="capitalize">{type}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Minimum Score */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Minimum Relevance: {Math.round((filters.minScore || 0) * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={filters.minScore || 0}
                onChange={(e) => setFilters(prev => ({ ...prev, minScore: parseFloat(e.target.value) }))}
                className="w-full"
              />
            </div>

            {/* Sources */}
            <div>
              <label className="text-sm font-medium mb-2 block">Sources</label>
              <div className="space-y-2">
                {contextSources.map((source) => (
                  <label key={source.id} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={filters.sources.includes(source.name)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFilters(prev => ({ ...prev, sources: [...prev.sources, source.name] }))
                        } else {
                          setFilters(prev => ({ ...prev, sources: prev.sources.filter(s => s !== source.name) }))
                        }
                      }}
                      className="rounded"
                    />
                    <span>{source.name}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">
              Search Results ({results.length})
            </h3>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                <Brain className="h-3 w-3 mr-1" />
                Semantic Search
              </Badge>
              <Badge variant="outline" className="text-xs">
                <Zap className="h-3 w-3 mr-1" />
                FAISS + PostgreSQL
              </Badge>
            </div>
          </div>

          <div className="space-y-3">
            {results.map((result) => (
              <div
                key={result.id}
                className={cn(
                  "p-4 border rounded-lg cursor-pointer transition-all",
                  selectedResult?.id === result.id ? "border-primary bg-primary/5" : "hover:border-accent"
                )}
                onClick={() => handleResultSelect(result)}
              >
                <div className="space-y-3">
                  {/* Result Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      {getResultIcon(result.type)}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium truncate">{result.title}</h4>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="secondary" className="text-xs px-2 py-0.5">
                            {result.type}
                          </Badge>
                          <Badge variant="outline" className="text-xs px-2 py-0.5">
                            {result.metadata.source}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {formatTimestamp(result.metadata.timestamp)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant="default" className="text-xs px-2 py-1">
                        <Star className="h-3 w-3 mr-1" />
                        {Math.round(result.score * 100)}%
                      </Badge>
                    </div>
                  </div>

                  {/* Result Content */}
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {result.snippet}
                  </p>

                  {/* Result Metadata */}
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-4">
                      {result.metadata.prospectName && (
                        <span>
                          <strong>Prospect:</strong> {result.metadata.prospectName}
                        </span>
                      )}
                      {result.metadata.author && (
                        <span>
                          <strong>Author:</strong> {result.metadata.author}
                        </span>
                      )}
                      {result.metadata.activityType && (
                        <span>
                          <strong>Type:</strong> {result.metadata.activityType}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-1">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleUseContext(result)
                        }}
                        className="h-6 px-2 text-xs"
                      >
                        <Copy className="h-3 w-3 mr-1" />
                        Use
                      </Button>

                      {result.metadata.documentPath && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-6 px-2 text-xs"
                        >
                          <Download className="h-3 w-3" />
                        </Button>
                      )}

                      {result.metadata.conversationId && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-6 px-2 text-xs"
                        >
                          <ExternalLink className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Tags */}
                  {result.metadata.tags && result.metadata.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-2 border-t">
                      {result.metadata.tags.map((tag, index) => (
                        <Badge key={index} variant="outline" className="text-xs px-1.5 py-0.5">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {query && !isSearching && results.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <Search className="h-12 w-12 mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No results found</h3>
          <p className="text-sm">
            Try adjusting your search query or filters
          </p>
        </div>
      )}
    </div>
  )
}