"use client"

import React from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

import { completeGoogleCalendarConnect } from '@/lib/api-client'

function GoogleCalendarCallbackContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const hasStartedRef = React.useRef(false)

  React.useEffect(() => {
    if (hasStartedRef.current) return
    hasStartedRef.current = true

    const code = searchParams.get('code')
    const state = searchParams.get('state')

    const run = async () => {
      if (!code || !state) {
        router.replace('/calendar?calendar_error=missing_params')
        return
      }
      try {
        await completeGoogleCalendarConnect(code, state)
        router.replace('/calendar?calendar_connected=true')
      } catch (error) {
        const message = error instanceof Error ? error.message : 'connect_failed'
        router.replace(`/calendar?calendar_error=${encodeURIComponent(message)}`)
      }
    }

    run()
  }, [router, searchParams])

  return <div className="min-h-screen flex items-center justify-center text-sm text-muted-foreground">Connecting Google Calendar...</div>
}

export default function GoogleCalendarCallbackPage() {
  return (
    <React.Suspense fallback={<div className="min-h-screen" />}>
      <GoogleCalendarCallbackContent />
    </React.Suspense>
  )
}
