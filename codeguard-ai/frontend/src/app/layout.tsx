import type { Metadata } from 'next'
import './globals.css'
import { Navbar } from '@/components/layout/navbar'
import { ErrorBoundary } from '@/components/ui/error-boundary'
import { AuthProvider } from '@/components/providers/auth-provider'

export const metadata: Metadata = {
  title: 'CodeGuard AI - Modern Security Scanner',
  description: 'Next-generation AI-powered code security and vulnerability scanner with modern UI',
  keywords: 'code security, AI scanner, vulnerability detection, modern UI',
  authors: [{ name: 'CodeGuard Team' }],
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="animated-bg text-white min-h-screen antialiased overflow-x-hidden">
        <ErrorBoundary>
          <AuthProvider>
            <div className="relative">
              <Navbar />
              <main className="relative z-10">
                {children}
              </main>
            </div>
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
}
