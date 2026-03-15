
"use client"

import React, { useState, useRef, useEffect } from 'react'
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, Sparkles, LayoutDashboard, Calendar, ChevronRight, FileText } from 'lucide-react'
import { cn } from "@/lib/utils"
import { toast } from "@/hooks/use-toast"
import { createChatSession, getLocalDateISO, sendChatMessage } from "@/lib/api-client"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  type?: 'text' | 'plan-preview'
  data?: any
}

const QUICK_REPLIES = [
  "Continue yesterday",
  "Add a task",
  "I have a meeting",
  "Plan my workout",
  "Review goals"
]

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hey there! I'm your Day Planner AI. Tell me about your day—what's on your mind? What do you need to get done?",
      type: 'text'
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const markdownFileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    let ignore = false
    const bootstrapSession = async () => {
      try {
        const session = await createChatSession()
        if (!ignore) setSessionId(session.session_id)
      } catch (error) {
        console.error(error)
      }
    }
    bootstrapSession()
    return () => {
      ignore = true
    }
  }, [])

  const handleSend = async (customInput?: string) => {
    const textToSend = customInput || input
    if (!textToSend.trim() || isLoading) return

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: textToSend,
      type: 'text'
    }

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    try {
      let activeSessionId = sessionId
      if (!activeSessionId) {
        const session = await createChatSession()
        activeSessionId = session.session_id
        setSessionId(activeSessionId)
      }

      const response = await sendChatMessage(activeSessionId, textToSend, getLocalDateISO())
      localStorage.setItem('dp_today_refresh_at', String(Date.now()))
      window.dispatchEvent(new CustomEvent('dp_today_refresh'))

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.assistant_reply || response.summary,
        type: 'text'
      }

      setMessages(prev => [...prev, assistantMsg])

      // If we got blocks, show a plan preview
      if (response.blocks && response.blocks.length > 0) {
        const firstItems = response.blocks.slice(0, 3).map((item) => item.title).join(', ')
        if (response.summary?.trim()) {
          toast({
            title: 'Today plan updated',
            description: `${response.summary} Tasks: ${firstItems}${response.blocks.length > 3 ? ', ...' : ''}`,
          })
        }

        setMessages(prev => [...prev, {
          id: (Date.now() + 2).toString(),
          role: 'assistant',
          content: "I've structured your timeline based on that.",
          type: 'plan-preview',
          data: response.blocks
        }])
      }
      
    } catch (error) {
      console.error(error)
      setMessages(prev => [...prev, {
        id: 'error',
        role: 'assistant',
        content: "I'm sorry, I hit a snag while planning. Can you try rephrasing?",
        type: 'text'
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleMarkdownFilePick = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    try {
      const content = await file.text()
      if (!content.trim()) {
        return
      }
      setInput(content)
      toast({
        title: 'Markdown imported',
        description: `${file.name} loaded into the chat composer.`,
      })
    } catch (error) {
      console.error(error)
      toast({
        title: 'Import failed',
        description: 'Could not read markdown file.',
      })
    } finally {
      event.target.value = ''
    }
  }

  useEffect(() => {
    if (scrollRef.current) {
      const scrollContainer = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [messages, isLoading])

  return (
    <div className="flex flex-col h-[calc(100vh-14rem)] md:h-[calc(100vh-12rem)] w-full border rounded-3xl bg-white shadow-xl shadow-slate-200/50 overflow-hidden relative">
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-6 pb-4">
          {messages.map((m) => (
            <div key={m.id} className={cn(
              "flex gap-3",
              m.role === 'user' ? "flex-row-reverse" : "flex-row"
            )}>
              {m.role === 'assistant' && (
                <Avatar className="h-8 w-8 bg-primary shadow-md shadow-primary/20 shrink-0">
                  <AvatarFallback className="bg-primary text-white">
                    <Sparkles className="h-4 w-4" />
                  </AvatarFallback>
                </Avatar>
              )}
              
              <div className={cn(
                "max-w-[85%] space-y-2",
                m.role === 'user' ? "items-end" : "items-start"
              )}>
                {m.type === 'text' && (
                  <div className={cn(
                    "p-4 rounded-2xl text-sm font-medium leading-relaxed shadow-sm",
                    m.role === 'user' 
                      ? "bg-primary text-white rounded-tr-none" 
                      : "bg-slate-100 text-slate-900 rounded-tl-none"
                  )}>
                    {m.role === 'assistant' ? (
                      <div className="prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-pre:my-1">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                      </div>
                    ) : (
                      m.content
                    )}
                  </div>
                )}

                {m.type === 'plan-preview' && (
                  <div className="bg-white border-2 border-slate-100 rounded-2xl p-4 shadow-lg w-full min-w-[280px] animate-in zoom-in-95 duration-300">
                    <div className="flex items-center gap-2 mb-3">
                      <LayoutDashboard className="h-4 w-4 text-primary" />
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Proposed Plan</span>
                    </div>
                    <div className="space-y-2">
                      {m.data.slice(0, 3).map((block: any, i: number) => (
                        <div key={i} className="flex items-center justify-between text-[11px] p-2 bg-slate-50 rounded-lg">
                          <span className="font-bold truncate max-w-[120px]">{block.title}</span>
                          <span className="text-slate-500 font-bold">{block.start_time}</span>
                        </div>
                      ))}
                      {m.data.length > 3 && (
                        <div className="text-[10px] text-center font-bold text-slate-400">+{m.data.length - 3} more blocks</div>
                      )}
                    </div>
                    <Button variant="outline" className="w-full mt-4 h-9 rounded-xl text-xs font-bold group" asChild>
                      <a href={`/today?refresh=${Date.now()}`}>
                        Open in Today <ChevronRight className="ml-1 h-3 w-3 transition-transform group-hover:translate-x-0.5" />
                      </a>
                    </Button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3 animate-in fade-in duration-300">
              <Avatar className="h-8 w-8 bg-primary shadow-md shadow-primary/20 shrink-0 animate-pulse">
                <AvatarFallback className="bg-primary text-white">
                  <Sparkles className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <div className="bg-slate-100 p-4 rounded-2xl rounded-tl-none shadow-sm flex gap-1.5 items-center">
                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce duration-700"></span>
                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce duration-700 delay-150"></span>
                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce duration-700 delay-300"></span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="p-4 border-t bg-slate-50/50 backdrop-blur-sm">
        <input
          ref={markdownFileInputRef}
          type="file"
          accept=".md,text/markdown"
          className="hidden"
          onChange={handleMarkdownFilePick}
        />
        <div className="flex flex-wrap gap-2 mb-3">
          {QUICK_REPLIES.map((reply) => (
            <button 
              key={reply}
              onClick={() => handleSend(reply)}
              disabled={isLoading}
              className="text-[10px] font-bold px-3 py-1.5 rounded-full bg-white border border-slate-200 hover:border-primary hover:text-primary transition-all duration-200 shadow-sm active:scale-95"
            >
              {reply}
            </button>
          ))}
          <button
            onClick={() => markdownFileInputRef.current?.click()}
            disabled={isLoading}
            className="text-[10px] font-bold px-3 py-1.5 rounded-full bg-white border border-slate-200 hover:border-primary hover:text-primary transition-all duration-200 shadow-sm active:scale-95 inline-flex items-center gap-1"
          >
            <FileText className="h-3 w-3" /> Import .md
          </button>
        </div>
        <div className="flex gap-2 relative">
          <Textarea 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder="Tell DP about your day..."
            className="min-h-[56px] py-3 rounded-2xl resize-none bg-white border-slate-200 focus-visible:ring-primary shadow-sm pr-12"
          />
          <Button 
            size="icon" 
            className="absolute right-2 bottom-2 h-10 w-10 rounded-xl shadow-lg shadow-primary/20 transition-transform active:scale-90" 
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
