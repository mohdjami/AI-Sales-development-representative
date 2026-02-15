import type React from "react"
import type { Metadata } from "next"
import { Inter } from 'next/font/google'
import "./globals.css"
import { createClient } from "@/utils/supabase/server"
import Header from "@/components/Header"
import { Toaster } from "sonner"

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" })

export const metadata: Metadata = {
  title: "AI SDR Platform",
  description: "AI-powered sales development and prospect management",
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()
  const { data } = await supabase.auth.getUser()
  const user = data.user

  return (
    <html lang="en" className="h-full dark">
      <body className={`${inter.variable} font-sans flex min-h-full flex-col antialiased bg-background text-foreground selection:bg-primary/20`}>
        <main className="flex-1">
          {children}
        </main>
        <Toaster position="top-right" />
      </body>
    </html>
  )
}
