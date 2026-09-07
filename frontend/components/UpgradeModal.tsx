'use client'

import { useState } from 'react'
import { createCheckout } from '@/lib/api'

interface Props {
  details: { message: string; plan: string; limit: number; used: number } | null
  onClose: () => void
}

export default function UpgradeModal({ details, onClose }: Props) {
  const [loading, setLoading] = useState<string | null>(null)

  async function upgrade(plan: 'basic' | 'premium') {
    setLoading(plan)
    try {
      const { url } = await createCheckout(plan)
      window.location.href = url
    } catch {
      setLoading(null)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 max-w-md w-full shadow-2xl">
        <div className="text-center mb-6">
          <div className="text-4xl mb-3">⚡</div>
          <h2 className="text-xl font-bold text-white">You've reached your limit</h2>
          <p className="mt-2 text-gray-400 text-sm">
            {details?.message ?? 'You have reached your free daily word limit.'}
          </p>
          {details && (
            <p className="mt-1 text-gray-500 text-xs">
              {details.used} / {details.limit} words used on the <strong>{details.plan}</strong> plan
            </p>
          )}
        </div>

        <div className="space-y-3">
          <button
            onClick={() => upgrade('basic')}
            disabled={!!loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            {loading === 'basic' ? 'Redirecting…' : (
              <>
                <span>Upgrade to Basic</span>
                <span className="text-blue-200 text-sm font-normal">$20 / month</span>
              </>
            )}
          </button>

          <button
            onClick={() => upgrade('premium')}
            disabled={!!loading}
            className="w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            {loading === 'premium' ? 'Redirecting…' : (
              <>
                <span>Upgrade to Premium</span>
                <span className="text-purple-200 text-sm font-normal">$50 / month</span>
              </>
            )}
          </button>

          <button
            onClick={onClose}
            className="w-full py-2.5 text-gray-400 hover:text-white text-sm transition-colors"
          >
            Maybe later
          </button>
        </div>
      </div>
    </div>
  )
}
