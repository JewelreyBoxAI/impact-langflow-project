'use client'

import * as React from "react"
import Link from "next/link"
import { Button } from "@/components/shared/Button"
import { ThemeToggle } from "@/components/shared/ThemeToggle"
import { Badge } from "@/components/shared/Badge"
import { BarChart3, ArrowLeft, Workflow, Zap, TrendingUp } from "lucide-react"

export default function OperationsPage() {
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
              <div className="h-10 w-10 rounded-full bg-emerald-600 flex items-center justify-center text-white">
                <BarChart3 className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-xl font-semibold">Operations Agent</h1>
                <p className="text-sm text-muted-foreground">Workflow Automation and Analytics</p>
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
            <div className="h-24 w-24 rounded-full bg-emerald-100 dark:bg-emerald-900/20 flex items-center justify-center">
              <BarChart3 className="h-12 w-12 text-emerald-600" />
            </div>
          </div>

          {/* Title and Description */}
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2">
              <h2 className="text-3xl font-bold">Operations Agent</h2>
              <Badge variant="warning" className="ml-2">
                Coming Soon
              </Badge>
            </div>
            <p className="text-xl text-muted-foreground">
              Intelligent workflow automation, process optimization, and operational analytics for real estate teams.
            </p>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-2 gap-6 text-left">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Workflow className="h-5 w-5 text-emerald-600" />
                <h3 className="font-semibold">Workflow Automation</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Automate repetitive tasks, streamline processes, and create intelligent workflow orchestration.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <TrendingUp className="h-5 w-5 text-emerald-600" />
                <h3 className="font-semibold">Performance Analytics</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Real-time operational metrics, performance insights, and data-driven optimization recommendations.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Zap className="h-5 w-5 text-emerald-600" />
                <h3 className="font-semibold">Process Optimization</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Intelligent process analysis and optimization suggestions to improve efficiency and outcomes.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <BarChart3 className="h-5 w-5 text-emerald-600" />
                <h3 className="font-semibold">Business Intelligence</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Advanced analytics, reporting, and predictive insights for strategic decision making.
              </p>
            </div>
          </div>

          {/* CTA */}
          <div className="pt-8">
            <p className="text-muted-foreground mb-4">
              This operations agent is coming soon. Get started with our recruiting agent now!
            </p>
            <Link href="/agents/recruiting">
              <Button size="lg" className="bg-emerald-600 hover:bg-emerald-700">
                Try Recruiting Agent
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}