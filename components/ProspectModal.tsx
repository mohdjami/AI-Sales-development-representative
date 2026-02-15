"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Loader2, Mail, Building2, MapPin, Globe, Sparkles, AlertCircle, Quote } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import axios from "axios"
import EmailDraftModal from "./EmailDrafts"
import { cn } from "@/lib/utils"

export type Prospect = {
  author: string
  role: string
  company: string
  isProspect: boolean
  alignment_score: number
  industry: string
  pain_points: string[]
  solution_fit: string
  insights: string
}

type ProspectModalProps = {
  prospect: Prospect
  onClose: () => void
}

export default function ProspectModal({ prospect, onClose }: ProspectModalProps) {
  const [showEmailDraft, setShowEmailDraft] = useState(false)
  const [emailDraft, setEmailDraft] = useState<{ subject: string; content: string } | null>(null)
  const [loading, setLoading] = useState(false)

  const handleGenerateEmailDraft = async () => {
    setLoading(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://ai-sdr-production.up.railway.app'
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
        <DialogContent className="sm:max-w-[700px] glass-card border-primary/10 overflow-hidden p-0 gap-0">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary/20 via-primary to-primary/20" />

          <DialogHeader className="p-6 pb-4 flex-row items-start justify-between space-y-0">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-3">
                <DialogTitle className="text-2xl font-bold">{prospect.author}</DialogTitle>
                <Badge variant={prospect.isProspect ? "default" : "secondary"} className={cn(
                  "text-xs px-2 py-0.5",
                  prospect.isProspect ? "bg-primary/20 text-primary hover:bg-primary/30" : ""
                )}>
                  {prospect.isProspect ? "High Intent" : "Lead"}
                </Badge>
              </div>
              <DialogDescription className="text-base flex items-center gap-2">
                <span className="font-medium text-foreground">{prospect.role}</span>
                <span className="text-muted-foreground">at</span>
                <span className="font-medium text-foreground flex items-center gap-1">
                  <Building2 className="h-3.5 w-3.5" />
                  {prospect.company}
                </span>
              </DialogDescription>
            </div>

            <div className="flex flex-col items-end gap-1">
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

          <div className="px-6 py-4 space-y-6 bg-card/30 backdrop-blur-sm max-h-[60vh] overflow-y-auto">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2 uppercase tracking-wider flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    Pain Points
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {prospect.pain_points.map((point, index) => (
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
                  <Badge variant="secondary" className="rounded-full px-3">
                    {prospect.industry}
                  </Badge>
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

          <DialogFooter className="p-6 pt-4 bg-muted/20 border-t border-border/50 flex flex-row justify-end items-center">
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

