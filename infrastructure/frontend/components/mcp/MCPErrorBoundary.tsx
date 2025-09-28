/**
 * MCP Error Boundary
 * Catches and handles MCP-related errors gracefully
 */

'use client'

import * as React from 'react'
import { Button } from '@/components/shared/Button'
import { AlertTriangle, RefreshCw, ExternalLink } from 'lucide-react'
import type { MCPError, MCPConnectionError, MCPTimeoutError, ZohoAuthError } from '@/lib/types/mcp'

interface ErrorInfo {
  componentStack: string
}

interface MCPErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  retryCount: number
}

interface MCPErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{
    error: Error
    errorInfo: ErrorInfo
    onRetry: () => void
    retryCount: number
  }>
  maxRetries?: number
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

export class MCPErrorBoundary extends React.Component<MCPErrorBoundaryProps, MCPErrorBoundaryState> {
  private retryTimeoutId: NodeJS.Timeout | null = null

  constructor(props: MCPErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    }
  }

  static getDerivedStateFromError(error: Error): Partial<MCPErrorBoundaryState> {
    return {
      hasError: true,
      error
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      errorInfo
    })

    // Call onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // Log error details
    console.error('MCP Error Boundary caught an error:', error, errorInfo)
  }

  componentWillUnmount() {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId)
    }
  }

  handleRetry = () => {
    const { maxRetries = 3 } = this.props
    const { retryCount } = this.state

    if (retryCount >= maxRetries) {
      console.warn('Max retry attempts reached')
      return
    }

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: retryCount + 1
    })

    // Add exponential backoff for retries
    const delay = Math.min(1000 * Math.pow(2, retryCount), 10000)
    this.retryTimeoutId = setTimeout(() => {
      // Force re-render of children
      this.forceUpdate()
    }, delay)
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    })
  }

  render() {
    const { hasError, error, errorInfo, retryCount } = this.state
    const { children, fallback: FallbackComponent, maxRetries = 3 } = this.props

    if (hasError && error) {
      // Use custom fallback if provided
      if (FallbackComponent) {
        return (
          <FallbackComponent
            error={error}
            errorInfo={errorInfo!}
            onRetry={this.handleRetry}
            retryCount={retryCount}
          />
        )
      }

      // Default error UI
      return (
        <MCPErrorFallback
          error={error}
          errorInfo={errorInfo!}
          onRetry={this.handleRetry}
          onReset={this.handleReset}
          retryCount={retryCount}
          maxRetries={maxRetries}
        />
      )
    }

    return children
  }
}

interface MCPErrorFallbackProps {
  error: Error
  errorInfo: ErrorInfo
  onRetry: () => void
  onReset: () => void
  retryCount: number
  maxRetries: number
}

