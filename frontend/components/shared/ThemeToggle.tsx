'use client'

import * as React from "react"
import { Moon, Sun } from "lucide-react"
import { Button } from "./Button"
import { useTheme } from "@/hooks/useTheme"

export function ThemeToggle() {
  const { theme, toggleTheme, isHydrated } = useTheme()

  // Prevent hydration mismatch by not showing dynamic title until hydrated
  const title = isHydrated ? `Switch to ${theme === 'light' ? 'dark' : 'light'} mode` : 'Toggle theme'

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={toggleTheme}
      className="transition-all duration-200"
      title={title}
    >
      <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}