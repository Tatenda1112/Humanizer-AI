'use client'

import { useState } from 'react'
import Link from 'next/link'

const APP_NAME = 'HumanizeAI'
const API_URL  = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const features = [
  { icon: '🛡️', title: 'Passes all major detectors',   desc: 'Tested against GPTZero, Turnitin, Originality.ai, and Copyleaks.' },
  { icon: '🎭', title: '5 tone modes',                  desc: 'Academic, casual, professional, friendly, or creative — your choice.' },
  { icon: '📊', title: 'Before & after score',          desc: 'See exactly how much the AI score dropped in real time.' },
  { icon: '✅', title: 'Meaning always preserved',       desc: 'Facts, stats, and names are never changed. Only the style shifts.' },
  { icon: '∞',  title: 'No daily limits on paid plans', desc: 'Humanize as many words as you need every single day.' },
  { icon: '⚡', title: 'Results in seconds',            desc: 'Powered by the latest Claude and GPT-4o models for instant output.' },
]

const faqs = [
  {
    q: 'Does it work on Turnitin?',
    a: 'Yes. Our rewrites are designed to pass Turnitin\'s AI detection. We test every model update against major detectors before release.',
  },
  {
    q: 'Will it change my meaning?',
    a: 'No. We never alter facts, statistics, names, or technical terms. Only the phrasing and style change to sound more human.',
  },
  {
    q: 'How many words can I humanize for free?',
    a: 'The free plan includes 300 words per day — enough to try the tool and see the quality before upgrading.',
  },
  {
    q: 'What AI detectors does it bypass?',
    a: 'GPTZero, Turnitin, Originality.ai, Copyleaks, ZeroGPT, and most others. AI detection is an arms race and we stay ahead.',
  },
  {
    q: 'Can I cancel anytime?',
    a: 'Absolutely. Cancel from the billing portal at any time and you keep access until the end of your billing period.',
  },
]

