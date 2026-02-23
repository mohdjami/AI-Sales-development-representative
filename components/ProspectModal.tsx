"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Loader2, Mail, Building2, Globe, Sparkles, AlertCircle, Quote, AtSign, CheckCircle2, HelpCircle, XCircle, ExternalLink } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import axios from "axios"
import EmailDraftModal from "./EmailDrafts"
import { cn } from "@/lib/utils"

export type EmailCandidate = {
  address: string
  pattern: string
  pattern_rank: number
  confidence: "verified" | "likely" | "unverifiable" | "invalid" | "unknown"
  smtp_code?: number
  note?: string
}

export type Prospect = {
  author: string
  name?: string
  role: string
  company: string
  isProspect: boolean
  alignment_score: number
  industry: string
  pain_points: string[]
  solution_fit: string
  insights: string
  // New fields from enhanced pipeline
  email?: string
  email_confidence?: "verified" | "likely" | "unverifiable" | "unknown"
  email_candidates?: EmailCandidate[]
  source?: string
  url?: string
}

type ProspectModalProps = {
  prospect: Prospect
  onClose: () => void
}

const confidenceConfig = {
  verified: { icon: CheckCircle2, color: "text-green-500", label: "Verified", bg: "bg-green-500/10 border-green-500/20" },
  likely: { icon: CheckCircle2, color: "text-blue-500", label: "Likely valid", bg: "bg-blue-500/10 border-blue-500/20" },
  unverifiable: { icon: HelpCircle, color: "text-yellow-500", label: "Unverifiable", bg: "bg-yellow-500/10 border-yellow-500/20" },
  invalid: { icon: XCircle, color: "text-red-500", label: "Invalid", bg: "bg-red-500/10 border-red-500/20" },
  unknown: { icon: HelpCircle, color: "text-muted-foreground", label: "Unknown", bg: "bg-muted/50 border-border" },
}

const sourceColors: Record<string, string> = {
  "Product Hunt": "bg-orange-500/10 text-orange-600 border-orange-500/20",
  "G2": "bg-red-500/10 text-red-600 border-red-500/20",
  "Hacker News Hiring": "bg-amber-500/10 text-amber-700 border-amber-500/20",
  "GitHub": "bg-violet-500/10 text-violet-600 border-violet-500/20",
  "Crunchbase": "bg-blue-500/10 text-blue-600 border-blue-500/20",
  "Wellfound": "bg-teal-500/10 text-teal-600 border-teal-500/20",
  "YC Directory": "bg-orange-600/10 text-orange-700 border-orange-600/20",
  "AngelList": "bg-black/5 text-foreground border-border",
  "LinkedIn": "bg-sky-500/10 text-sky-600 border-sky-500/20",
  "Google": "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  "Reddit": "bg-rose-500/10 text-rose-600 border-rose-500/20",
}

