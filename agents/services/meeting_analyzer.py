from typing import Dict, Any
import logging
from services.llm_service import LLMService
logger = logging.getLogger(__name__)

class MeetingAnalyzer:
    def __init__(self):
        self.llm_service = LLMService() 
    async def analyze_meeting(self, transcript: str, meeting_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze meeting transcript and generate insights"""
        try:
            # Construct the system prompt
            system_prompt = """You are an AI meeting analyzer. Your task is to:
1. Create a concise summary of the meeting.
2. Extract key action items and decisions.
3. Identify main topics discussed.
4. Highlight important insights.
5. Format the transcript for better readability."""

            # Few-shot examples to demonstrate expected output quality
            few_shot_examples = """
Example 1:
Meeting Title: Product Roadmap Planning
Date: 2023-05-15

Short Transcript:
John: Let's review the Q3 roadmap. We need to prioritize either the mobile app redesign or the API overhaul.
Sarah: The customer feedback shows mobile experience is suffering. I think we should focus there first.
Michael: I agree, but we need to make sure the backend can support the new features.
John: Let's plan the redesign for Q3 and schedule the API work for early Q4.
Sarah: Sounds good. I'll prepare mock-ups by next Friday.
Michael: I'll assess the backend requirements by Wednesday.

Example Analysis:
{
  "ai_summary": "The meeting focused on prioritizing Q3 roadmap items, with the team deciding to proceed with the mobile app redesign in Q3 while postponing the API overhaul to early Q4. This decision was based on customer feedback highlighting issues with the mobile experience.",
  "action_items": [
    "Sarah to prepare mobile app redesign mock-ups by next Friday",
    "Michael to assess backend requirements by Wednesday",
    "Team to begin mobile redesign in Q3",
    "Schedule API overhaul for early Q4"
  ],
  "main_topics": [
    "Q3 roadmap prioritization",
    "Mobile app redesign vs API overhaul",
    "Customer feedback on mobile experience",
    "Backend compatibility requirements"
  ],
  "insights": [
    "Customer feedback is driving prioritization of mobile experience improvements",
    "Team recognizes the interdependence between frontend redesign and backend capabilities",
    "Sequential approach to major upgrades (mobile first, then API) to manage resources effectively"
  ],
  "formatted_transcript": "John: Let's review the Q3 roadmap. We need to prioritize either the mobile app redesign or the API overhaul.\n\nSarah: The customer feedback shows mobile experience is suffering. I think we should focus there first.\n\nMichael: I agree, but we need to make sure the backend can support the new features.\n\nJohn: Let's plan the redesign for Q3 and schedule the API work for early Q4.\n\nSarah: Sounds good. I'll prepare mock-ups by next Friday.\n\nMichael: I'll assess the backend requirements by Wednesday."
}

Example 2:
Meeting Title: Sales Team Weekly Check-in
Date: 2023-06-02

Short Transcript:
Lisa: Our conversion rate dropped 5% this week. What's happening?
David: The new pricing page is confusing customers. I've received multiple complaints.
Emma: We should revert to the old design or simplify immediately.
Lisa: Agreed. Let's revert by tomorrow. David, can you monitor results for the next week?
David: Yes, I'll create a dashboard and report back next meeting.
Emma: I suggest we also offer a special discount to recent visitors who abandoned their carts.
Lisa: Good idea. Let's do 15% off for the next 72 hours.

Example Analysis:
{
  "ai_summary": "The sales team identified a 5% drop in conversion rates attributed to customer confusion with the new pricing page. The team decided to revert to the old design immediately and offer a 15% discount to recent cart abandoners for the next 72 hours to recover potential lost sales.",
  "action_items": [
    "Revert pricing page to old design by tomorrow",
    "David to create a monitoring dashboard and track results for one week",
    "Implement 15% discount for recent cart abandoners (72-hour window)",
    "Review results at next meeting"
  ],
  "main_topics": [
    "Conversion rate drop (5% decrease)",
    "Customer confusion with new pricing page",
    "Recovery strategies for lost sales",
    "Performance monitoring approach"
  ],
  "insights": [
    "UI/UX changes can have immediate negative impact on conversion metrics",
    "Team is agile in responding to negative performance indicators",
    "Combination of reverting changes and offering incentives provides both short and longer-term solutions",
    "Data-driven approach with monitoring dashboard will help validate decisions"
  ],
  "formatted_transcript": "Lisa: Our conversion rate dropped 5% this week. What's happening?\n\nDavid: The new pricing page is confusing customers. I've received multiple complaints.\n\nEmma: We should revert to the old design or simplify immediately.\n\nLisa: Agreed. Let's revert by tomorrow. David, can you monitor results for the next week?\n\nDavid: Yes, I'll create a dashboard and report back next meeting.\n\nEmma: I suggest we also offer a special discount to recent visitors who abandoned their carts.\n\nLisa: Good idea. Let's do 15% off for the next 72 hours."
}
"""

            # Construct the user prompt as a string
            user_prompt = f"""
Here are examples of how to analyze meeting transcripts effectively:

{few_shot_examples}

Now, please analyze the following meeting:

Meeting Title: {meeting_info['title']}
Date: {meeting_info['date']}

Transcript:
{transcript}

Please provide:
1. A concise summary (max 3 paragraphs)
2. Key action items (bullet points)
3. Main topics discussed (bullet points)
4. Important insights (bullet points)
5. A cleaned, formatted version of the transcript
"""

            # Define the expected JSON structure
            json_structure = {
                "ai_summary": "",
                "action_items": [],
                "main_topics": [],
                "insights": [],
                "formatted_transcript": ""
            }

            # Call the LLM service to get the response
            ai_analysis = await self.llm_service.get_json_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_structure=json_structure
            )

            # Return structured analysis
            return {
                "ai_summary": ai_analysis.get("ai_summary", ""),
                "action_items": ai_analysis.get("action_items", []),
                "main_topics": ai_analysis.get("main_topics", []),
                "insights": ai_analysis.get("insights", []),
                "formatted_transcript": ai_analysis.get("formatted_transcript", "")
            }

        except Exception as e:
            logger.error(f"Error analyzing meeting: {str(e)}")
            raise 