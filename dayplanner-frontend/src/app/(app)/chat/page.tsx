
"use client"

import React from 'react'
import Link from 'next/link'
import { ChatInterface } from "@/components/chat/chat-interface"
import { Sparkles, History, MessageSquare } from 'lucide-react'
import { addMemoryItem, deleteMemoryItem, getMemoryContext, type ApiMemoryItem } from "@/lib/api-client"

export default function ChatPage() {
  const [memoryItems, setMemoryItems] = React.useState<ApiMemoryItem[]>([])
  const [showManage, setShowManage] = React.useState(false)
  const [memoryInput, setMemoryInput] = React.useState('')

  const loadMemoryContext = React.useCallback(async () => {
    try {
      const response = await getMemoryContext('chat planning')
      setMemoryItems(response.items)
    } catch (error) {
      console.error(error)
    }
  }, [])

  React.useEffect(() => {
    loadMemoryContext()
  }, [loadMemoryContext])

  const handleAddMemory = async () => {
    if (!memoryInput.trim()) return
    try {
      await addMemoryItem(memoryInput.trim(), 'note', 'medium')
      setMemoryInput('')
      await loadMemoryContext()
    } catch (error) {
      console.error(error)
    }
  }

  const handleDeleteMemory = async (memoryId: string) => {
    try {
      await deleteMemoryItem(memoryId)
      await loadMemoryContext()
    } catch (error) {
      console.error(error)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-headline font-bold">Conversational Planning</h1>
          <p className="text-muted-foreground">Talk naturally about your day and let the AI build your plan.</p>
        </div>
        <div className="hidden md:flex gap-2">
          <Link href="/history" className="flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-medium hover:bg-slate-50">
            <History className="h-4 w-4" /> History
          </Link>
          <button
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-medium hover:bg-slate-50"
            onClick={() => window.location.reload()}
          >
             <MessageSquare className="h-4 w-4" /> New Session
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-3">
          <ChatInterface />
        </div>
        
        <div className="space-y-6">
          <div className="bg-indigo-50 p-6 rounded-2xl border border-indigo-100">
            <h3 className="font-headline font-semibold text-indigo-900 mb-3 flex items-center gap-2">
              <Sparkles className="h-4 w-4" /> Pro Tips
            </h3>
            <ul className="space-y-4 text-xs text-indigo-800 leading-relaxed">
              <li className="flex gap-2">
                <span className="font-bold shrink-0">1.</span>
                <span>Mention energy levels: "I'm slow in the morning, plan my hard work for 2 PM."</span>
              </li>
              <li className="flex gap-2">
                <span className="font-bold shrink-0">2.</span>
                <span>Group tasks: "I have 3 errands to run in the afternoon, please batch them."</span>
              </li>
              <li className="flex gap-2">
                <span className="font-bold shrink-0">3.</span>
                <span>Ask for breaks: "Make sure I have a 30-min break every 2 hours."</span>
              </li>
            </ul>
          </div>
          
          <div className="bg-white p-6 rounded-2xl border shadow-sm space-y-4">
            <h3 className="font-headline font-semibold">Active Memory</h3>
            {memoryItems.length === 0 ? (
              <p className="text-xs text-muted-foreground leading-relaxed">No active memory items yet.</p>
            ) : (
              <ul className="space-y-2">
                {memoryItems.slice(0, showManage ? memoryItems.length : 2).map((item) => (
                  <li key={item.id} className="text-xs text-muted-foreground leading-relaxed border rounded-lg p-2 flex items-start justify-between gap-2">
                    <span>{item.content}</span>
                    {showManage && (
                      <button className="text-[10px] font-bold text-rose-600 hover:underline" onClick={() => handleDeleteMemory(item.id)}>
                        Remove
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
            {showManage && (
              <div className="space-y-2">
                <input
                  value={memoryInput}
                  onChange={(event) => setMemoryInput(event.target.value)}
                  placeholder="Add a memory note"
                  className="w-full text-xs border rounded-md px-2 py-1.5"
                />
                <button className="text-xs font-bold text-primary hover:underline" onClick={handleAddMemory}>Add Memory</button>
              </div>
            )}
            <button className="text-xs font-bold text-primary hover:underline" onClick={() => setShowManage((prev) => !prev)}>
              {showManage ? 'Done' : 'Manage Context'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
