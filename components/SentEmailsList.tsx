import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function SentEmailsList() {
  // TODO: Fetch real data from API or Supabase
  const sentEmails = [
    { id: 1, recipient: "John Doe", subject: "Introducing Our Solution", sentAt: "2023-05-01" },
    { id: 2, recipient: "Jane Smith", subject: "Follow-up on Our Conversation", sentAt: "2023-05-02" },
    // Add more dummy data as needed
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recently Sent Emails</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {sentEmails.map((email) => (
            <li key={email.id} className="border-b pb-2">
              <p className="font-semibold">{email.recipient}</p>
              <p className="text-sm text-gray-600">{email.subject}</p>
              <p className="text-xs text-gray-400">{email.sentAt}</p>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

