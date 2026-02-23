import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Prospect } from "./ProspectModal"
import { cn } from "@/lib/utils"
import { Building2, User, AtSign, CheckCircle2, HelpCircle } from "lucide-react"

type ProspectCardProps = {
  prospect: Prospect
  onClick: () => void
}

const sourceColors: Record<string, string> = {
  "Product Hunt": "bg-orange-500/10 text-orange-600 border-orange-500/20",
  "G2": "bg-red-500/10 text-red-600 border-red-500/20",
  "Hacker News Hiring": "bg-amber-500/10 text-amber-700 border-amber-500/20",
  "GitHub": "bg-violet-500/10 text-violet-600 border-violet-500/20",
  "Crunchbase": "bg-blue-500/10 text-blue-600 border-blue-500/20",
  "Wellfound": "bg-teal-500/10 text-teal-600 border-teal-500/20",
  "YC Directory": "bg-orange-600/10 text-orange-700 border-orange-600/20",
  "AngelList": "bg-muted text-muted-foreground border-border",
  "LinkedIn": "bg-sky-500/10 text-sky-600 border-sky-500/20",
  "Google": "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  "Reddit": "bg-rose-500/10 text-rose-600 border-rose-500/20",
}

export default function ProspectCard({ prospect, onClick }: ProspectCardProps) {
  const alignmentScore = prospect.alignment_score * 100
  const displayName = prospect.name || prospect.author
  const sourceBadgeClass = prospect.source
    ? (sourceColors[prospect.source] || "bg-muted text-muted-foreground border-border")
    : ""

  const emailVerified = prospect.email_confidence === "verified"
  const emailLikely = prospect.email_confidence === "likely"
  const hasEmail = !!prospect.email

  return (
    <Card
      className={cn(
        "glass-card cursor-pointer group hover:border-primary/50 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 relative overflow-hidden",
        prospect.isProspect ? "border-primary/20" : ""
      )}
      onClick={onClick}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

      <CardHeader className="pb-3 relative z-10">
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1 min-w-0">
            <h3 className="font-semibold text-lg leading-tight group-hover:text-primary transition-colors line-clamp-1">
              {displayName}
            </h3>
            <div className="flex items-center text-sm text-muted-foreground gap-1.5">
              <User className="h-3.5 w-3.5 shrink-0" />
              <p className="line-clamp-1">{prospect.role}</p>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1.5 shrink-0">
            <Badge variant={prospect.isProspect ? "default" : "secondary"}>
              {prospect.isProspect ? "Prospect" : "Lead"}
            </Badge>
            {prospect.source && (
              <Badge variant="outline" className={cn("text-[10px] px-1.5 py-0", sourceBadgeClass)}>
                {prospect.source}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="relative z-10 space-y-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted/50 p-2 rounded-md">
          <Building2 className="h-4 w-4 shrink-0" />
          <p className="font-medium text-foreground line-clamp-1">{prospect.company}</p>
        </div>

        {/* Email indicator */}
        {hasEmail && (
          <div className={cn(
            "flex items-center gap-2 text-xs px-2 py-1.5 rounded-md border",
            emailVerified ? "bg-green-500/10 text-green-700 border-green-500/20"
              : emailLikely ? "bg-blue-500/10 text-blue-700 border-blue-500/20"
                : "bg-muted/50 text-muted-foreground border-border"
          )}>
            {emailVerified || emailLikely
              ? <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
              : <HelpCircle className="h-3.5 w-3.5 shrink-0" />
            }
            <AtSign className="h-3 w-3 shrink-0 -ml-1" />
            <span className="font-mono truncate">{prospect.email}</span>
            <span className="ml-auto opacity-60 shrink-0">
              {emailVerified ? "✓" : emailLikely ? "~" : "?"}
            </span>
          </div>
        )}

        {/* Match Score */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground font-medium">Match Score</span>
            <span className={cn(
              "font-bold",
              alignmentScore >= 80 ? "text-green-500" : alignmentScore >= 50 ? "text-yellow-500" : "text-muted-foreground"
            )}>
              {alignmentScore.toFixed(0)}%
            </span>
          </div>
          <Progress
            value={alignmentScore}
            className="h-2"
            indicatorClassName={cn(
              alignmentScore >= 80 ? "bg-green-500" : alignmentScore >= 50 ? "bg-yellow-500" : "bg-muted-foreground"
            )}
          />
        </div>

        <div className="pt-1 border-t border-border/50">
          <p className="text-xs text-muted-foreground line-clamp-2 italic">
            {prospect.industry}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
