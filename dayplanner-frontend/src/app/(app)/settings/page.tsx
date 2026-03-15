
"use client"

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Input } from "@/components/ui/input"
import { Bell, Shield, User, Sparkles, Clock, Globe } from 'lucide-react'
import {
  checkLLMUsageLimit,
  getLLMConfig,
  getSettings,
  listNotifications,
  listProviderModels,
  resetMemory,
  updateLLMConfig,
  updateSettings,
  type ApiLLMConfig,
  type ApiNotification,
  type ApiProviderModel,
  type ApiSettings,
} from "@/lib/api-client"

type SettingsTab = 'profile' | 'notifications' | 'ai' | 'privacy'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = React.useState<SettingsTab>('profile')
  const [settings, setSettings] = React.useState<ApiSettings>({
    timezone: 'UTC',
    planning_style: 'structured',
    morning_briefing_time: '07:30',
    evening_checkin_time: '21:00',
    notifications_enabled: true,
    privacy_mode: 'standard',
  })
  const [llmConfig, setLlmConfig] = React.useState<ApiLLMConfig>({
    primary_provider: 'openrouter',
    primary_api_key: '',
    primary_model: '',
    fallback_provider: 'gemini',
    fallback_api_key: '',
    fallback_model: '',
    usage_alert_enabled: true,
    usage_alert_threshold_pct: 80,
  })
  const [primaryModels, setPrimaryModels] = React.useState<ApiProviderModel[]>([])
  const [fallbackModels, setFallbackModels] = React.useState<ApiProviderModel[]>([])
  const [notifications, setNotifications] = React.useState<ApiNotification[]>([])
  const [usageNotice, setUsageNotice] = React.useState<string | null>(null)
  const [isSaving, setIsSaving] = React.useState(false)

  React.useEffect(() => {
    const loadSettings = async () => {
      try {
        const [loaded, loadedConfig, loadedNotifications] = await Promise.all([
          getSettings(),
          getLLMConfig(),
          listNotifications(),
        ])
        const allowedStyles = new Set(['balanced', 'structured', 'flexible', 'minimal'])
        setSettings({
          timezone: loaded.timezone,
          planning_style: allowedStyles.has(loaded.planning_style) ? loaded.planning_style : 'structured',
          morning_briefing_time: loaded.morning_briefing_time,
          evening_checkin_time: loaded.evening_checkin_time,
          notifications_enabled: loaded.notifications_enabled,
          privacy_mode: loaded.privacy_mode,
        })
        setLlmConfig(loadedConfig)
        setNotifications(loadedNotifications)
      } catch (error) {
        console.error(error)
      }
    }
    loadSettings()
  }, [])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const updated = await updateSettings(settings)
      setSettings(updated)
    } catch (error) {
      console.error(error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleResetMemory = async () => {
    try {
      await resetMemory()
    } catch (error) {
      console.error(error)
    }
  }

  const loadPrimaryModels = async () => {
    if (!llmConfig.primary_api_key.trim()) return
    try {
      const models = await listProviderModels(llmConfig.primary_provider, llmConfig.primary_api_key.trim())
      setPrimaryModels(models)
      if (!llmConfig.primary_model && models[0]?.id) {
        setLlmConfig((prev) => ({ ...prev, primary_model: models[0].id }))
      }
    } catch (error) {
      console.error(error)
    }
  }

  const loadFallbackModels = async () => {
    if (!llmConfig.fallback_api_key.trim()) return
    try {
      const models = await listProviderModels(llmConfig.fallback_provider, llmConfig.fallback_api_key.trim())
      setFallbackModels(models)
      if (!llmConfig.fallback_model && models[0]?.id) {
        setLlmConfig((prev) => ({ ...prev, fallback_model: models[0].id }))
      }
    } catch (error) {
      console.error(error)
    }
  }

  const handleSaveLLM = async () => {
    setIsSaving(true)
    try {
      const updated = await updateLLMConfig(llmConfig)
      setLlmConfig(updated)
      const usage = await checkLLMUsageLimit()
      if (usage.alert_triggered) {
        setUsageNotice(`${usage.provider} usage is ${usage.usage_pct.toFixed(1)}%. Consider fallback model.`)
      } else {
        setUsageNotice(null)
      }
      setNotifications(await listNotifications())
    } catch (error) {
      console.error(error)
    } finally {
      setIsSaving(false)
    }
  }

  const tabButton = (tab: SettingsTab, label: string, icon: React.ReactNode) => (
    <Button
      variant="ghost"
      className={`w-full justify-start ${activeTab === tab ? 'text-primary bg-primary/10' : ''}`}
      onClick={() => setActiveTab(tab)}
    >
      {icon} {label}
    </Button>
  )

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20">
      <header>
        <h1 className="text-3xl font-headline font-bold">Account Settings</h1>
        <p className="text-muted-foreground">Manage your AI preferences and connected accounts.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        <aside className="md:col-span-1 space-y-1">
          {tabButton('profile', 'Profile', <User className="mr-2 h-4 w-4" />)}
          {tabButton('notifications', 'Notifications', <Bell className="mr-2 h-4 w-4" />)}
          {tabButton('ai', 'AI Preferences', <Sparkles className="mr-2 h-4 w-4" />)}
          {tabButton('privacy', 'Privacy', <Shield className="mr-2 h-4 w-4" />)}
        </aside>

        <div className="md:col-span-3 space-y-6">
          {activeTab === 'profile' && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Daily Schedule Engine</CardTitle>
                  <CardDescription>How strictly should the AI plan your time blocks?</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Planning Style</Label>
                      <p className="text-xs text-muted-foreground">Choose your level of structure.</p>
                    </div>
                    <Select value={settings.planning_style} onValueChange={(value) => setSettings((prev) => ({ ...prev, planning_style: value }))}>
                      <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Select style" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="balanced">Balanced</SelectItem>
                        <SelectItem value="structured">Structured (Fixed)</SelectItem>
                        <SelectItem value="flexible">Flexible (Estimates)</SelectItem>
                        <SelectItem value="minimal">Minimal (Key Tasks)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Auto-Resolve Conflicts</Label>
                      <p className="text-xs text-muted-foreground">Allow AI to move tasks based on calendar events.</p>
                    </div>
                    <Switch checked={settings.notifications_enabled} onCheckedChange={(checked) => setSettings((prev) => ({ ...prev, notifications_enabled: checked }))} />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Nudges & Engagement</CardTitle>
                  <CardDescription>Configure your daily automation triggers.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5 flex items-center gap-2">
                      <Clock className="h-4 w-4 text-primary" />
                      <div>
                        <Label>Morning Briefing</Label>
                        <p className="text-xs text-muted-foreground">Get a fresh summary every morning.</p>
                      </div>
                    </div>
                    <Input type="time" value={settings.morning_briefing_time} onChange={(event) => setSettings((prev) => ({ ...prev, morning_briefing_time: event.target.value }))} className="w-24 h-8" />
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5 flex items-center gap-2">
                      <Clock className="h-4 w-4 text-amber-500" />
                      <div>
                        <Label>Evening Check-in</Label>
                        <p className="text-xs text-muted-foreground">Review your accomplishments.</p>
                      </div>
                    </div>
                    <Input type="time" value={settings.evening_checkin_time} onChange={(event) => setSettings((prev) => ({ ...prev, evening_checkin_time: event.target.value }))} className="w-24 h-8" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Regional & Timezone</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Timezone</Label>
                    <div className="flex gap-2">
                      <div className="flex-1 bg-slate-50 border rounded-lg px-3 py-2 flex items-center gap-2 text-sm">
                        <Globe className="h-4 w-4 text-muted-foreground" />
                        {settings.timezone}
                      </div>
                      <Button variant="outline" size="sm" onClick={() => setSettings((prev) => ({ ...prev, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone }))}>Auto-Detect</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="pt-4 flex justify-end gap-3">
                <Button variant="ghost" onClick={handleResetMemory}>Reset Memory</Button>
                <Button onClick={handleSave} disabled={isSaving}>{isSaving ? 'Saving...' : 'Save Changes'}</Button>
              </div>
            </>
          )}

          {activeTab === 'notifications' && (
            <Card>
              <CardHeader>
                <CardTitle>Notifications</CardTitle>
                <CardDescription>System and usage notifications from your planner AI stack.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {usageNotice && (
                  <div className="text-sm rounded-lg border border-amber-200 bg-amber-50 text-amber-900 px-3 py-2">
                    {usageNotice}
                  </div>
                )}
                {notifications.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No notifications yet.</p>
                ) : (
                  notifications.map((item) => (
                    <div key={item.id} className="border rounded-lg px-3 py-2">
                      <p className="text-sm font-semibold capitalize">{item.kind}</p>
                      <p className="text-sm text-muted-foreground">{item.message}</p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          )}

          {activeTab === 'ai' && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Primary Provider</CardTitle>
                  <CardDescription>Set provider, API key, and model for primary responses.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Provider</Label>
                    <Select value={llmConfig.primary_provider} onValueChange={(value) => setLlmConfig((prev) => ({ ...prev, primary_provider: value, primary_model: '' }))}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select provider" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="openrouter">OpenRouter</SelectItem>
                        <SelectItem value="gemini">Gemini</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>API Key</Label>
                    <Input
                      type="password"
                      value={llmConfig.primary_api_key}
                      onChange={(event) => setLlmConfig((prev) => ({ ...prev, primary_api_key: event.target.value }))}
                      placeholder="Enter primary API key"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={loadPrimaryModels}>Load Models</Button>
                  </div>
                  <div className="space-y-2">
                    <Label>Model</Label>
                    <Select value={llmConfig.primary_model || undefined} onValueChange={(value) => setLlmConfig((prev) => ({ ...prev, primary_model: value }))}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select model" />
                      </SelectTrigger>
                      <SelectContent>
                        {primaryModels.map((model) => (
                          <SelectItem key={model.id} value={model.id}>{model.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Fallback Provider</CardTitle>
                  <CardDescription>Automatically used if your primary provider fails.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Provider</Label>
                    <Select value={llmConfig.fallback_provider} onValueChange={(value) => setLlmConfig((prev) => ({ ...prev, fallback_provider: value, fallback_model: '' }))}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select fallback provider" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="openrouter">OpenRouter</SelectItem>
                        <SelectItem value="gemini">Gemini</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>API Key</Label>
                    <Input
                      type="password"
                      value={llmConfig.fallback_api_key}
                      onChange={(event) => setLlmConfig((prev) => ({ ...prev, fallback_api_key: event.target.value }))}
                      placeholder="Enter fallback API key"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={loadFallbackModels}>Load Fallback Models</Button>
                  </div>
                  <div className="space-y-2">
                    <Label>Fallback Model</Label>
                    <Select value={llmConfig.fallback_model || undefined} onValueChange={(value) => setLlmConfig((prev) => ({ ...prev, fallback_model: value }))}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select fallback model" />
                      </SelectTrigger>
                      <SelectContent>
                        {fallbackModels.map((model) => (
                          <SelectItem key={model.id} value={model.id}>{model.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Usage Alerts</CardTitle>
                  <CardDescription>Warn before your provider usage limit is exhausted.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>Enable usage alerts</Label>
                    <Switch
                      checked={llmConfig.usage_alert_enabled}
                      onCheckedChange={(checked) => setLlmConfig((prev) => ({ ...prev, usage_alert_enabled: checked }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Alert threshold (%)</Label>
                    <Input
                      type="number"
                      min={1}
                      max={100}
                      value={llmConfig.usage_alert_threshold_pct}
                      onChange={(event) => setLlmConfig((prev) => ({ ...prev, usage_alert_threshold_pct: Number(event.target.value || '0') }))}
                    />
                  </div>
                </CardContent>
              </Card>

              <div className="pt-2 flex justify-end">
                <Button onClick={handleSaveLLM} disabled={isSaving}>{isSaving ? 'Saving...' : 'Save AI Preferences'}</Button>
              </div>
            </>
          )}

          {activeTab === 'privacy' && (
            <Card>
              <CardHeader>
                <CardTitle>Privacy</CardTitle>
                <CardDescription>Control memory and personalization behavior.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Privacy Mode</Label>
                    <p className="text-xs text-muted-foreground">Choose how personalized planning should be.</p>
                  </div>
                  <Select value={settings.privacy_mode} onValueChange={(value) => setSettings((prev) => ({ ...prev, privacy_mode: value }))}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Select privacy mode" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="standard">Standard</SelectItem>
                      <SelectItem value="strict">Strict</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Separator />
                <div className="flex justify-end">
                  <Button onClick={handleSave} disabled={isSaving}>{isSaving ? 'Saving...' : 'Save Privacy'}</Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
