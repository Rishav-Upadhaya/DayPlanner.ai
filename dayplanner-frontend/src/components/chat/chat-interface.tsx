"use client"

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Send, Sparkles, LayoutDashboard, ChevronRight, FileText, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import { toast } from '@/hooks/use-toast'
import { useRouter } from 'next/navigation'
import {
  createChatSession,
  forceSavePlan,
  getLocalDateISO,
  getSessionMessages,
  listChatSessions,
  sendMessageStream,
  type ApiPlanBlock,
} from '@/lib/api-client'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const STORAGE_KEY = 'dp_chat_session_id'
const WELCOME_MESSAGE_ID = 'welcome-static'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  type?: 'text' | 'plan-pending-approval'
  planMeta?: { blocks: ApiPlanBlock[]; summary: string }
}

const WELCOME: Message = {
  id: WELCOME_MESSAGE_ID,
  role: 'assistant',
  content:
    "Hey there! I'm your **Day Planner AI**. Tell me about your day — what do you need to get done today? I'll read your calendar and build a personalised schedule.",
  type: 'text',
}

const QUICK_REPLIES = [
  "Continue yesterday's tasks",
  'Add a meeting',
  'Plan a stress-free day',
  'Review my goals',
  'I just finished a task',
]

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([WELCOME])
  const [pastSessions, setPastSessions] = useState<Array<{ id: string; title: string; created_at: string }>>([])
  const [showSessions, setShowSessions] = useState(false)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [pendingPlan, setPendingPlan] = useState<{ blocks: ApiPlanBlock[]; summary: string; sessionId: string } | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)
  const markdownFileInputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()

  useEffect(() => {
    if (scrollRef.current) {
      const scrollContainer = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        ;(scrollContainer as HTMLDivElement).scrollTop = (scrollContainer as HTMLDivElement).scrollHeight
      }
    }
  }, [messages, isLoading])

  useEffect(() => {
    const init = async () => {
      const savedSessionId = localStorage.getItem(STORAGE_KEY)
      if (savedSessionId) {
        try {
          const previousMessages = await getSessionMessages(savedSessionId)
          if (previousMessages.length > 0) {
            const restored: Message[] = previousMessages.map((message) => ({
              id: message.id,
              role: message.role as 'user' | 'assistant',
              content: message.content,
              type: 'text',
            }))
            setMessages(restored)
            setSessionId(savedSessionId)
            return
          }
        } catch {
          localStorage.removeItem(STORAGE_KEY)
        }
      }

      try {
        const session = await createChatSession()
        setSessionId(session.session_id)
        localStorage.setItem(STORAGE_KEY, session.session_id)
      } catch (error) {
        console.error('Failed to create session', error)
      }
    }

    init()
  }, [])

  const loadPastSessions = useCallback(async () => {
    try {
      const sessions = await listChatSessions()
      setPastSessions(sessions.slice(0, 20))
    } catch (error) {
      console.error(error)
    }
  }, [])

  const resumeSession = async (id: string) => {
    try {
      const restoredMessages = await getSessionMessages(id)
      const restored: Message[] = restoredMessages.map((message) => ({
        id: message.id,
        role: message.role as 'user' | 'assistant',
        content: message.content,
        type: 'text',
      }))
      setMessages(restored.length > 0 ? restored : [WELCOME])
      setSessionId(id)
      localStorage.setItem(STORAGE_KEY, id)
      setShowSessions(false)
      setPendingPlan(null)
    } catch {
      toast({ title: 'Could not load session', variant: 'destructive' })
    }
  }

  const startNewSession = async () => {
    abortRef.current?.abort()
    try {
      const session = await createChatSession()
      setSessionId(session.session_id)
      localStorage.setItem(STORAGE_KEY, session.session_id)
      setMessages([WELCOME])
      setPendingPlan(null)
      setShowSessions(false)
    } catch {
      toast({ title: 'Could not create session', variant: 'destructive' })
    }
  }

  const handleSend = async (customInput?: string) => {
    const textToSend = (customInput ?? input).trim()
    if (!textToSend || isLoading) return

    abortRef.current?.abort()
    abortRef.current = new AbortController()

    const userMsgId = `user-${Date.now()}`
    const assistantMsgId = `assistant-${Date.now() + 1}`

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: 'user', content: textToSend, type: 'text' },
      { id: assistantMsgId, role: 'assistant', content: '', type: 'text' },
    ])
    setInput('')
    setIsLoading(true)

    let activeSessionId = sessionId
    if (!activeSessionId) {
      const session = await createChatSession()
      activeSessionId = session.session_id
      setSessionId(activeSessionId)
      localStorage.setItem(STORAGE_KEY, activeSessionId)
    }

    try {
      await sendMessageStream(
        activeSessionId,
        textToSend,
        getLocalDateISO(),
        (token) => {
          setMessages((prev) => prev.map((message) => {
            if (message.id !== assistantMsgId) return message
            return {
              ...message,
              content: message.content + token,
            }
          }))
        },
        (blocks, summary, saved) => {
          if (saved) {
            localStorage.setItem('dp_today_refresh_at', String(Date.now()))
            window.dispatchEvent(new CustomEvent('dp_today_refresh'))
          } else if (blocks && blocks.length > 0) {
            setPendingPlan({ blocks, summary, sessionId: activeSessionId! })
            setMessages((prev) => [
              ...prev,
              {
                id: `plan-approval-${Date.now()}`,
                role: 'assistant',
                content: '',
                type: 'plan-pending-approval',
                planMeta: { blocks, summary },
              },
            ])
          }
        },
        () => setIsLoading(false),
        (errorMessage) => {
          setMessages((prev) => prev.map((message) => {
            if (message.id !== assistantMsgId) return message
            return {
              ...message,
              content: `Sorry, something went wrong: ${errorMessage}`,
            }
          }))
          setIsLoading(false)
        },
        abortRef.current.signal
      )
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        setIsLoading(false)
      }
    }
  }

  const handleApprove = async (blocks: ApiPlanBlock[], summary: string) => {
    try {
      await forceSavePlan(getLocalDateISO(), summary, blocks)
      localStorage.setItem('dp_today_refresh_at', String(Date.now()))
      window.dispatchEvent(new CustomEvent('dp_today_refresh'))
      setPendingPlan(null)
      toast({ title: '✅ Plan saved! Opening Today…' })
      router.push('/today')
    } catch (err) {
      toast({
        title: 'Could not save plan',
        description: String(err),
        variant: 'destructive',
      })
    }
  }

  const handleMarkdownFilePick = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    const content = await file.text()
    setInput(content)
  }

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between pb-3 border-b mb-2">
        <div className="flex items-center gap-2">
          <Avatar className="h-8 w-8 bg-gradient-to-br from-indigo-500 to-teal-500">
            <AvatarFallback className="bg-transparent text-white text-xs font-bold">DP</AvatarFallback>
          </Avatar>
          <div>
            <p className="text-sm font-bold">Day Planner AI</p>
            <p className="text-xs text-muted-foreground">Your intelligent planning assistant</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setShowSessions(!showSessions)
              loadPastSessions()
            }}
          >
            <Clock className="h-4 w-4 mr-1" /> History
          </Button>
          <Button variant="ghost" size="sm" onClick={startNewSession}>
            + New Chat
          </Button>
        </div>
      </div>

      {showSessions && (
        <div className="bg-white border rounded-xl shadow-lg p-3 mb-3 max-h-48 overflow-y-auto space-y-1">
          <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Past Sessions</p>
          {pastSessions.length === 0 && <p className="text-xs text-muted-foreground">No previous sessions yet.</p>}
          {pastSessions.map((session) => (
            <button
              key={session.id}
              onClick={() => resumeSession(session.id)}
              className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-50 text-sm flex justify-between"
            >
              <span className="font-medium">{session.title || 'Planning Session'}</span>
              <span className="text-xs text-muted-foreground">
                {new Date(session.created_at).toLocaleDateString()}
              </span>
            </button>
          ))}
        </div>
      )}

      <ScrollArea className="flex-1 pr-2" ref={scrollRef as any}>
        <div className="space-y-4 py-2">
          {messages.map((message) => {
            if (message.type === 'plan-pending-approval' && message.planMeta) {
              return (
                <PlanApprovalCard
                  key={message.id}
                  blocks={message.planMeta.blocks}
                  summary={message.planMeta.summary}
                  onApprove={() => handleApprove(message.planMeta!.blocks, message.planMeta!.summary)}
                  onRevise={() => setInput('Please revise — ')}
                />
              )
            }

            return (
              <div key={message.id} className={cn('flex gap-3', message.role === 'user' && 'flex-row-reverse')}>
                {message.role === 'assistant' && (
                  <Avatar className="h-8 w-8 shrink-0 bg-gradient-to-br from-indigo-500 to-teal-500 shadow-md shadow-primary/20">
                    <AvatarFallback className="bg-transparent text-white">
                      <Sparkles className="h-4 w-4" />
                    </AvatarFallback>
                  </Avatar>
                )}
                <div
                  className={cn(
                    'max-w-[80%] rounded-2xl px-4 py-3 text-sm shadow-sm',
                    message.role === 'assistant'
                      ? 'bg-slate-100 rounded-tl-none text-slate-800'
                      : 'bg-primary text-white rounded-tr-none'
                  )}
                >
                  {message.role === 'assistant' ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose prose-sm max-w-none">
                      {message.content || '▋'}
                    </ReactMarkdown>
                  ) : (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  )}
                </div>
              </div>
            )
          })}

          {isLoading && (
            <div className="flex gap-3">
              <Avatar className="h-8 w-8 bg-primary shadow-md shadow-primary/20 shrink-0 animate-pulse">
                <AvatarFallback className="bg-primary text-white">
                  <Sparkles className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <div className="bg-slate-100 p-4 rounded-2xl rounded-tl-none shadow-sm flex gap-1.5 items-center">
                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {messages.length <= 2 && !isLoading && (
        <div className="flex flex-wrap gap-2 py-2">
          {QUICK_REPLIES.map((reply) => (
            <button
              key={reply}
              onClick={() => handleSend(reply)}
              className="text-xs px-3 py-1.5 rounded-full border border-primary/30 text-primary hover:bg-primary/5 transition-colors font-medium"
            >
              {reply}
            </button>
          ))}
        </div>
      )}

      <div className="pt-3 border-t bg-slate-50/50 backdrop-blur-sm">
        <div className="flex gap-2 items-end">
          <input
            ref={markdownFileInputRef}
            type="file"
            accept=".md,text/markdown"
            className="hidden"
            onChange={handleMarkdownFilePick}
          />
          <button
            onClick={() => markdownFileInputRef.current?.click()}
            className="shrink-0 p-2 rounded-lg hover:bg-slate-100 text-muted-foreground"
          >
            <FileText className="h-4 w-4" />
          </button>
          <Textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                handleSend()
              }
            }}
            placeholder="Tell me about your day... (Enter to send, Shift+Enter for new line)"
            className="resize-none min-h-[44px] max-h-32 rounded-xl border-slate-200 focus:border-primary bg-white"
            rows={1}
          />
          <Button onClick={() => handleSend()} disabled={!input.trim() || isLoading} size="icon" className="shrink-0 rounded-xl h-11 w-11">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

