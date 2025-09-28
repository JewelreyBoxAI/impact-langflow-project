'use client'

/**
 * Simple reload button client component
 */
export default function ReloadButton() {
  return (
    <button
      onClick={() => window.location.reload()}
      className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
    >
      Reload Application
    </button>
  )
}