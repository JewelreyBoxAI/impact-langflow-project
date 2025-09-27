import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from 'react-hot-toast'
import { AgentProvider } from '@/context/AgentContext'
import { SessionProvider } from '@/context/SessionContext'
import '@/styles/globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Impact LangFlow AI Platform',
  description: 'AI-powered recruiting and real estate automation platform',
  keywords: ['AI', 'recruiting', 'real estate', 'automation', 'LangFlow'],
  authors: [{ name: 'Impact AI Team' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#1D4ED8' },
    { media: '(prefers-color-scheme: dark)', color: '#3B82F6' },
  ],
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body className={inter.className}>
        <AgentProvider>
          <SessionProvider>
            {children}
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: 'hsl(var(--background))',
                  color: 'hsl(var(--foreground))',
                  border: '1px solid hsl(var(--border))',
                },
                success: {
                  iconTheme: {
                    primary: '#10b981',
                    secondary: '#ffffff',
                  },
                },
                error: {
                  iconTheme: {
                    primary: '#ef4444',
                    secondary: '#ffffff',
                  },
                },
              }}
            />
          </SessionProvider>
        </AgentProvider>
      </body>
    </html>
  )
}