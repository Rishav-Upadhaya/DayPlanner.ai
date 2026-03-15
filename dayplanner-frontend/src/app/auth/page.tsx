"use client"

import React from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Sparkles } from 'lucide-react'
import { completeGoogleCallback, getStoredAccessToken, login, signup, startGoogleLogin } from "@/lib/api-client"

function AuthPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [tab, setTab] = React.useState<'login' | 'signup'>('login')
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [fullName, setFullName] = React.useState('')
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null)

  React.useEffect(() => {
    const existingToken = getStoredAccessToken()
    if (existingToken) {
      router.replace('/today')
      return
    }

    const code = searchParams.get('code')
    const state = searchParams.get('state')
    if (!code) return

    const runGoogleCallback = async () => {
      setIsSubmitting(true)
      setErrorMessage(null)
      try {
        if (!state) {
          throw new Error('Missing state')
        }
        await completeGoogleCallback(code, state)
        router.replace('/today')
      } catch {
        setErrorMessage('Google login failed. Please try again.')
      } finally {
        setIsSubmitting(false)
      }
    }

    runGoogleCallback()
  }, [router, searchParams])

  const handleAuthSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setIsSubmitting(true)
    setErrorMessage(null)
    try {
      if (tab === 'signup') {
        await signup(email.trim(), fullName.trim(), password)
      } else {
        await login(email.trim(), password)
      }
      router.replace('/today')
    } catch {
      setErrorMessage(tab === 'signup' ? 'Signup failed. Try another email.' : 'Login failed. Check your credentials.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleGoogle = async () => {
    setIsSubmitting(true)
    setErrorMessage(null)
    try {
      const payload = await startGoogleLogin()
      window.location.href = payload.redirect_url
    } catch {
      setErrorMessage('Unable to start Google login.')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md space-y-6">
        <div className="flex items-center justify-center gap-2">
          <div className="bg-primary p-1.5 rounded-lg">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <span className="font-headline font-bold text-xl">Day Planner AI</span>
        </div>

        <Card className="shadow-lg border-slate-200">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl">Welcome</CardTitle>
            <CardDescription>Login or create your account to start real planning.</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={tab} onValueChange={(value) => setTab(value as 'login' | 'signup')} className="space-y-4">
              <TabsList className="grid grid-cols-2 w-full">
                <TabsTrigger value="login">Login</TabsTrigger>
                <TabsTrigger value="signup">Sign Up</TabsTrigger>
              </TabsList>

              <TabsContent value={tab}>
                <form className="space-y-4" onSubmit={handleAuthSubmit}>
                  {tab === 'signup' && (
                    <div className="space-y-2">
                      <Label htmlFor="fullName">Full Name</Label>
                      <Input
                        id="fullName"
                        value={fullName}
                        onChange={(event) => setFullName(event.target.value)}
                        placeholder="Your full name"
                        required
                      />
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      placeholder="you@example.com"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      placeholder="••••••••"
                      required
                      minLength={8}
                    />
                  </div>

                  {errorMessage && <p className="text-sm text-rose-600">{errorMessage}</p>}

                  <Button className="w-full" type="submit" disabled={isSubmitting}>
                    {isSubmitting ? 'Please wait...' : tab === 'signup' ? 'Create Account' : 'Login'}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>

            <div className="mt-4">
              <Button variant="outline" className="w-full" onClick={handleGoogle} disabled={isSubmitting}>
                Continue with Google
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default function AuthPage() {
  return (
    <React.Suspense fallback={<div className="min-h-screen bg-slate-50" />}>
      <AuthPageContent />
    </React.Suspense>
  )
}
