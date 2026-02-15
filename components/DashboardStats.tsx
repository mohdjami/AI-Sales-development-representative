import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function DashboardStats() {
  // TODO: Fetch real data from API or Supabase
  const stats = {
    totalProspects: 100,
    emailsSent: 50,
    responseRate: "25%",
    meetingsScheduled: 10,
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Total Prospects</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold">{stats.totalProspects}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Emails Sent</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold">{stats.emailsSent}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Response Rate</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold">{stats.responseRate}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Meetings Scheduled</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold">{stats.meetingsScheduled}</p>
        </CardContent>
      </Card>
    </div>
  )
}

