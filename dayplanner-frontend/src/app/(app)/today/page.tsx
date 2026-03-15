
"use client"

import React, { useState, useEffect } from 'react'
import { TimeBlockCard, type TimeBlock } from "@/components/planner/time-block-card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Sparkles, Plus, Calendar as CalendarIcon, ChevronRight, Zap } from 'lucide-react'
import { cn } from "@/lib/utils"
import { getLocalDateISO, getMe, getTodayPlan, startEveningCheckin, updatePlanBlock, type ApiPlan, type ApiPlanBlock } from "@/lib/api-client"

const FALLBACK_PLAN: TimeBlock[] = []

const toMinutes = (start: string, end: string): number => {
  const [startHour, startMinute] = start.split(':').map(Number)
  const [endHour, endMinute] = end.split(':').map(Number)
  return Math.max(15, endHour * 60 + endMinute - (startHour * 60 + startMinute))
}

const toUiType = (category: string): TimeBlock['type'] => {
  const value = category?.toLowerCase()
  if (value === 'meeting' || value === 'break' || value === 'personal' || value === 'class' || value === 'work') {
    return value
  }
  return 'other'
}

const mapApiBlockToTimeBlock = (block: ApiPlanBlock): TimeBlock => ({
  id: block.id,
  title: block.title,
  type: toUiType(block.category),
  start_time: block.start_time,
  end_time: block.end_time,
  duration_minutes: toMinutes(block.start_time, block.end_time),
  priority: block.priority,
  completed: block.completed,
})

