
"use client"

import React from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { 
  CalendarDays, 
  MessageSquare, 
  LayoutDashboard, 
  History, 
  Settings,
  Sparkles,
  LogOut
} from 'lucide-react'
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { bootstrapFrontendInitialization, clearAuthSession, getStoredAccessToken, getMe, type MeResponse } from "@/lib/api-client"

const navItems = [
  { name: 'Today', icon: LayoutDashboard, href: '/today' },
  { name: 'Chat', icon: MessageSquare, href: '/chat' },
  { name: 'Calendar', icon: CalendarDays, href: '/calendar' },
  { name: 'History', icon: History, href: '/history' },
  { name: 'Settings', icon: Settings, href: '/settings' },
]

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [isReady, setIsReady] = React.useState(false)
  const [profile, setProfile] = React.useState<MeResponse | null>(null)

  React.useEffect(() => {
    let active = true
    const init = async () => {
      const token = getStoredAccessToken()
      if (!token) {
        router.replace('/auth')
        return
      }
      try {
        const me = await getMe()
        if (!active) return
        setProfile(me)
        await bootstrapFrontendInitialization()
        if (active) setIsReady(true)
      } catch (error) {
        clearAuthSession()
        router.replace('/auth')
      }
    }
    init()
    return () => {
      active = false
    }
  }, [router])

  const handleLogout = () => {
    clearAuthSession()
    router.replace('/auth')
  }

  if (!isReady) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-muted-foreground text-sm font-medium">
        Initializing your workspace...
      </div>
    )
  }

  const initials = profile?.full_name
    ?.split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || 'DP'

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-background">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 bg-white border-r p-6 shrink-0 h-screen sticky top-0">
        <div className="flex items-center gap-2 px-2 mb-8">
          <div className="bg-primary p-1.5 rounded-lg shadow-lg shadow-primary/20">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <span className="font-headline font-bold text-lg tracking-tight">Day Planner <span className="text-primary">AI</span></span>
        </div>
        
        <nav className="flex-1 space-y-1">
          {navItems.map((item) => (
            <Link 
              key={item.href} 
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                pathname === item.href 
                  ? "bg-primary text-primary-foreground shadow-md shadow-primary/20" 
                  : "text-muted-foreground hover:bg-slate-50 hover:text-foreground"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          ))}
        </nav>

        <div className="mt-auto p-4 bg-slate-50 rounded-2xl border border-slate-100">
          <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Account Level</p>
          <p className="text-sm font-bold">Free Tier</p>
          <div className="flex items-center justify-between mt-2">
            <Button variant="link" size="sm" className="p-0 h-auto text-xs text-primary font-bold hover:no-underline">UPGRADE TO PRO</Button>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="md:hidden flex items-center justify-between p-4 bg-white/80 backdrop-blur-md border-b sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <div className="bg-primary p-1 rounded-md">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <span className="font-headline font-bold text-base tracking-tight">Day Planner AI</span>
        </div>
        <div className="h-8 w-8 rounded-full bg-slate-100 border flex items-center justify-center">
          <span className="text-[10px] font-bold">{initials}</span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-4 md:p-8 max-w-7xl mx-auto w-full pb-24 md:pb-8">
        {children}
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-white border-t flex items-center justify-around px-2 z-50 shadow-[0_-4px_12px_rgba(0,0,0,0.05)]">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link 
              key={item.href} 
              href={item.href}
              className={cn(
                "flex flex-col items-center justify-center gap-1 flex-1 h-full transition-colors",
                isActive ? "text-primary" : "text-muted-foreground"
              )}
            >
              <item.icon className={cn("h-5 w-5", isActive && "fill-current/10")} />
              <span className="text-[10px] font-bold tracking-tight">{item.name}</span>
            </Link>
          )
        })}
      </nav>
    </div>
  )
}
