"use client"

import React from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Plus, Check, RefreshCw, Calendar as CalendarIcon, Mail } from 'lucide-react'
import { cn } from "@/lib/utils"
import { getCalendarAccounts, getCalendarConflicts, resolveCalendarConflict, startGoogleCalendarConnect, syncCalendarAccounts, type ApiCalendarAccount, type ApiCalendarConflict } from "@/lib/api-client"

function CalendarPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const connectedParam = searchParams.get('calendar_connected')
  const errorParam = searchParams.get('calendar_error')
  const [isSyncing, setIsSyncing] = React.useState(false)
  const [accounts, setAccounts] = React.useState<ApiCalendarAccount[]>([])
  const [conflicts, setConflicts] = React.useState<ApiCalendarConflict[]>([])
  const [statusMessage, setStatusMessage] = React.useState<string | null>(null)
  const initializedRef = React.useRef(false)

  const loadCalendarData = React.useCallback(async () => {
    try {
      const [loadedAccounts, loadedConflicts] = await Promise.all([
        getCalendarAccounts(),
        getCalendarConflicts(new Date().toISOString().split('T')[0]),
      ])
      setAccounts(loadedAccounts)
      setConflicts(loadedConflicts)
    } catch (error) {
      console.error(error)
    }
  }, [])

  React.useEffect(() => {
    if (initializedRef.current) return
    initializedRef.current = true

    const initialize = async () => {
      try {
        if (connectedParam) {
          setStatusMessage('Google Calendar connected successfully.')
          router.replace('/calendar')
        } else if (errorParam) {
          const decoded = decodeURIComponent(errorParam)
          setStatusMessage(`Calendar connect failed: ${decoded}`)
          router.replace('/calendar')
        }
      } catch (error) {
        console.error(error)
      } finally {
        await loadCalendarData()
      }
    }

    initialize()
  }, [connectedParam, errorParam, loadCalendarData, router])

  React.useEffect(() => {
    if (accounts.length > 0 && statusMessage && !statusMessage.toLowerCase().includes('failed')) {
      setStatusMessage(null)
    }
  }, [accounts.length, statusMessage])

  const handleSync = async () => {
    setIsSyncing(true)
    try {
      await syncCalendarAccounts()
      await loadCalendarData()
    } catch (error) {
      console.error(error)
    } finally {
      setIsSyncing(false)
    }
  }

  const handleResolveConflict = async (conflictId: string) => {
    try {
      await resolveCalendarConflict(conflictId)
      await loadCalendarData()
    } catch (error) {
      console.error(error)
    }
  }

  const handleConnectGoogle = async () => {
    try {
      const payload = await startGoogleCalendarConnect()
      window.location.href = payload.redirect_url
    } catch (error) {
      console.error(error)
    }
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-headline font-bold">Calendar Integrations</h1>
          <p className="text-muted-foreground">Sync multiple accounts to prevent conflicts and automate scheduling.</p>
        </div>
        <Button onClick={handleSync} variant="outline" className="rounded-full" disabled={isSyncing}>
          <RefreshCw className={cn("mr-2 h-4 w-4", isSyncing && "animate-spin")} />
          {isSyncing ? "Syncing..." : "Sync All"}
        </Button>
      </header>

      {statusMessage && (
        <div className="text-sm rounded-lg border px-3 py-2 bg-slate-50 text-slate-700">
          {statusMessage}
        </div>
      )}

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {accounts.map((account) => (
          <div key={account.id} className="bg-white p-6 rounded-2xl border shadow-sm flex flex-col gap-4">
            <div className="flex justify-between items-start">
              <div className={cn("p-2.5 rounded-xl", account.status === 'connected' ? 'bg-primary/10' : 'bg-slate-100')}>
                <Mail className={cn("h-6 w-6", account.status === 'connected' ? 'text-primary' : 'text-slate-600')} />
              </div>
              {account.status === 'connected' ? (
                <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">Connected</Badge>
              ) : (
                <Badge variant="outline">Disconnected</Badge>
              )}
            </div>
            <div>
              <h3 className="font-headline font-semibold text-lg capitalize">{account.provider} Account</h3>
              <p className="text-sm text-muted-foreground">{account.email}</p>
            </div>
            <div className="pt-4 border-t flex justify-between items-center mt-auto">
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Check className="h-3 w-3 text-emerald-500" /> {account.last_synced_at ? 'Synced recently' : 'Not synced yet'}
              </span>
              <Button variant="ghost" size="sm" className="h-8 text-xs">Manage</Button>
            </div>
          </div>
        ))}

        <div className="bg-slate-50 border-2 border-dashed rounded-2xl flex flex-col items-center justify-center p-8 text-center gap-3">
          <div className="bg-white p-3 rounded-full border shadow-sm">
             <Plus className="h-6 w-6 text-slate-400" />
          </div>
          <div>
            <p className="font-semibold text-sm">Add New Calendar</p>
            <p className="text-xs text-muted-foreground">Connect Outlook or iCal</p>
          </div>
          <Button variant="ghost" size="sm" className="text-xs" onClick={handleConnectGoogle}>Connect Google</Button>
        </div>
      </section>

      <div className="bg-white p-8 rounded-2xl border shadow-sm space-y-6">
         <div className="flex items-center gap-3">
           <CalendarIcon className="h-6 w-6 text-primary" />
           <h2 className="text-xl font-headline font-bold">Upcoming Conflict Detection</h2>
         </div>
         
         <div className="space-y-4">
           {conflicts.map((conflict) => (
             <div key={conflict.id} className="p-4 bg-slate-50 rounded-xl border flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-bold">Conflict: {conflict.description}</p>
                  <p className="text-xs text-muted-foreground">Status: {conflict.status}</p>
                </div>
                <Button size="sm" className="text-xs" onClick={() => handleResolveConflict(conflict.id)}>Resolve Now</Button>
             </div>
           ))}

           {conflicts.length === 0 && (
             <div className="p-12 text-center text-muted-foreground">
               <div className="max-w-xs mx-auto space-y-2">
                  <p className="text-sm font-medium">No conflicts found for today</p>
                  <p className="text-xs">Sync your calendar after adding events to detect overlaps with your planned blocks.</p>
               </div>
             </div>
           )}
         </div>
      </div>
    </div>
  )
}

export default function CalendarPage() {
  return (
    <React.Suspense fallback={<div className="min-h-[40vh]" />}>
      <CalendarPageContent />
    </React.Suspense>
  )
}
