import ProspectList from "@/components/ProspectList"
import redis from "@/utils/redis"
import { Users } from 'lucide-react'

export default async function ProspectsPage() {
  const cachedProspects = await redis.get("atlan_prospects")
  const prospects = JSON.parse(cachedProspects || '[]')

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent flex items-center gap-2">
          Prospects
          <Users className="h-6 w-6 text-primary" />
        </h1>
        <p className="text-muted-foreground text-lg">
          Manage your leads and find new opportunities
        </p>
      </div>
      <ProspectList initialProspects={prospects} />
    </div>
  )
}

