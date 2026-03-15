"use client"

import React, { useEffect, useState } from 'react'
import { listNotifications, type ApiNotification } from '@/lib/api-client'
import { X, Moon, Sun } from 'lucide-react'
import { cn } from '@/lib/utils'

export function NotificationBanner() {
  const [notifications, setNotifications] = useState<ApiNotification[]>([])
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())

  useEffect(() => {
    const load = async () => {
      try {
        const all = await listNotifications()
        const recent = all.filter((notification) => {
          const age = Date.now() - new Date(notification.created_at).getTime()
          return notification.kind === 'engagement' && age < 24 * 60 * 60 * 1000 && !notification.is_read
        })
        setNotifications(recent.slice(0, 2))
      } catch {
      }
    }
    load()
  }, [])

  const visible = notifications.filter((notification) => !dismissed.has(notification.id))
  if (visible.length === 0) return null

  return (
    <div className="space-y-2 mb-4">
      {visible.map((notification) => {
        const isMorning = notification.message.toLowerCase().includes('morning')
        return (
          <div
            key={notification.id}
            className={cn(
              'flex items-start gap-3 p-4 rounded-2xl border relative',
              isMorning
                ? 'bg-amber-50 border-amber-200 text-amber-900'
                : 'bg-indigo-50 border-indigo-200 text-indigo-900'
            )}
          >
            <div className={cn('p-1.5 rounded-lg shrink-0', isMorning ? 'bg-amber-100' : 'bg-indigo-100')}>
              {isMorning ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </div>
            <p className="text-sm font-medium leading-relaxed flex-1">{notification.message}</p>
            <button
              onClick={() => setDismissed((prev) => new Set([...prev, notification.id]))}
              className="shrink-0 opacity-50 hover:opacity-100 transition-opacity"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
