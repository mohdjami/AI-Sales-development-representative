import { NextResponse } from "next/server"

export async function GET(request: Request) {
  // TODO: Implement actual API call to your backend
  const dummyProspects = [
    {
      author: "John Doe",
      role: "CTO",
      company: "Tech Corp",
      alignment_score: 0.85,
      industry: "Technology",
      pain_points: ["Data management", "Scalability"],
      solution_fit: "High",
      insights: "Interested in AI-driven solutions",
    },
    {
      author: "Jane Smith",
      role: "VP of Marketing",
      company: "Marketing Inc",
      alignment_score: 0.78,
      industry: "Marketing",
      pain_points: ["Lead generation", "Campaign analytics"],
      solution_fit: "Medium",
      insights: "Looking for data-driven marketing tools",
    },
    // Add more dummy prospects as needed
  ]

  return NextResponse.json(dummyProspects)
}

