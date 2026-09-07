import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'HumanizeAI — Make AI Writing Sound Human',
  description:
    'Bypass GPTZero, Turnitin and Originality.ai in seconds. Free to try.',
  openGraph: {
    title: 'HumanizeAI',
    description: 'Make your AI writing sound human instantly.',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
