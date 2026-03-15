
"use client"

import React from 'react'
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { Clock, MoreHorizontal } from 'lucide-react'

export interface TimeBlock {
  id: string
  title: string
  type: 'work' | 'meeting' | 'break' | 'personal' | 'class' | 'other'
  start_time: string
  end_time: string
  duration_minutes: number
  priority: 'high' | 'medium' | 'low'
  agent_note?: string
  completed: boolean
}

interface TimeBlockCardProps {
  block: TimeBlock
  onToggle: (id: string) => void
}

const typeStyles = {
  work: "border-indigo-600 bg-indigo-50/50 text-indigo-900",
  meeting: "border-teal-600 bg-teal-50/50 text-teal-900",
  break: "border-emerald-600 bg-emerald-50/50 text-emerald-900",
  personal: "border-amber-600 bg-amber-50/50 text-amber-900",
  class: "border-blue-600 bg-blue-50/50 text-blue-900",
  other: "border-slate-600 bg-slate-50/50 text-slate-900",
}

export function TimeBlockCard({ block, onToggle }: TimeBlockCardProps) {
  return (
    <div className={cn(
      "relative group flex flex-col gap-2 p-4 rounded-2xl border-l-4 transition-all duration-300 hover:shadow-lg hover:shadow-slate-200/50 bg-white border border-slate-100",
      typeStyles[block.type as keyof typeof typeStyles] || typeStyles.other,
      block.completed && "opacity-60 grayscale-[0.2]"
    )}>
      <div className="flex justify-between items-start">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center flex-wrap gap-2">
            <h3 className={cn(
              "font-headline font-bold text-base leading-tight tracking-tight",
              block.completed && "line-through text-slate-400"
            )}>
              {block.title}
            </h3>
            <Badge variant="outline" className="capitalize text-[10px] h-5 px-2 py-0 font-bold border-current opacity-70">
              {block.type}
            </Badge>
          </div>
          <div className="flex items-center gap-3 text-[11px] font-bold opacity-60">
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{block.start_time} - {block.end_time}</span>
            </div>
            <span className="h-1 w-1 rounded-full bg-current opacity-30"></span>
            <div className="px-1.5 py-0.5 rounded-full bg-current/10">
              {block.duration_minutes}m
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Checkbox 
            checked={block.completed} 
            onCheckedChange={() => onToggle(block.id)}
            className="h-6 w-6 rounded-full border-current data-[state=checked]:bg-primary data-[state=checked]:border-primary transition-all duration-300"
          />
        </div>
      </div>

      {block.agent_note && (
        <p className="text-xs italic text-muted-foreground mt-1 flex items-center gap-1">
          <span>💡</span> {block.agent_note}
        </p>
      )}
    </div>
  )
}
