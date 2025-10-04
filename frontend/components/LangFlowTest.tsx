'use client'

/**
 * LangFlow Integration Test Component
 * Tests the LangFlow TypeScript client integration following Rick's guidelines
 */

import React, { useState } from 'react'
import { browserLangflowService, browserRecruitingService } from '@/lib/services/langflow-browser-client'
import type { FlowExecutionResponse } from '@/lib/services/langflow-browser-client'

interface StreamingEvent {
  event: string
  data: unknown
}

export default function LangFlowTest() {
  const [response, setResponse] = useState<FlowExecutionResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [streamingEvents, setStreamingEvents] = useState<StreamingEvent[]>([])
  const [health, setHealth] = useState<any>(null)

  const testHealthCheck = async () => {
    setLoading(true)
    setError(null)
    try {
      const healthResult = await browserLangflowService.healthCheck()
      setHealth(healthResult)
      console.log('LangFlow Health Check:', healthResult)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMsg)
      console.error('Health check failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const testFlowExecution = async () => {
    setLoading(true)
    setError(null)
    setResponse(null)
    try {
      const result = await browserLangflowService.executeFlow({
        flow_id: 'test-flow',
        input_value: 'Hello from frontend integration test!',
        input_type: 'chat',
        session_id: `test-session-${Date.now()}`,
      })
      setResponse(result)
      console.log('Flow execution result:', result)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMsg)
      console.error('Flow execution failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const testRecruitingFlow = async () => {
    setLoading(true)
    setError(null)
    setResponse(null)
    try {
      const result = await browserRecruitingService.executeRecruitingFlow({
        message: 'Test recruiting message from frontend',
        session_id: `recruiting-test-${Date.now()}`,
        prospects: [
          { name: 'Test Prospect', email: 'test@example.com', phone: '+1234567890' }
        ],
      })
      setResponse(result)
      console.log('Recruiting flow result:', result)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMsg)
      console.error('Recruiting flow failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const testStreamingFlow = async () => {
    setLoading(true)
    setError(null)
    setStreamingEvents([])
    try {
      const stream = browserRecruitingService.sendRecruitingMessageStream(
        'Test streaming message from frontend',
        `streaming-test-${Date.now()}`
      )

      for await (const event of stream) {
        setStreamingEvents(prev => [...prev, event])
        console.log('Streaming event:', event)
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMsg)
      console.error('Streaming failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const testAvailableFlows = async () => {
    setLoading(true)
    setError(null)
    try {
      const flows = await browserLangflowService.getAvailableFlows()
      console.log('Available flows:', flows)
      setError(null)
      alert(`Found ${flows.length} flows. Check console for details.`)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMsg)
      console.error('Get flows failed:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Recruiting Agent</h1>
      <p className="text-gray-600 mb-8">
        Testing TypeScript client integration with LangFlow backend following Rick's guidelines.
      </p>

      {/* Test Buttons */}
      <div className="grid grid-cols-2 gap-4 mb-8">
        <button
          onClick={testHealthCheck}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Testing...' : 'Test Health Check'}
        </button>

        <button
          onClick={testAvailableFlows}
          disabled={loading}
          className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
        >
          {loading ? 'Testing...' : 'Get Available Flows'}
        </button>

        <button
          onClick={testFlowExecution}
          disabled={loading}
          className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 disabled:opacity-50"
        >
          {loading ? 'Testing...' : 'Test Flow Execution'}
        </button>

        <button
          onClick={testRecruitingFlow}
          disabled={loading}
          className="bg-orange-600 text-white px-4 py-2 rounded-md hover:bg-orange-700 disabled:opacity-50"
        >
          {loading ? 'Testing...' : 'Test Recruiting Flow'}
        </button>
      </div>

      <button
        onClick={testStreamingFlow}
        disabled={loading}
        className="w-full bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50 mb-8"
      >
        {loading ? 'Testing...' : 'Test Streaming Flow'}
      </button>

      {/* Health Status */}
      {health && (
        <div className="bg-gray-100 p-4 rounded-md mb-6">
          <h3 className="font-semibold mb-2">Health Check Result:</h3>
          <pre className="text-sm overflow-auto max-h-64 max-w-full break-words">
            {JSON.stringify(health, null, 2)}
          </pre>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Response Display */}
      {response && (
        <div className="bg-green-100 p-4 rounded-md mb-6">
          <h3 className="font-semibold mb-2">Response:</h3>
          <pre className="text-sm overflow-auto max-h-64 max-w-full break-words">
            {JSON.stringify(response, null, 2)}
          </pre>
        </div>
      )}

      {/* Streaming Events */}
      {streamingEvents.length > 0 && (
        <div className="bg-blue-100 p-4 rounded-md">
          <h3 className="font-semibold mb-2">Streaming Events ({streamingEvents.length}):</h3>
          <div className="max-h-64 overflow-auto">
            {streamingEvents.map((event, index) => (
              <div key={index} className="border-b border-blue-200 py-2">
                <div className="text-sm font-medium">{event.event}</div>
                <pre className="text-xs text-gray-600 max-w-full break-words">
                  {JSON.stringify(event.data, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Configuration Info */}
      <div className="mt-8 p-4 bg-gray-50 rounded-md">
        <h3 className="font-semibold mb-2">Configuration:</h3>
        <ul className="text-sm text-gray-600">
          <li>LangFlow Base URL: {process.env.NEXT_PUBLIC_LANGFLOW_URL || 'http://localhost:7860'}</li>
          <li>API Key Configured: {process.env.NEXT_PUBLIC_LANGFLOW_API_KEY ? 'Yes' : 'No'}</li>
          <li>Backend API URL: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</li>
        </ul>
      </div>
    </div>
  )
}