
"use client"

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Calendar, TrendingUp, Award, CheckCircle2 } from 'lucide-react'
import { getArchivedPlans, getHistorySummary, getWeeklyPerformance, type ApiArchivedPlan, type ApiHistorySummary } from "@/lib/api-client"

type ChartPoint = { day: string; rate: number; color: string }

export default function HistoryPage() {
  const [summary, setSummary] = React.useState<ApiHistorySummary>({ completion_rate: 0, streak_days: 0, memory_patterns_count: 0 })
  const [stats, setStats] = React.useState<ChartPoint[]>([])
  const [plans, setPlans] = React.useState<ApiArchivedPlan[]>([])

  React.useEffect(() => {
    const loadHistory = async () => {
      try {
        const [summaryData, weeklyData, plansData] = await Promise.all([
          getHistorySummary('7d'),
          getWeeklyPerformance(),
          getArchivedPlans(),
        ])

        setSummary(summaryData)
        setStats(
          weeklyData.map((item) => ({
            day: item.day,
            rate: item.completion,
            color: item.completion >= 70 ? 'hsl(var(--primary))' : 'hsl(var(--muted-foreground))',
          }))
        )
        setPlans(plansData)
      } catch (error) {
        console.error(error)
      }
    }
    loadHistory()
  }, [])

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header>
        <h1 className="text-3xl font-headline font-bold">Performance History</h1>
        <p className="text-muted-foreground">Analyze your planning habits and celebrate your wins.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">7-Day Completion</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.completion_rate}%</div>
            <p className="text-xs text-muted-foreground mt-1 text-emerald-600 font-medium">Based on your recent tracked blocks</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Streak</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.streak_days} Days</div>
            <p className="text-xs text-muted-foreground mt-1">Current completion streak</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Memory Context</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.memory_patterns_count} Patterns</div>
            <p className="text-xs text-muted-foreground mt-1">AI memory patterns inferred from usage</p>
          </CardContent>
        </Card>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-8">
           <h2 className="text-xl font-headline font-bold">Weekly Performance</h2>
           <Badge variant="outline">Past 7 Days</Badge>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={stats}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
              <XAxis dataKey="day" axisLine={false} tickLine={false} fontSize={12} dy={10} />
              <YAxis hide />
              <Tooltip 
                cursor={{ fill: 'transparent' }} 
                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
              />
              <Bar dataKey="rate" radius={[4, 4, 0, 0]}>
                {stats.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="space-y-4">
        <h2 className="text-xl font-headline font-bold">Past Daily Plans</h2>
        <div className="space-y-3">
          {plans.length === 0 && (
            <div className="bg-white p-6 rounded-xl border text-sm text-muted-foreground">
              No history yet. Generate and complete blocks in Today to see your past plans here.
            </div>
          )}
          {plans.map((plan) => (
            <div key={plan.id} className="bg-white p-4 rounded-xl border flex items-center justify-between hover:bg-slate-50 transition-colors cursor-pointer group">
              <div className="flex items-center gap-4">
                <div className="bg-slate-100 p-2.5 rounded-lg group-hover:bg-primary/10 transition-colors">
                  <Calendar className="h-5 w-5 text-slate-500 group-hover:text-primary transition-colors" />
                </div>
                <div>
                  <p className="font-bold text-sm">{plan.date}</p>
                  <p className="text-xs text-muted-foreground">{plan.tasks_planned} tasks planned</p>
                </div>
              </div>
              <div className="flex items-center gap-6">
                 <div className="hidden sm:block w-32 space-y-1">
                    <div className="flex justify-between text-[10px] font-bold">
                       <span>COMPLETED</span>
                       <span>{plan.completion_rate}%</span>
                    </div>
                    <Progress value={plan.completion_rate} className="h-1.5" />
                 </div>
                 <Badge variant="secondary" className="text-[10px] px-2">ARCHIVED</Badge>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
