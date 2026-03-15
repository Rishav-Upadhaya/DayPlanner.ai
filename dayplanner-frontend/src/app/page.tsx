"use client"

import React from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { Button } from "@/components/ui/button"
import { Sparkles, ArrowRight, Calendar, MessageSquare, Brain, Zap, CheckCircle2 } from 'lucide-react'
import { cn } from "@/lib/utils"

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Navbar */}
      <header className="px-6 h-16 flex items-center justify-between bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b">
        <div className="flex items-center gap-2">
          <div className="bg-primary p-1 rounded-lg">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <span className="font-headline font-extrabold text-xl tracking-tighter">Day Planner <span className="text-primary">AI</span></span>
        </div>
        <nav className="hidden md:flex items-center gap-8">
          <Link href="#features" className="text-sm font-medium hover:text-primary transition-colors">Features</Link>
          <Link href="#pricing" className="text-sm font-medium hover:text-primary transition-colors">Pricing</Link>
          <Link href="/auth" className="text-sm font-medium bg-primary text-white px-5 py-2 rounded-full hover:bg-primary/90 transition-all">Start Planning</Link>
        </nav>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative py-20 lg:py-32 overflow-hidden bg-slate-50">
          <div className="container px-6 mx-auto grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8 text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold uppercase tracking-wider">
                <Zap className="h-3 w-3" /> Powered by GPT-4 & LangGraph
              </div>
              <h1 className="text-5xl lg:text-7xl font-headline font-extrabold leading-tight tracking-tight">
                Turn your messy day into <span className="text-primary">pure intention.</span>
              </h1>
              <p className="text-lg text-slate-600 max-w-xl mx-auto lg:mx-0 leading-relaxed">
                Day Planner AI is an intelligent agent that understands your life, your goals, and your calendar. Talk naturally, and let it build your perfect day.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Link href="/auth">
                  <Button size="lg" className="rounded-full px-8 text-lg font-bold shadow-xl shadow-primary/20 h-14 w-full sm:w-auto">
                    Get Started Free <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>
                <Button size="lg" variant="outline" className="rounded-full px-8 text-lg font-bold h-14 w-full sm:w-auto">
                  Watch Demo
                </Button>
              </div>
              <div className="flex items-center justify-center lg:justify-start gap-4 text-xs font-medium text-slate-400">
                <span className="flex items-center gap-1"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> No credit card</span>
                <span className="flex items-center gap-1"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Syncs with Google</span>
              </div>
            </div>
            
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 blur-[100px] rounded-full"></div>
              <div className="relative bg-white rounded-2xl shadow-2xl border p-2 overflow-hidden animate-in zoom-in duration-1000">
                <Image 
                  src="https://picsum.photos/seed/planner2/800/600" 
                  alt="App Interface" 
                  width={800} 
                  height={600} 
                  className="rounded-xl"
                  data-ai-hint="productivity app"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section id="features" className="py-24 bg-white">
          <div className="container px-6 mx-auto text-center space-y-16">
            <div className="max-w-2xl mx-auto space-y-4">
              <h2 className="text-4xl font-headline font-bold">Everything you need to follow through.</h2>
              <p className="text-slate-500">Traditional planners demand effort. Day Planner AI does the heavy lifting for you.</p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  title: "Conversational Planning",
                  desc: "User talks naturally. Agent listens, infers, plans. No manual drag-and-drop needed.",
                  icon: MessageSquare,
                  color: "text-blue-600",
                  bg: "bg-blue-50"
                },
                {
                  title: "Contextual Memory",
                  desc: "We learn your patterns over time. The AI remembers what works for you and what doesn't.",
                  icon: Brain,
                  color: "text-indigo-600",
                  bg: "bg-indigo-50"
                },
                {
                  title: "Calendar Sync",
                  desc: "Integrate multiple Google Calendars to prevent conflicts and prioritize what matters.",
                  icon: Calendar,
                  color: "text-teal-600",
                  bg: "bg-teal-50"
                }
              ].map((f, i) => (
                <div key={i} className="p-8 rounded-2xl border bg-slate-50 hover:bg-white hover:shadow-xl transition-all text-left space-y-4 group">
                  <div className={cn("p-3 rounded-xl inline-block", f.bg)}>
                    <f.icon className={cn("h-6 w-6", f.color)} />
                  </div>
                  <h3 className="text-xl font-headline font-bold">{f.title}</h3>
                  <p className="text-slate-600 text-sm leading-relaxed">{f.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Closing CTA */}
        <section className="py-24 bg-primary text-white overflow-hidden relative">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
          <div className="container px-6 mx-auto text-center space-y-8 relative z-10">
            <h2 className="text-4xl lg:text-6xl font-headline font-extrabold max-w-4xl mx-auto">Stop managing tasks. Start managing your life.</h2>
            <p className="text-xl opacity-80 max-w-xl mx-auto">Join 250,000+ professionals reclaiming their time.</p>
            <div className="pt-4">
              <Link href="/auth">
                <Button size="lg" variant="secondary" className="rounded-full px-12 h-16 text-lg font-bold shadow-2xl">
                  Try Day Planner AI Free
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="py-12 px-6 border-t bg-slate-50">
        <div className="container mx-auto flex flex-col md:flex-row justify-between items-center gap-8 text-slate-400 text-sm">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <span className="font-headline font-bold text-slate-900">Day Planner AI</span>
          </div>
          <div className="flex gap-8">
            <Link href="#" className="hover:text-primary">Privacy Policy</Link>
            <Link href="#" className="hover:text-primary">Terms of Service</Link>
            <Link href="#" className="hover:text-primary">Help Center</Link>
          </div>
          <p>© 2025 Day Planner AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
