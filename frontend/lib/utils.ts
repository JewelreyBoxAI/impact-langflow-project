// infrastructure/frontend/lib/utils.ts

import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function generateId() {
  return Math.random().toString(36).substring(2, 9)
}

// Add this function
export function formatTimestamp(timestamp: string | Date): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
  if (isNaN(date.getTime())) {
    return "Invalid Date";
  }
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// And add this function
export function truncateText(text: any, maxLength: number = 50): string {
  // Handle non-string values
  if (!text) {
    return '';
  }
  
  // Convert to string if it's not already
  const textStr = typeof text === 'string' ? text : String(text);
  
  if (textStr.length <= maxLength) {
    return textStr;
  }
  
  return textStr.substring(0, maxLength) + '...';
}