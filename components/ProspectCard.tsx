import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Prospect } from "./ProspectModal"
import { cn } from "@/lib/utils"
import { Building2, User } from "lucide-react"

type ProspectCardProps = {
  prospect: Prospect
  onClick: () => void
}

export default function ProspectCard({ prospect, onClick }: ProspectCardProps) {
  const alignmentScore = prospect.alignment_score * 100

  return (
    <Card
      className={cn(
        "glass-card cursor-pointer group hover:border-primary/50 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 relative overflow-hidden",
        prospect.isProspect ? "border-primary/20" : ""
      )}
      onClick={onClick}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

      <CardHeader className="pb-3 relative z-10">
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1">
            <h3 className="font-semibold text-lg leading-tight group-hover:text-primary transition-colors line-clamp-1">
              {prospect.author}
            </h3>
            <div className="flex items-center text-sm text-muted-foreground gap-1.5">
              <User className="h-3.5 w-3.5" />
              <p className="line-clamp-1">{prospect.role}</p>
            </div>
          </div>
          <Badge variant={prospect.isProspect ? "default" : "secondary"} className="shrink-0">
            {prospect.isProspect ? "Prospect" : "Lead"}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="relative z-10 space-y-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted/50 p-2 rounded-md">
          <Building2 className="h-4 w-4 shrink-0" />
          <p className="font-medium text-foreground line-clamp-1">{prospect.company}</p>
        </div>

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

        <div className="pt-2 border-t border-border/50">
          <p className="text-xs text-muted-foreground line-clamp-2 italic">
            "{prospect.industry}"
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