function PlanApprovalCard({
  blocks,
  summary,
  onApprove,
  onRevise,
}: {
  blocks: ApiPlanBlock[]
  summary: string
  onApprove: () => void
  onRevise: () => void
}) {
  const categoryColors: Record<string, string> = {
    work: 'border-indigo-400 bg-indigo-50',
    meeting: 'border-teal-400 bg-teal-50',
    break: 'border-emerald-400 bg-emerald-50',
    personal: 'border-amber-400 bg-amber-50',
    class: 'border-blue-400 bg-blue-50',
  }

  return (
    <div className="border-2 border-primary/20 rounded-2xl bg-white p-4 shadow-md space-y-3">
      <div className="flex items-center gap-2">
        <div className="p-1.5 bg-primary/10 rounded-lg">
          <LayoutDashboard className="h-4 w-4 text-primary" />
        </div>
        <p className="font-bold text-sm">Proposed Plan — Pending Your Approval</p>
      </div>
      <p className="text-xs text-muted-foreground">{summary}</p>

      <div className="space-y-2 max-h-52 overflow-y-auto">
        {blocks.map((block, index) => (
          <div
            key={index}
            className={cn(
              'flex items-center gap-3 p-2 rounded-xl border-l-4',
              categoryColors[block.category] || 'border-slate-300 bg-slate-50'
            )}
          >
            <div className="text-xs font-mono text-muted-foreground w-20 shrink-0">
              {block.start_time} – {block.end_time}
            </div>
            <div>
              <p className="text-xs font-bold">{block.title}</p>
              {block.agent_note && <p className="text-[10px] text-muted-foreground italic">{block.agent_note}</p>}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2 pt-1">
        <Button size="sm" className="flex-1 rounded-xl font-bold" onClick={onApprove}>
          ✅ Approve & Save to Today
        </Button>
        <Button size="sm" variant="outline" className="flex-1 rounded-xl" onClick={onRevise}>
          ✏️ Request Changes
        </Button>
      </div>
      <Button variant="outline" className="w-full h-9 rounded-xl text-xs font-bold group" asChild>
        <a href="/today">
          Open in Today <ChevronRight className="ml-1 h-3 w-3 transition-transform group-hover:translate-x-0.5" />
        </a>
      </Button>
    </div>
  )
}
