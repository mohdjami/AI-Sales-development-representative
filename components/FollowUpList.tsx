import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function FollowUpList() {
  // TODO: Fetch real data from API or Supabase
  const followUps = [
    { id: 1, prospect: "John Doe", lastInteraction: "2023-05-01", sentiment: "Positive" },
    { id: 2, prospect: "Jane Smith", lastInteraction: "2023-05-02", sentiment: "Neutral" },
    // Add more dummy data as needed
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Follow-ups</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-4">
          {followUps.map((followUp) => (
            <li key={followUp.id} className="border-b pb-4">
              <p className="font-semibold">{followUp.prospect}</p>
              <p className="text-sm text-gray-600">Last Interaction: {followUp.lastInteraction}</p>
              <p className="text-xs text-gray-400">Sentiment: {followUp.sentiment}</p>
              <Button className="mt-2" size="sm">
                Schedule Meeting
              </Button>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

