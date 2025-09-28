'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

export default function HomePage() {
  const router = useRouter()
  const [isRedirecting, setIsRedirecting] = useState(false)

  useEffect(() => {
    const handleRedirect = async () => {
      console.log('HomePage: Starting redirect to /agents/recruiting')
      setIsRedirecting(true)

      try {
        // Add a small delay to ensure the router is ready
        await new Promise(resolve => setTimeout(resolve, 100))
        router.push('/agents/recruiting')
        console.log('HomePage: Redirect initiated')
      } catch (error) {
        console.error('HomePage: Redirect failed:', error)

        // Fallback: Use window.location if router.push fails
        if (typeof window !== 'undefined') {
          console.log('HomePage: Using window.location fallback')
          window.location.href = '/agents/recruiting'
        }
      }
    }

    handleRedirect()
  }, [router])

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="h-12 w-12 mx-auto rounded-full bg-primary flex items-center justify-center">
          <div className="h-6 w-6 rounded-full bg-primary-foreground animate-pulse" />
        </div>
        <p className="text-muted-foreground">
          {isRedirecting ? 'Redirecting to Recruiting Agent...' : 'Loading...'}
        </p>
        <p className="text-xs text-muted-foreground">
          If you are not redirected automatically,
          <a
            href="/agents/recruiting"
            className="text-primary hover:underline ml-1"
          >
            click here
          </a>
        </p>
      </div>
    </div>
  )
}