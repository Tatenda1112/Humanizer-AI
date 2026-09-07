'use client'

import { useState } from 'react'
import Link from 'next/link'
import { createCheckout } from '@/lib/api'

const plans = [
  {
    name: 'Free',
    monthly: 0,
    yearly: 0,
    popular: false,
    features: [
      '300 words per day',
      'Basic humanization',
      'AI detector included',
      'Light & Medium rewrite levels',
    ],
    cta: 'Get Started Free',
    action: 'signup',
    color: 'gray',
  },
  {
    name: 'Basic',
    monthly: 20,
    yearly: 17,
    popular: true,
    features: [
      '10,000 words per month',
      'No daily limits',
      'All 3 rewrite levels',
      'All 5 tone modes',
      'Words roll over monthly',
    ],
    cta: 'Start Basic',
    action: 'basic',
    color: 'blue',
  },
  {
    name: 'Premium',
    monthly: 50,
    yearly: 42,
    popular: false,
    features: [
      'Unlimited words',
      'Fastest processing (GPT-4o / Sonnet)',
      'All features',
      'Priority support',
      'API access (coming soon)',
    ],
    cta: 'Start Premium',
    action: 'premium',
    color: 'purple',
  },
]

export default function PricingPage() {
  const [yearly, setYearly]     = useState(false)
  const [loading, setLoading]   = useState<string | null>(null)

  async function handleCTA(action: string) {
    if (action === 'signup') return
    setLoading(action)
    try {
      const { url } = await createCheckout(action)
      window.location.href = url
    } catch {
      setLoading(null)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <Link href="/" className="text-xl font-bold">
          Humanize<span className="text-blue-500">AI</span>
        </Link>
        <div className="flex gap-4">
          <Link href="/login"  className="text-gray-400 hover:text-white text-sm">Sign In</Link>
          <Link href="/signup" className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium">
            Get Started
          </Link>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Simple, transparent pricing</h1>
          <p className="text-gray-400 text-lg">Start free. Upgrade when you need more.</p>

          {/* Toggle */}
          <div className="mt-8 inline-flex items-center gap-3 bg-gray-900 border border-gray-800 rounded-full p-1">
            <button
              onClick={() => setYearly(false)}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-colors ${!yearly ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
            >
              Monthly
            </button>
            <button
              onClick={() => setYearly(true)}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-colors ${yearly ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
            >
              Yearly <span className="text-xs text-green-400 ml-1">–17%</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map(plan => (
            <div
              key={plan.name}
              className={`relative rounded-2xl p-6 border ${
                plan.popular
                  ? 'border-blue-500 bg-blue-950/30'
                  : 'border-gray-800 bg-gray-900'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                    MOST POPULAR
                  </span>
                </div>
              )}

              <div className="mb-6">
                <h2 className="text-lg font-bold">{plan.name}</h2>
                <div className="mt-3 flex items-end gap-1">
                  <span className="text-4xl font-extrabold">
                    ${yearly ? plan.yearly : plan.monthly}
                  </span>
                  {plan.monthly > 0 && (
                    <span className="text-gray-400 text-sm mb-1">/month</span>
                  )}
                </div>
                {yearly && plan.monthly > 0 && (
                  <p className="text-xs text-green-400 mt-1">Billed annually</p>
                )}
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="text-green-400 mt-0.5">✓</span>
                    {f}
                  </li>
                ))}
              </ul>

              {plan.action === 'signup' ? (
                <Link
                  href="/signup"
                  className="block w-full py-3 text-center bg-gray-800 hover:bg-gray-700 text-white font-semibold rounded-xl transition-colors"
                >
                  {plan.cta}
                </Link>
              ) : (
                <button
                  onClick={() => handleCTA(plan.action)}
                  disabled={loading === plan.action}
                  className={`w-full py-3 font-semibold rounded-xl transition-colors disabled:opacity-50 ${
                    plan.popular
                      ? 'bg-blue-600 hover:bg-blue-700 text-white'
                      : 'bg-purple-600 hover:bg-purple-700 text-white'
                  }`}
                >
                  {loading === plan.action ? 'Redirecting…' : plan.cta}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
