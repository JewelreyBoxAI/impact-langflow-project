'use client'

import * as React from "react"
import Link from "next/link"
import { Button } from "@/components/shared/Button"
import { ThemeToggle } from "@/components/shared/ThemeToggle"
import { Badge } from "@/components/shared/Badge"
import { Settings, ArrowLeft, Users, Shield, Database } from "lucide-react"

export default function AdminPage() {
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
              <div className="h-10 w-10 rounded-full bg-red-600 flex items-center justify-center text-white">
                <Settings className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-xl font-semibold">Admin Agent</h1>
                <p className="text-sm text-muted-foreground">System Administration and Configuration</p>
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
            <div className="h-24 w-24 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
              <Settings className="h-12 w-12 text-red-600" />
            </div>
          </div>

          {/* Title and Description */}
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2">
              <h2 className="text-3xl font-bold">Admin Agent</h2>
              <Badge variant="warning" className="ml-2">
                Coming Soon
              </Badge>
            </div>
            <p className="text-xl text-muted-foreground">
              Intelligent system administration, user management, and platform configuration assistance.
            </p>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-2 gap-6 text-left">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-red-600" />
                <h3 className="font-semibold">User Management</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Automated user provisioning, role assignment, and access control management.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Shield className="h-5 w-5 text-red-600" />
                <h3 className="font-semibold">Security Management</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Intelligent security monitoring, compliance checking, and vulnerability management.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Database className="h-5 w-5 text-red-600" />
                <h3 className="font-semibold">System Configuration</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Automated system setup, configuration management, and optimization recommendations.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Settings className="h-5 w-5 text-red-600" />
                <h3 className="font-semibold">Platform Administration</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Comprehensive platform management with intelligent troubleshooting and maintenance.
              </p>
            </div>
          </div>

          {/* CTA */}
          <div className="pt-8">
            <p className="text-muted-foreground mb-4">
              This powerful admin agent is under development. Start with our recruiting agent today!
            </p>
            <Link href="/agents/recruiting">
              <Button size="lg" className="bg-red-600 hover:bg-red-700">
                Try Recruiting Agent
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}