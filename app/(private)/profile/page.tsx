import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { createClient } from "@/utils/supabase/server"
import { redirect } from "next/navigation"

interface ProfileSectionProps {
  user?: {
    name: string
    email: string
    avatar_url?: string
    provider?: string
    status?: "online" | "offline"
    email_verified?: boolean
    last_sign_in_at?: string
  }
}

export default async function ProfileSection() {
    const supabase = await createClient()
    const { data } = await supabase.auth.getUser()
    if (!data.user) {
        redirect('/login')
    }
    const user = data.user

    return (
    <Card className="w-full max-w-md mx-auto mt-32">
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <Avatar className="h-12 w-12">
            <AvatarImage src={user?.user_metadata?.avatar_url || "/placeholder.svg?height=48&width=48"} />
            <AvatarFallback>{user?.user_metadata.full_name?.charAt(0).toUpperCase() || user?.user_metadata.email.charAt(0).toUpperCase()}</AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold truncate">{user.user_metadata.full_name}</h3>
              {user.user_metadata.email_verified && (
                <Badge variant="outline" className="text-xs text-green-600">Verified</Badge>
              )}
            </div>

            <div className="mt-1 text-sm text-muted-foreground truncate">{user.email}</div>

            {user.app_metadata.provider && (
              <div className="mt-2">
                <Badge variant="outline" className="text-xs">
                  {user.app_metadata.provider}
                </Badge>
              </div>
            )}

            <div className="mt-2 text-sm text-muted-foreground">
              Last Sign In: {user.last_sign_in_at ? new Date(user.last_sign_in_at).toLocaleString() : 'N/A'}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

