"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Loader2, Send, Wand2, Copy, Check, Mail } from "lucide-react"
import { toast } from "sonner"
import { useState, useEffect } from "react"
import { Prospect } from "./ProspectModal"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { createClient } from "@/utils/supabase/client"

type EmailDraft = {
  subject: string
  content: string
}

type EmailDraftModalProps = {
  prospect: Prospect
  emailDraft: EmailDraft | null
  onClose: () => void
}

export default function EmailDraftModal({ prospect, emailDraft, onClose }: EmailDraftModalProps) {
  const [loading, setLoading] = useState(false)
  const [email, setEmail] = useState<EmailDraft | null>(emailDraft)
  const [copied, setCopied] = useState(false)
  const [googleConnected, setGoogleConnected] = useState<boolean | null>(null)
  const supabase = createClient()

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://ai-sdr-production.up.railway.app'

  useEffect(() => {
    checkGoogleStatus()
  }, [])

  const checkGoogleStatus = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return
      const res = await fetch(`${apiUrl}/auth/google/status`, {
        headers: { 'Authorization': `Bearer ${session.access_token}` },
      })
      if (res.ok) {
        const data = await res.json()
        setGoogleConnected(data.connected)
      }
    } catch { setGoogleConnected(false) }
  }

  const handleSendEmail = async () => {
    if (!googleConnected) {
      toast.error('Please connect your Google account first (use the Connect Gmail button in the dashboard header)')
      return
    }
    setLoading(true)
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        toast.error('Please sign in first')
        return
      }

      const response = await fetch(`${apiUrl}/emails/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          to: prospect.author,
          subject: email?.subject,
          body: email?.content,
        })
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Failed to send email')
      }

      toast.success('Email sent via Gmail successfully!')
      onClose()
    } catch (error: any) {
      console.error('Error sending email:', error)
      toast.error(error.message || 'Failed to send email')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (email) {
      const text = `Subject: ${email.subject}\n\n${email.content}`
      navigator.clipboard.writeText(text)
      setCopied(true)
      toast.success('Email copied to clipboard')
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[700px] glass-card border-primary/10 p-0 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500" />

        <DialogHeader className="px-6 py-4 bg-muted/20 border-b border-border/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-full bg-primary/10 text-primary">
                <Wand2 className="h-4 w-4" />
              </div>
              <div>
                <DialogTitle className="text-xl">AI Email Draft</DialogTitle>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Review and personalize before sending to <span className="font-medium text-foreground">{prospect.author}</span>
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 gap-1.5 text-muted-foreground hover:text-foreground"
              onClick={handleCopy}
            >
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              <span className="text-xs">{copied ? 'Copied' : 'Copy'}</span>
            </Button>
          </div>
        </DialogHeader>

        <div className="p-6 space-y-5">
          {email ? (
            <>
              <div className="space-y-2">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Subject Line</label>
                <Input
                  value={email.subject}
                  onChange={(e) => setEmail({ ...email, subject: e.target.value })}
                  className="font-medium bg-background/50 border-border/50 focus-visible:ring-primary/20"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Email Content</label>
                <div className="relative">
                  <Textarea
                    value={email.content}
                    onChange={(e) => setEmail({ ...email, content: e.target.value })}
                    className="min-h-[300px] resize-y bg-background/50 border-border/50 focus-visible:ring-primary/20 font-sans leading-relaxed p-4"
                  />
                  <div className="absolute bottom-3 right-3 text-xs text-muted-foreground bg-background/80 px-2 py-1 rounded-md backdrop-blur-sm border border-border/50">
                    {email.content.length} chars
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
              <Loader2 className="h-8 w-8 animate-spin mb-4 text-primary/50" />
              <p>Generating perfect draft...</p>
            </div>
          )}
        </div>

        <DialogFooter className="px-6 py-4 bg-muted/20 border-t border-border/50 gap-2">
          <Button variant="outline" onClick={onClose} className="border-border/50 hover:bg-muted/50">
            Discard
          </Button>
          <Button
            onClick={handleSendEmail}
            disabled={loading || !email}
            className="min-w-[120px] shadow-lg shadow-primary/20"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Send Email
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

