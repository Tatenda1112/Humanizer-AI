'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'
import {
  humanizeText,
  getProfile,
  LimitExceededError,
  type UserProfile,
} from '@/lib/api'
import UpgradeModal from '@/components/UpgradeModal'

const LEVELS = ['Light', 'Medium', 'Aggressive'] as const
const TONES  = ['Academic', 'Casual', 'Professional', 'Friendly', 'Creative'] as const

export default function DashboardPage() {
  const router  = useRouter()
  const supabase = createClient()

  const [profile, setProfile]           = useState<UserProfile | null>(null)
  const [inputText, setInputText]       = useState('')
  const [outputText, setOutputText]     = useState('')
  const [level, setLevel]               = useState('Medium')
  const [tone, setTone]                 = useState('Academic')
  const [mode, setMode]                 = useState<'ghost_1' | 'ghost_2'>('ghost_2')
  const [modeName, setModeName]         = useState('')
  const [loading, setLoading]           = useState(false)
  const [copied, setCopied]             = useState(false)
  const [error, setError]               = useState('')
  const [showUpgrade, setShowUpgrade]   = useState(false)
  const [limitDetails, setLimitDetails] = useState<any>(null)

  const wordCount    = inputText.trim()  ? inputText.trim().split(/\s+/).length  : 0
  const outWordCount = outputText.trim() ? outputText.trim().split(/\s+/).length : 0

  const loadProfile = useCallback(async () => {
    try { setProfile(await getProfile()) }
    catch { router.push('/login') }
  }, [router])

  useEffect(() => { loadProfile() }, [loadProfile])

  async function handleHumanize() {
    if (!inputText.trim() || loading) return
    setLoading(true)
    setError('')
    setOutputText('')
    try {
      const r = await humanizeText(inputText, level.toLowerCase(), tone.toLowerCase(), mode)
      setOutputText(r.humanized_text)
      setModeName(r.mode_name)
      await loadProfile()
    } catch (err) {
      if (err instanceof LimitExceededError) { setLimitDetails(err.details); setShowUpgrade(true) }
      else setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally { setLoading(false) }
  }

  async function handleCopy() {
    if (!outputText) return
    await navigator.clipboard.writeText(outputText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const planLabel = profile?.plan
    ? profile.plan.charAt(0).toUpperCase() + profile.plan.slice(1)
    : '…'

  return (
    <div className="min-h-screen bg-[#111111] text-white flex flex-col">

      {/* Nav */}
      <header className="flex items-center justify-between px-8 h-14 border-b border-white/[0.06]">
        <span className="font-semibold text-sm tracking-tight text-white">GhostWriter</span>
        <div className="flex items-center gap-4">
          <span className="text-xs text-white/30">{planLabel} plan</span>
          <button
            onClick={async () => { await supabase.auth.signOut(); router.push('/') }}
            className="text-xs text-white/30 hover:text-white/60 transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="flex-1 flex flex-col max-w-5xl mx-auto w-full px-8 py-6 gap-5">

        {/* Mode + settings row */}
        <div className="flex flex-wrap items-center gap-6">

          {/* Mode toggle */}
          <div className="flex items-center gap-1 p-1 rounded-lg bg-white/[0.04] border border-white/[0.06]">
            {(['ghost_1', 'ghost_2'] as const).map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all duration-150 ${
                  mode === m
                    ? 'bg-white text-black'
                    : 'text-white/40 hover:text-white/70'
                }`}
              >
                {m === 'ghost_1' ? 'Ghost 1' : 'Ghost 2'}
              </button>
            ))}
          </div>

          <div className="w-px h-5 bg-white/[0.08]" />

          {/* Level */}
          <div className="flex items-center gap-1">
            <span className="text-xs text-white/25 mr-2">Level</span>
            {LEVELS.map(l => (
              <button
                key={l}
                onClick={() => setLevel(l)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-150 ${
                  level === l
                    ? 'bg-white/10 text-white'
                    : 'text-white/30 hover:text-white/60'
                }`}
              >
                {l}
              </button>
            ))}
          </div>

          <div className="w-px h-5 bg-white/[0.08]" />

          {/* Tone */}
          <div className="flex items-center gap-1">
            <span className="text-xs text-white/25 mr-2">Tone</span>
            {TONES.map(t => (
              <button
                key={t}
                onClick={() => setTone(t)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-150 ${
                  tone === t
                    ? 'bg-white/10 text-white'
                    : 'text-white/30 hover:text-white/60'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Editor */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* Input */}
          <div className="flex flex-col rounded-xl border border-white/[0.07] bg-white/[0.02] overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.05]">
              <span className="text-xs font-medium text-white/25 uppercase tracking-widest">Original</span>
              {wordCount > 0 && <span className="text-xs text-white/20">{wordCount} words</span>}
            </div>

            <textarea
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              placeholder="Paste your AI-generated text here…"
              className="flex-1 w-full px-4 py-3 bg-transparent text-white/80 placeholder-white/15 resize-none focus:outline-none text-sm leading-7"
              style={{ minHeight: '380px' }}
            />

            {error && (
              <div className="px-4 pb-2 text-xs text-red-400/80">{error}</div>
            )}

            <div className="px-4 py-3 border-t border-white/[0.05]">
              <button
                onClick={handleHumanize}
                disabled={!inputText.trim() || loading}
                className="w-full py-2.5 rounded-lg text-sm font-semibold transition-all duration-150 disabled:opacity-25 disabled:cursor-not-allowed bg-white text-black hover:bg-white/90 active:scale-[0.98]"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Humanizing…
                  </span>
                ) : 'Humanize'}
              </button>
            </div>
          </div>

          {/* Output */}
          <div className="flex flex-col rounded-xl border border-white/[0.07] bg-white/[0.02] overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.05]">
              <span className="text-xs font-medium text-white/25 uppercase tracking-widest">Humanized</span>
              <div className="flex items-center gap-3">
                {modeName && (
                  <span className="text-xs text-white/25">{modeName}</span>
                )}
                {outWordCount > 0 && (
                  <span className="text-xs text-white/20">{outWordCount} words</span>
                )}
              </div>
            </div>

            {outputText ? (
              <textarea
                readOnly
                value={outputText}
                className="flex-1 w-full px-4 py-3 bg-transparent text-white/80 resize-none focus:outline-none text-sm leading-7"
                style={{ minHeight: '380px' }}
              />
            ) : (
              <div className="flex-1 flex items-center justify-center" style={{ minHeight: '380px' }}>
                <p className="text-sm text-white/12">Output will appear here</p>
              </div>
            )}

            <div className="px-4 py-3 border-t border-white/[0.05]">
              <button
                onClick={handleCopy}
                disabled={!outputText}
                className={`w-full py-2.5 rounded-lg text-sm font-medium transition-all duration-150 disabled:opacity-20 disabled:cursor-not-allowed border ${
                  copied
                    ? 'border-white/20 text-white/60 bg-white/[0.05]'
                    : 'border-white/[0.07] text-white/30 hover:text-white/60 hover:border-white/15 bg-transparent'
                }`}
              >
                {copied ? '✓  Copied' : 'Copy'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {showUpgrade && (
        <UpgradeModal details={limitDetails} onClose={() => setShowUpgrade(false)} />
      )}
    </div>
  )
}
