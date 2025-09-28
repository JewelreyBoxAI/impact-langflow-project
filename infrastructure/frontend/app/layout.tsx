import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from 'react-hot-toast'
import { AgentProvider } from '@/context/AgentContext'
import { SessionProvider } from '@/context/SessionContext'
import { MCPProvider } from '@/context/MCPContext'
import '@/styles/globals.css'

const inter = Inter({ subsets: ['latin'] })

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#1D4ED8' },
    { media: '(prefers-color-scheme: dark)', color: '#3B82F6' },
  ],
}

export const metadata: Metadata = {
  title: 'Impact LangFlow AI Platform',
  description: 'AI-powered recruiting and real estate automation platform',
  keywords: ['AI', 'recruiting', 'real estate', 'automation', 'LangFlow'],
  authors: [{ name: 'Impact AI Team' }],
  icons: {
    icon: [
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/favicon.ico', sizes: 'any' },
    ],
    apple: '/apple-touch-icon.png',
    other: [
      { rel: 'android-chrome-192x192', url: '/android-chrome-192x192.png' },
      { rel: 'android-chrome-512x512', url: '/android-chrome-512x512.png' },
    ],
  },
  manifest: '/site.webmanifest',
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body className={inter.className}>
        <MCPProvider
          autoConnect={true}
          healthMonitoringInterval={30000}
          enableNotifications={true}
        >
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
        </MCPProvider>
      </body>
    </html>
  )
}