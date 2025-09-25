'use client'

import * as React from "react"
import Link from "next/link"
import { Button } from "@/components/shared/Button"
import { ThemeToggle } from "@/components/shared/ThemeToggle"
import { Badge } from "@/components/shared/Badge"
import { UserCheck, ArrowLeft, Clock, Settings } from "lucide-react"

export default function SupervisorPage() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/agents/recruiting">
              <Button variant="outline" size="icon">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-purple-600 flex items-center justify-center text-white">
                <UserCheck className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-xl font-semibold">Supervisor Agent</h1>
                <p className="text-sm text-muted-foreground">AI Oversight and Analytics</p>
              </div>
            </div>
          </div>
          <ThemeToggle />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto text-center space-y-8">
          {/* Icon */}
          <div className="flex justify-center">
            <div className="h-24 w-24 rounded-full bg-purple-100 dark:bg-purple-900/20 flex items-center justify-center">
              <UserCheck className="h-12 w-12 text-purple-600" />
            </div>
          </div>

          {/* Title and Description */}
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2">
              <h2 className="text-3xl font-bold">Supervisor Agent</h2>
              <Badge variant="warning" className="ml-2">
                Coming Soon
              </Badge>
            </div>
            <p className="text-xl text-muted-foreground">
              Advanced AI oversight, analytics, and performance monitoring for your real estate operations.
            </p>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-2 gap-6 text-left">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Settings className="h-5 w-5 text-purple-600" />
                <h3 className="font-semibold">Performance Analytics</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Monitor agent performance, conversation quality, and success metrics across all interactions.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Clock className="h-5 w-5 text-purple-600" />
                <h3 className="font-semibold">Real-time Oversight</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Live monitoring of agent conversations with intelligent escalation and intervention capabilities.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <UserCheck className="h-5 w-5 text-purple-600" />
                <h3 className="font-semibold">Quality Assurance</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Automated quality scoring and recommendations for improving agent interactions.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Settings className="h-5 w-5 text-purple-600" />
                <h3 className="font-semibold">Configuration Management</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Centralized control over agent settings, workflows, and business rules.
              </p>
            </div>
          </div>

          {/* CTA */}
          <div className="pt-8">
            <p className="text-muted-foreground mb-4">
              This advanced agent is currently in development. Experience our recruiting agent while you wait!
            </p>
            <Link href="/agents/recruiting">
              <Button size="lg" className="bg-purple-600 hover:bg-purple-700">
                Try Recruiting Agent
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}