export default function LandingPage() {
  const [demoText,    setDemoText]    = useState('')
  const [demoResult,  setDemoResult]  = useState('')
  const [demoLoading, setDemoLoading] = useState(false)

  async function handleDemo() {
    if (!demoText.trim() || demoLoading) return
    const words = demoText.trim().split(/\s+/)
    if (words.length > 100) {
      alert('Demo is limited to 100 words. Sign up for more!')
      return
    }
    setDemoLoading(true)
    try {
      const res = await fetch(`${API_URL}/humanize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: demoText, level: 'medium', tone: 'professional' }),
      })
      if (res.status === 401) {
        window.location.href = '/signup'
        return
      }
      const data = await res.json()
      setDemoResult(data.humanized_text ?? 'Sign up to see your result!')
    } catch {
      setDemoResult('Sign up to try the full tool!')
    } finally {
      setDemoLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Nav */}
      <nav className="border-b border-gray-800/50 px-6 py-4 flex items-center justify-between max-w-7xl mx-auto">
        <span className="text-xl font-bold">
          Humanize<span className="text-blue-500">AI</span>
        </span>
        <div className="hidden md:flex items-center gap-6 text-sm text-gray-400">
          <a href="#how"      className="hover:text-white transition-colors">How it works</a>
          <a href="#features" className="hover:text-white transition-colors">Features</a>
          <Link href="/pricing" className="hover:text-white transition-colors">Pricing</Link>
          <a href="#faq"      className="hover:text-white transition-colors">FAQ</a>
        </div>
        <div className="flex gap-3">
          <Link href="/login"  className="text-sm text-gray-400 hover:text-white transition-colors">Sign In</Link>
          <Link href="/signup" className="text-sm px-4 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors">
            Try Free
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-4 pt-24 pb-20 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-950 border border-blue-800 rounded-full text-blue-300 text-xs mb-6">
          <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
          Trusted by 10,000+ writers
        </div>
        <h1 className="text-5xl md:text-6xl font-extrabold leading-tight mb-6">
          Make Your AI Writing<br />
          <span className="text-blue-500">Sound Human</span>
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
          Bypass GPTZero, Turnitin and Originality.ai in seconds. Free to try.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Link
            href="/signup"
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-lg transition-colors"
          >
            Try Free Now
          </Link>
          <Link
            href="/pricing"
            className="px-8 py-4 bg-gray-800 hover:bg-gray-700 text-white font-bold rounded-xl text-lg transition-colors"
          >
            See Pricing
          </Link>
        </div>

        {/* Mini demo */}
        <div className="max-w-2xl mx-auto bg-gray-900 border border-gray-700 rounded-2xl p-5 text-left">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Live demo — 100 words max</p>
          <textarea
            value={demoText}
            onChange={e => setDemoText(e.target.value)}
            placeholder="Paste a sentence of AI text here and hit Humanize…"
            rows={4}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleDemo}
            disabled={demoLoading || !demoText.trim()}
            className="mt-3 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white font-medium rounded-lg text-sm transition-colors"
          >
            {demoLoading ? 'Humanizing…' : 'Humanize'}
          </button>
          {demoResult && (
            <div className="mt-4 p-3 bg-green-900/20 border border-green-800 rounded-lg text-sm text-green-100">
              {demoResult}
            </div>
          )}
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="bg-gray-900/50 py-20">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-12">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: '1', title: 'Paste AI text',              desc: 'Copy any AI-generated text — essay, email, blog post, anything.' },
              { step: '2', title: 'Choose level & tone',         desc: 'Pick light, medium, or aggressive rewriting, and select your tone.' },
              { step: '3', title: 'Get human-sounding text',     desc: 'Receive naturally rewritten text that passes every AI detector.' },
            ].map(s => (
              <div key={s.step} className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-xl font-bold">
                  {s.step}
                </div>
                <h3 className="font-semibold text-lg">{s.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 max-w-6xl mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-12">Everything you need</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map(f => (
            <div key={f.title} className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
              <div className="text-3xl mb-4">{f.icon}</div>
              <h3 className="font-semibold text-lg mb-2">{f.title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20 bg-gray-900/50">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Simple pricing</h2>
          <p className="text-gray-400 mb-10">Start free. No credit card required.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            {[
              { name: 'Free',    price: '$0',  per: '/month', highlight: false, features: ['300 words/day', 'Basic humanization', 'AI detector'], cta: 'Get Started', href: '/signup' },
              { name: 'Basic',   price: '$20', per: '/month', highlight: true,  features: ['10,000 words/month', 'No daily limits', 'All levels & tones'], cta: 'Start Basic', href: '/signup' },
              { name: 'Premium', price: '$50', per: '/month', highlight: false, features: ['Unlimited words', 'Fastest models', 'Priority support'], cta: 'Start Premium', href: '/signup' },
            ].map(p => (
              <div key={p.name} className={`rounded-2xl p-6 border ${p.highlight ? 'border-blue-500 bg-blue-950/30' : 'border-gray-700 bg-gray-900'}`}>
                {p.highlight && <div className="text-xs text-blue-400 font-bold uppercase mb-2">Most Popular</div>}
                <div className="text-lg font-bold">{p.name}</div>
                <div className="text-3xl font-extrabold mt-2">{p.price}<span className="text-sm font-normal text-gray-400">{p.per}</span></div>
                <ul className="mt-4 space-y-2 mb-6">
                  {p.features.map(f => <li key={f} className="text-sm text-gray-300 flex gap-2"><span className="text-green-400">✓</span>{f}</li>)}
                </ul>
                <Link href={p.href} className={`block text-center py-2.5 rounded-lg font-semibold text-sm transition-colors ${p.highlight ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-700 hover:bg-gray-600'}`}>
                  {p.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-20 max-w-3xl mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-12">Frequently asked questions</h2>
        <div className="space-y-4">
          {faqs.map(faq => (
            <details key={faq.q} className="group bg-gray-900 border border-gray-800 rounded-xl p-5 cursor-pointer">
              <summary className="font-semibold text-white list-none flex justify-between items-center">
                {faq.q}
                <span className="text-gray-400 group-open:rotate-180 transition-transform">▾</span>
              </summary>
              <p className="mt-3 text-gray-400 text-sm leading-relaxed">{faq.a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* CTA banner */}
      <section className="py-20 text-center bg-gradient-to-b from-gray-900/50 to-gray-950">
        <h2 className="text-3xl font-bold mb-4">Ready to humanize your writing?</h2>
        <p className="text-gray-400 mb-8">Join thousands of students, writers, and professionals.</p>
        <Link href="/signup" className="px-10 py-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-lg transition-colors">
          Start Free — No Credit Card
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-10 px-6">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row justify-between gap-6 text-sm text-gray-500">
          <div>
            <span className="text-white font-bold">
              Humanize<span className="text-blue-500">AI</span>
            </span>
            <p className="mt-1">Make AI writing sound human.</p>
          </div>
          <div className="flex gap-8">
            <div className="space-y-2">
              <p className="text-gray-400 font-medium">Product</p>
              <Link href="/pricing" className="block hover:text-white transition-colors">Pricing</Link>
              <Link href="/dashboard" className="block hover:text-white transition-colors">Dashboard</Link>
            </div>
            <div className="space-y-2">
              <p className="text-gray-400 font-medium">Account</p>
              <Link href="/signup" className="block hover:text-white transition-colors">Sign Up</Link>
              <Link href="/login"  className="block hover:text-white transition-colors">Login</Link>
            </div>
          </div>
        </div>
        <p className="text-center text-gray-700 text-xs mt-8">
          © {new Date().getFullYear()} {APP_NAME}. All rights reserved.
        </p>
      </footer>
    </div>
  )
}