const MCPErrorFallback: React.FC<MCPErrorFallbackProps> = ({
  error,
  errorInfo,
  onRetry,
  onReset,
  retryCount,
  maxRetries
}) => {
  const [showDetails, setShowDetails] = React.useState(false)

  const getErrorIcon = () => {
    if (error instanceof MCPConnectionError || error instanceof MCPTimeoutError) {
      return <RefreshCw className="h-8 w-8 text-yellow-500" />
    }
    return <AlertTriangle className="h-8 w-8 text-red-500" />
  }

  const getErrorTitle = () => {
    if (error instanceof MCPConnectionError) {
      return 'Connection Error'
    }
    if (error instanceof MCPTimeoutError) {
      return 'Request Timeout'
    }
    if (error instanceof ZohoAuthError) {
      return 'Authentication Error'
    }
    if (error instanceof MCPError) {
      return 'MCP Server Error'
    }
    return 'Unexpected Error'
  }

  const getErrorDescription = () => {
    if (error instanceof MCPConnectionError) {
      return 'Unable to connect to the MCP server. Please check your network connection and server status.'
    }
    if (error instanceof MCPTimeoutError) {
      return 'The request to the MCP server timed out. The server may be overloaded or experiencing issues.'
    }
    if (error instanceof ZohoAuthError) {
      return 'There was an issue with Zoho authentication. You may need to re-authenticate or refresh your token.'
    }
    if (error instanceof MCPError) {
      return error.message || 'An error occurred while communicating with the MCP server.'
    }
    return 'An unexpected error occurred. Please try refreshing the page or contact support if the issue persists.'
  }

  const getRecoveryActions = () => {
    const actions = []

    if (retryCount < maxRetries) {
      actions.push(
        <Button key="retry" onClick={onRetry} variant="default">
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry ({maxRetries - retryCount} attempts left)
        </Button>
      )
    }

    actions.push(
      <Button key="reset" onClick={onReset} variant="outline">
        Reset Component
      </Button>
    )

    if (error instanceof ZohoAuthError) {
      actions.push(
        <Button key="auth" variant="outline" asChild>
          <a href="https://accounts.zoho.com/home" target="_blank" rel="noopener noreferrer">
            <ExternalLink className="h-4 w-4 mr-2" />
            Zoho Console
          </a>
        </Button>
      )
    }

    return actions
  }

  return (
    <div className="rounded-lg border border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950 p-6">
      <div className="flex items-start gap-4">
        {getErrorIcon()}
        <div className="flex-1 space-y-4">
          <div>
            <h3 className="font-semibold text-lg text-red-800 dark:text-red-200">
              {getErrorTitle()}
            </h3>
            <p className="text-sm text-red-600 dark:text-red-300 mt-1">
              {getErrorDescription()}
            </p>
          </div>

          {/* Error Details */}
          <div className="space-y-2">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-sm text-red-600 dark:text-red-300 hover:text-red-800 dark:hover:text-red-200 underline"
            >
              {showDetails ? 'Hide' : 'Show'} technical details
            </button>

            {showDetails && (
              <div className="space-y-3">
                <div className="rounded-md bg-red-100 dark:bg-red-900 p-3">
                  <div className="text-xs font-medium text-red-800 dark:text-red-200 mb-2">
                    Error Message:
                  </div>
                  <div className="text-xs text-red-700 dark:text-red-300 font-mono">
                    {error.message}
                  </div>
                </div>

                {error instanceof MCPError && error.details && (
                  <div className="rounded-md bg-red-100 dark:bg-red-900 p-3">
                    <div className="text-xs font-medium text-red-800 dark:text-red-200 mb-2">
                      Error Details:
                    </div>
                    <pre className="text-xs text-red-700 dark:text-red-300 font-mono whitespace-pre-wrap">
                      {JSON.stringify(error.details, null, 2)}
                    </pre>
                  </div>
                )}

                <div className="rounded-md bg-red-100 dark:bg-red-900 p-3">
                  <div className="text-xs font-medium text-red-800 dark:text-red-200 mb-2">
                    Component Stack:
                  </div>
                  <pre className="text-xs text-red-700 dark:text-red-300 font-mono whitespace-pre-wrap max-h-32 overflow-y-auto">
                    {errorInfo.componentStack}
                  </pre>
                </div>

                {error.stack && (
                  <div className="rounded-md bg-red-100 dark:bg-red-900 p-3">
                    <div className="text-xs font-medium text-red-800 dark:text-red-200 mb-2">
                      Stack Trace:
                    </div>
                    <pre className="text-xs text-red-700 dark:text-red-300 font-mono whitespace-pre-wrap max-h-32 overflow-y-auto">
                      {error.stack}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Recovery Actions */}
          <div className="flex flex-wrap gap-2">
            {getRecoveryActions()}
          </div>

          {/* Retry Information */}
          {retryCount > 0 && (
            <div className="text-xs text-red-600 dark:text-red-300">
              Previous retry attempts: {retryCount}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * Hook for handling MCP errors with automatic retry logic
 */
export const useMCPErrorHandler = (maxRetries = 3, retryDelay = 1000) => {
  const [retryCount, setRetryCount] = React.useState(0)
  const [isRetrying, setIsRetrying] = React.useState(false)

  const handleError = React.useCallback(async (
    error: Error,
    retryFunction: () => Promise<any>
  ): Promise<any> => {
    // Check if error is retryable
    const isRetryable = (
      error instanceof MCPConnectionError ||
      error instanceof MCPTimeoutError ||
      (error instanceof MCPError && error.statusCode && error.statusCode >= 500)
    )

    if (!isRetryable || retryCount >= maxRetries) {
      throw error
    }

    setIsRetrying(true)
    setRetryCount(prev => prev + 1)

    // Exponential backoff
    const delay = Math.min(retryDelay * Math.pow(2, retryCount), 10000)
    await new Promise(resolve => setTimeout(resolve, delay))

    try {
      const result = await retryFunction()
      setRetryCount(0) // Reset on success
      return result
    } catch (retryError) {
      return handleError(retryError, retryFunction)
    } finally {
      setIsRetrying(false)
    }
  }, [retryCount, maxRetries, retryDelay])

  const reset = React.useCallback(() => {
    setRetryCount(0)
    setIsRetrying(false)
  }, [])

  return {
    handleError,
    retryCount,
    isRetrying,
    reset,
    canRetry: retryCount < maxRetries
  }
}