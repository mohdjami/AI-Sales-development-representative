import type React from "react"
import type { Metadata } from "next"
import { createClient } from "@/utils/supabase/server"
import { redirect } from "next/navigation"
import { AppSidebar } from "@/components/app-sidebar"

export const metadata: Metadata = {
  title: "Prospect App",
  description: "Generate and manage prospects",
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()
  const { data, error } = await supabase.auth.getUser()
  const user = data.user
  if (!user) {
    redirect('/login')
  }
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <AppSidebar user={user} />
      <main className="flex-1 overflow-y-auto lg:ml-72 transition-all duration-300">
        <div className="container mx-auto p-4 md:p-8 pt-6">
          {children}
        </div>
      </main>
    </div>
  )
}