export default function TodayPage() {
  const [blocks, setBlocks] = useState<TimeBlock[]>(FALLBACK_PLAN)
  const [planId, setPlanId] = useState<string | null>(null)
  const [fullName, setFullName] = useState('')
  const [planSummary, setPlanSummary] = useState('')
  const [isEveningCheckinLoading, setIsEveningCheckinLoading] = useState(false)
  const [eveningCheckinMessage, setEveningCheckinMessage] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)

  const todayString = getLocalDateISO()
  const formattedDate = new Intl.DateTimeFormat(undefined, {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date())

  const loadPlan = React.useCallback(async () => {
    try {
      const [plan, me]: [ApiPlan, Awaited<ReturnType<typeof getMe>>] = await Promise.all([
        getTodayPlan(todayString),
        getMe(),
      ])
      setPlanId(plan.id)
      setBlocks(plan.blocks.map(mapApiBlockToTimeBlock))
      setPlanSummary(plan.summary)
      setFullName(me.full_name)
    } catch (error) {
      console.error(error)
    }
  }, [todayString])

  useEffect(() => {
    setMounted(true)
    loadPlan()
  }, [loadPlan])

  useEffect(() => {
    const refreshToken = new URLSearchParams(window.location.search).get('refresh')
    if (refreshToken) {
      loadPlan()
    }
  }, [loadPlan])

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key === 'dp_today_refresh_at') {
        loadPlan()
      }
    }
    const onPlanRefresh = () => loadPlan()
    window.addEventListener('storage', onStorage)
    window.addEventListener('dp_today_refresh', onPlanRefresh)
    return () => {
      window.removeEventListener('storage', onStorage)
      window.removeEventListener('dp_today_refresh', onPlanRefresh)
    }
  }, [loadPlan])

  const toggleBlock = async (id: string) => {
    let targetCompleted = false
    setBlocks(prev => prev.map(b => {
      if (b.id === id) {
        targetCompleted = !b.completed
        return { ...b, completed: targetCompleted }
      }
      return b
    }))

    if (planId) {
      try {
        await updatePlanBlock(planId, id, targetCompleted)
      } catch (error) {
        console.error(error)
      }
    }
  }

  const completedCount = blocks.filter((b) => b.completed).length
  const progress = blocks.length > 0 ? (completedCount / blocks.length) * 100 : 0

  const handleStartEveningCheckin = async () => {
    if (!planId || isEveningCheckinLoading) return
    setIsEveningCheckinLoading(true)
    setEveningCheckinMessage(null)
    try {
      const response = await startEveningCheckin(planId)
      setEveningCheckinMessage(response.message)
      await loadPlan()
    } catch (error) {
      console.error(error)
      setEveningCheckinMessage('Unable to start evening check-in right now.')
    } finally {
      setIsEveningCheckinLoading(false)
    }
  }

  if (!mounted) return null

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-5xl mx-auto">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-[10px] font-bold uppercase tracking-wider">
            <CalendarIcon className="h-3 w-3" />
            <span>{formattedDate}</span>
          </div>
          <h1 className="text-4xl font-headline font-extrabold tracking-tight">Good morning{fullName ? `, ${fullName.split(' ')[0]}` : ''}.</h1>
          <p className="text-muted-foreground font-medium">
            {blocks.length > 0 ? `Your agent has prepared ${blocks.length} focus blocks for your day.` : 'Share your priorities in Chat to generate your day plan.'}
          </p>
        </div>
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Timeline */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-headline font-bold">Timeline Overview</h2>
            <div className="hidden sm:flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-indigo-500"></span> Work
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-teal-500"></span> Meeting
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Break
              </div>
            </div>
          </div>

          <div className="relative space-y-4 timeline-line">
            {blocks.map((block) => (
              <div key={block.id} className="relative z-10 pl-6 group">
                <div className={cn(
                  "absolute left-[-1px] top-[1.375rem] w-4 h-4 bg-background rounded-full border-2 border-slate-200 transition-all duration-300 flex items-center justify-center",
                  block.completed && "border-emerald-500 bg-emerald-50",
                  "group-hover:border-primary group-hover:scale-110"
                )}>
                   {block.completed && <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-in zoom-in duration-300"></div>}
                </div>
                <TimeBlockCard block={block} onToggle={toggleBlock} />
              </div>
            ))}
          </div>

          {/* Evening Check-in Banner */}
          <div className="mt-12 p-6 bg-amber-50 rounded-3xl border border-amber-100 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="bg-white p-3 rounded-2xl shadow-sm">
                <Zap className="h-6 w-6 text-amber-500 fill-current" />
              </div>
              <div>
                <p className="text-lg font-headline font-bold text-amber-900">Evening Check-in</p>
                <p className="text-sm font-medium text-amber-700/80">6:00 PM — Record your daily progress with DP.</p>
              </div>
            </div>
            <Button
              className="rounded-full bg-amber-500 hover:bg-amber-600 text-white font-bold px-6 shadow-lg shadow-amber-500/20"
              onClick={handleStartEveningCheckin}
              disabled={!planId || isEveningCheckinLoading}
            >
              Start <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
          {eveningCheckinMessage && (
            <p className="text-xs font-medium text-amber-800 mt-2">{eveningCheckinMessage}</p>
          )}
        </div>

        {/* Right Column: Stats & Insights */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm space-y-5">
            <h3 className="text-lg font-headline font-bold">Daily Completion</h3>
            <div className="space-y-3">
              <div className="flex justify-between text-sm font-bold">
                <span className="text-slate-500">Progress</span>
                <span className="text-primary">{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="h-2.5 bg-slate-100" />
            </div>
            <p className="text-xs font-medium text-muted-foreground leading-relaxed italic">
              {planSummary ? `"${planSummary}"` : 'No AI summary yet. Start in Chat to build your plan.'}
            </p>
          </div>

          <div className="bg-primary p-6 rounded-3xl text-primary-foreground shadow-xl shadow-primary/20 space-y-4 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2 blur-2xl"></div>
            <div className="flex items-center gap-2 relative z-10">
              <Sparkles className="h-5 w-5 fill-current" />
              <h3 className="font-headline font-bold">Proactive Nudge</h3>
            </div>
            <p className="text-sm leading-relaxed font-medium opacity-90 italic relative z-10">
              {blocks.length > 0
                ? 'Your current plan is active. Use checkboxes on timeline blocks to track progress and improve tomorrow\'s suggestions.'
                : 'No live nudge available yet. Generate a plan in Chat and suggestions will appear here.'}
            </p>
            <Button variant="secondary" size="sm" className="w-full font-bold rounded-xl bg-white text-primary hover:bg-slate-50 border-none shadow-md">
              View Timeline
            </Button>
          </div>

          <div className="bg-slate-50 p-6 rounded-3xl border border-slate-100 space-y-4">
             <h3 className="font-headline font-bold text-slate-900">Calendar Sync</h3>
             <div className="p-4 bg-white rounded-2xl border border-slate-100 flex items-start gap-3 shadow-sm">
               <div className="mt-0.5 p-1.5 bg-emerald-100 rounded-lg">
                 <CalendarIcon className="h-4 w-4 text-emerald-600" />
               </div>
               <div className="text-xs">
                 <p className="font-bold text-slate-900">Check calendar for live conflict status</p>
                 <p className="font-medium text-slate-500">Open Calendar tab to sync and detect overlaps.</p>
               </div>
             </div>
          </div>
        </div>
      </section>

      {/* Floating Action Button */}
      <Button 
        size="icon" 
        className="fixed bottom-20 right-6 md:bottom-8 md:right-8 h-14 w-14 rounded-2xl shadow-2xl shadow-primary/40 md:h-16 md:w-16 z-40 transition-transform active:scale-95"
      >
        <Plus className="h-8 w-8" />
      </Button>
    </div>
  )
}