export default function ProspectModal({ prospect, onClose }: ProspectModalProps) {
  const [showEmailDraft, setShowEmailDraft] = useState(false)
  const [emailDraft, setEmailDraft] = useState<{ subject: string; content: string } | null>(null)
  const [loading, setLoading] = useState(false)
  const [showAllEmails, setShowAllEmails] = useState(false)

  const displayName = prospect.name || prospect.author
  const primaryEmail = prospect.email
  const emailConf = prospect.email_confidence || "unknown"
  const confConfig = confidenceConfig[emailConf] || confidenceConfig.unknown
  const ConfIcon = confConfig.icon
  const sourceBadgeClass = prospect.source ? (sourceColors[prospect.source] || "bg-muted text-muted-foreground border-border") : ""

  const handleGenerateEmailDraft = async () => {
    setLoading(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await axios.post(`${apiUrl}/draft-emails`, prospect)
      setEmailDraft(response.data.email)
      setShowEmailDraft(true)
    } catch (error) {
      console.error("Error generating email draft:", error)
    } finally {
      setLoading(false)
    }
  }

  const alignmentScore = prospect.alignment_score * 100

  return (
    <>
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent className="sm:max-w-[720px] glass-card border-primary/10 overflow-hidden p-0 gap-0">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary/20 via-primary to-primary/20" />

          {/* Header */}
          <DialogHeader className="p-6 pb-4 flex-row items-start justify-between space-y-0">
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center gap-3 flex-wrap">
                <DialogTitle className="text-2xl font-bold">{displayName}</DialogTitle>
                <Badge variant={prospect.isProspect ? "default" : "secondary"} className={cn(
                  "text-xs px-2 py-0.5",
                  prospect.isProspect ? "bg-primary/20 text-primary hover:bg-primary/30" : ""
                )}>
                  {prospect.isProspect ? "High Intent" : "Lead"}
                </Badge>
                {prospect.source && (
                  <Badge variant="outline" className={cn("text-xs px-2 py-0.5", sourceBadgeClass)}>
                    {prospect.source}
                  </Badge>
                )}
              </div>
              <DialogDescription className="text-base flex items-center gap-2 flex-wrap">
                <span className="font-medium text-foreground">{prospect.role}</span>
                <span className="text-muted-foreground">at</span>
                <span className="font-medium text-foreground flex items-center gap-1">
                  <Building2 className="h-3.5 w-3.5" />
                  {prospect.company}
                </span>
                {prospect.url && (
                  <a
                    href={prospect.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline flex items-center gap-1 text-sm"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <ExternalLink className="h-3 w-3" />
                    View Source
                  </a>
                )}
              </DialogDescription>
            </div>

            <div className="flex flex-col items-end gap-1 shrink-0">
              <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Alignment</span>
              <div className="flex items-center gap-2">
                <span className={cn(
                  "text-2xl font-bold",
                  alignmentScore >= 80 ? "text-green-500" : alignmentScore >= 50 ? "text-yellow-500" : "text-muted-foreground"
                )}>
                  {alignmentScore.toFixed(0)}%
                </span>
                <Progress value={alignmentScore} className="w-16 h-2" />
              </div>
            </div>
          </DialogHeader>

          {/* Body */}
          <div className="px-6 py-4 space-y-5 bg-card/30 backdrop-blur-sm max-h-[60vh] overflow-y-auto">

            {/* Email Section */}
            {(primaryEmail || (prospect.email_candidates && prospect.email_candidates.length > 0)) && (
              <div className={cn("rounded-lg border p-3 space-y-2", confConfig.bg)}>
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium flex items-center gap-2">
                    <AtSign className="h-4 w-4" />
                    Discovered Email
                  </h4>
                  {prospect.email_candidates && prospect.email_candidates.length > 1 && (
                    <button
                      onClick={() => setShowAllEmails(!showAllEmails)}
                      className="text-xs text-primary hover:underline"
                    >
                      {showAllEmails ? "Hide" : `+${prospect.email_candidates.length} candidates`}
                    </button>
                  )}
                </div>
                {primaryEmail && (
                  <div className="flex items-center gap-2">
                    <ConfIcon className={cn("h-4 w-4 shrink-0", confConfig.color)} />
                    <code className="text-sm font-mono bg-background/60 px-2 py-0.5 rounded">{primaryEmail}</code>
                    <span className={cn("text-xs", confConfig.color)}>{confConfig.label}</span>
                    <a
                      href={`mailto:${primaryEmail}`}
                      className="ml-auto text-xs text-primary hover:underline flex items-center gap-1"
                    >
                      <Mail className="h-3 w-3" />
                      Open
                    </a>
                  </div>
                )}
                {showAllEmails && prospect.email_candidates && (
                  <div className="mt-2 space-y-1 border-t border-border/30 pt-2">
                    {prospect.email_candidates.slice(0, 6).map((c, i) => {
                      const cfg = confidenceConfig[c.confidence] || confidenceConfig.unknown
                      const Icon = cfg.icon
                      return (
                        <div key={i} className="flex items-center gap-2 text-xs">
                          <Icon className={cn("h-3 w-3 shrink-0", cfg.color)} />
                          <code className="font-mono text-foreground/80">{c.address}</code>
                          <span className="text-muted-foreground ml-auto">{c.pattern}</span>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Pain Points + Solution Fit + Insights */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2 uppercase tracking-wider flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    Pain Points
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {(prospect.pain_points || []).map((point, index) => (
                      <Badge key={index} variant="outline" className="bg-background/50 border-destructive/20 text-destructive-foreground">
                        {point}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2 uppercase tracking-wider flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    Solution Fit
                  </h4>
                  <p className="text-sm leading-relaxed bg-primary/5 p-3 rounded-lg border border-primary/10">
                    {prospect.solution_fit}
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2 uppercase tracking-wider">Industry</h4>
                  <Badge variant="secondary" className="rounded-full px-3">{prospect.industry}</Badge>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2 uppercase tracking-wider flex items-center gap-2">
                    <Quote className="h-4 w-4" />
                    AI Insights
                  </h4>
                  <p className="text-sm text-muted-foreground italic leading-relaxed bg-muted/50 p-3 rounded-lg">
                    "{prospect.insights}"
                  </p>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter className="p-6 pt-4 bg-muted/20 border-t border-border/50 flex flex-row justify-end items-center gap-2">
            {prospect.url && (
              <Button variant="outline" size="lg" asChild>
                <a href={prospect.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2">
                  <Globe className="h-4 w-4" />
                  View Profile
                </a>
              </Button>
            )}
            <Button
              onClick={handleGenerateEmailDraft}
              disabled={loading}
              className="w-full sm:w-auto shadow-lg shadow-primary/20"
              size="lg"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating Draft...
                </>
              ) : (
                <>
                  <Mail className="mr-2 h-4 w-4" />
                  Generate Personalized Email
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {showEmailDraft && (
        <EmailDraftModal prospect={prospect} emailDraft={emailDraft} onClose={() => setShowEmailDraft(false)} />
      )}
    </>
  )
}
