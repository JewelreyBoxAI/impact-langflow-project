'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function HomePage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to recruiting agent as the main entry point
    router.replace('/agents/recruiting')
  }, [router])

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="h-12 w-12 mx-auto rounded-full bg-primary flex items-center justify-center">
          <div className="h-6 w-6 rounded-full bg-primary-foreground animate-pulse" />
        </div>
        <p className="text-muted-foreground">Redirecting to Impact LangFlow...</p>
      </div>
    </div>
  )
}