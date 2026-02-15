from typing import Dict, List, Tuple, Any, Optional
from langgraph.graph import StateGraph, END
from .llm_service import LLMService
from typing import TypedDict, Annotated
import json
from langchain_core.messages import SystemMessage, HumanMessage
from datetime import datetime

from core.logger import logger

class ProspectData(TypedDict):
    author: str
    role: str
    company: str
    alignment_score: float
    industry: str
    pain_points: List[str]
    solution_fit: str
    insights: str

class EmailState(TypedDict):
    subject: str
    content: str 
    refined_content: str
    final_email: str
    prospect: ProspectData
    attempts: int
    should_continue: bool

class EmailDraft(TypedDict):
    prospect: ProspectData
    email: Dict[str, str]

class EmailService:
    def __init__(self):
        self.llm_service = LLMService()
        self.max_attempts = 2
        self.workflow = self.build_workflow()

    def build_workflow(self) -> StateGraph:
        """Creates the email workflow graph"""
        workflow = StateGraph(EmailState)

        # Add nodes with async functions
        workflow.add_node("create_subject", self.subject_agent)
        workflow.add_node("build_content", self.content_builder_agent)
        workflow.add_node("refine_content", self.content_refiner_agent)
        workflow.add_node("create_final", self.final_draft_agent)

        # Define edges
        workflow.add_edge("create_subject", "build_content")
        workflow.add_edge("build_content", "refine_content")
        
        # Conditional edge for refinement loop
        workflow.add_conditional_edges(
            "refine_content",
            lambda x: "refine_content" if x["should_continue"] else "create_final",
            {
                "refine_content": "refine_content",
                "create_final": "create_final"
            }
        )

        workflow.set_entry_point("create_subject")
        workflow.add_edge("create_final", END)

        return workflow.compile()

    async def subject_agent(self, state: EmailState) -> EmailState:
        """Agent responsible for creating email subject"""
        try:
            messages = [
                SystemMessage(content="""You are an expert email subject line writer for B2B sales.
                Create a compelling subject line that references their pain points and Atlan's solution.
                Respond in JSON format with a 'subject' field containing your subject line.
                Keep it under 50 characters."""),
                HumanMessage(content=f"""
                Prospect Information:
                Name: {state['prospect']['author']}
                Role: {state['prospect']['role']}
                Company: {state['prospect']['company']}
                Pain Points: {', '.join(state['prospect']['pain_points'])}
                Industry: {state['prospect']['industry']}
                Solution Fit: {state['prospect']['solution_fit']}
                Insights: {state['prospect']['insights']}
                """)
            ]

            response = await self.llm_service.llm.ainvoke(messages)
            
            # Clean the response
            cleaned_response = response.content.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()
            
            # Log the cleaned response for debugging
            logger.debug(f"Cleaned subject response: {cleaned_response}")
            
            try:
                state['subject'] = json.loads(cleaned_response)["subject"]
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in subject agent: {str(e)}")
                logger.error(f"Raw response: {response.content}")
                # Fallback: use a default subject or extract it from text
                if "subject" in cleaned_response.lower():
                    # Try to extract subject from text format
                    try:
                        subject_text = cleaned_response.split("subject")[1].strip()
                        # Remove any quotes, colons, etc.
                        subject_text = subject_text.strip('":,\n {}').strip()
                        state['subject'] = subject_text
                    except Exception:
                        state['subject'] = "Simplify Your Data Governance with Atlan"
                else:
                    state['subject'] = "Simplify Your Data Governance with Atlan"
            
            return state

        except Exception as e:
            logger.error(f"Error in subject agent: {str(e)}")
            logger.error(f"State: {state}")
            logger.error(f"Response: {response.content if 'response' in locals() else 'No response'}")
            # Provide a fallback subject
            state['subject'] = "Atlan: Modern Data Governance Solution"
            return state

    async def content_builder_agent(self, state: EmailState) -> EmailState:
        """Agent responsible for creating initial email content"""
        try:
            messages = [
                SystemMessage(content="""You are an expert B2B sales email writer.
                Create personalized email content and respond in JSON format with a 'content' field.
                The email should:
                1. Show understanding of their pain points
                2. Demonstrate how Atlan specifically solves their problems
                3. Include relevant social proof
                4. End with a clear call to action for a meeting
                5. Keep it concise (max 150 words)"""),
                HumanMessage(content=f"""
                Prospect Information:
                Name: {state['prospect']['author']}
                Role: {state['prospect']['role']}
                Company: {state['prospect']['company']}
                Pain Points: {', '.join(state['prospect']['pain_points'])}
                Industry: {state['prospect']['industry']}
                Solution Fit: {state['prospect']['solution_fit']}
                Insights: {state['prospect']['insights']}
                Subject Line: {state['subject']}
                """)
            ]

            response = await self.llm_service.llm.ainvoke(messages)
            
            # Clean the response
            cleaned_response = response.content.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()
            
            # Log the cleaned response for debugging
            logger.debug(f"Cleaned content response: {cleaned_response}")
            
            try:
                state['content'] = json.loads(cleaned_response)["content"]
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in content builder agent: {str(e)}")
                logger.error(f"Raw response: {response.content}")
                # Fallback: use the raw response if it seems to contain email content
                if "Dear" in cleaned_response or state['prospect']['author'] in cleaned_response:
                    state['content'] = cleaned_response
                else:
                    state['content'] = f"Dear {state['prospect']['author']},\n\nI noticed your focus on {', '.join(state['prospect']['pain_points'])} at {state['prospect']['company']}. Atlan's data catalog and governance platform directly addresses these challenges with our comprehensive solution.\n\nCould we schedule a brief call to discuss how Atlan has helped similar companies in the {state['prospect']['industry']} industry?\n\nBest regards,\n[Your Name]\nSales Development Representative\nAtlan"
            
            return state

        except Exception as e:
            logger.error(f"Error in content builder agent: {str(e)}")
            logger.error(f"State: {state}")
            logger.error(f"Response: {response.content if 'response' in locals() else 'No response'}")
            # Fallback: provide a generic content
            state['content'] = f"Dear {state['prospect']['author']},\n\nI noticed your focus on {', '.join(state['prospect']['pain_points'])} at {state['prospect']['company']}. Atlan's data catalog and governance platform directly addresses these challenges with our comprehensive solution.\n\nCould we schedule a brief call to discuss how Atlan has helped similar companies in the {state['prospect']['industry']} industry?\n\nBest regards,\n[Your Name]\nSales Development Representative\nAtlan"
            return state

    async def content_refiner_agent(self, state: EmailState) -> EmailState:
        """Agent responsible for refining email content"""
        try:
            messages = [
                SystemMessage(content="""You are an expert email editor. You MUST respond with valid JSON in the following format:
                {
                    "refined_content": "your refined email text here",
                    "needs_another_iteration": false
                }
                
                Important:
                - Use proper JSON escaping for quotes and special characters
                - Do not include any explanation text outside the JSON
                - Ensure the JSON is properly formatted
                
                Your task is to refine the email content focusing on:
                1. Improving clarity and conciseness
                2. Ensuring professional tone
                3. Optimizing persuasiveness
                4. Maintaining natural flow"""),
                HumanMessage(content=f"""
                Current Email:
                Subject: {state['subject']}
                Content: {state['content']}
                
                Context:
                Role: {state['prospect']['role']}
                Industry: {state['prospect']['industry']}
                """)
            ]

            response = await self.llm_service.llm.ainvoke(messages)
            
            # Clean the response
            cleaned_response = response.content.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            
            # Log the cleaned response for debugging
            logger.debug(f"Cleaned response: {cleaned_response}")
            
            try:
                result = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                logger.error(f"Raw response: {response.content}")
                # Fallback: keep the content as is
                result = {
                    "refined_content": state['content'],
                    "needs_another_iteration": False
                }

            state['refined_content'] = result.get('refined_content', state['content'])
            state['should_continue'] = result.get('needs_another_iteration', False) and state['attempts'] < self.max_attempts
            state['attempts'] += 1
            return state

        except Exception as e:
            logger.error(f"Error in content refiner agent: {str(e)}")
            logger.error(f"State: {state}")
            logger.error(f"Response: {response.content if 'response' in locals() else 'No response'}")
            # Fallback: return state without refinement
            state['refined_content'] = state['content']
            state['should_continue'] = False
            state['attempts'] += 1
            return state

    async def final_draft_agent(self, state: EmailState) -> EmailState:
        """Agent responsible for creating the final email draft"""
        try:
            messages = [
                SystemMessage(content="""You are an expert email formatter. 
                Format the email with proper greeting, signature, and professional structure.
                
                RESPOND ONLY WITH THE FINAL EMAIL TEXT. 
                DO NOT USE JSON FORMAT.
                DO NOT ADD ANY ADDITIONAL EXPLANATION OR FORMATTING."""),
                HumanMessage(content=f"""
                Email Components:
                Subject: {state['subject']}
                Refined Content: {state['refined_content']}
                
                Prospect:
                Name: {state['prospect']['author']}
                Role: {state['prospect']['role']}
                Company: {state['prospect']['company']}
                
                Sender Information:
                Name: [Your Name]
                Title: Sales Development Representative
                Company: Atlan
                """)
            ]

            response = await self.llm_service.llm.ainvoke(messages)
            
            # Simply use the raw response content without JSON parsing
            state['final_email'] = response.content.strip()
            
            # Log for debugging
            logger.debug(f"Final email content: {state['final_email']}")
            
            return state

        except Exception as e:
            logger.error(f"Error in final draft agent: {str(e)}")
            logger.error(f"State: {state}")
            logger.error(f"Response: {response.content if 'response' in locals() else 'No response'}")
            # Fallback: use the refined content if final formatting fails
            state['final_email'] = state.get('refined_content', '')
            return state

    async def process(self, prospect: Dict) -> EmailDraft:
        """Process a single prospect through the workflow"""
        try:
            # Sanitize and validate prospect data
            sanitized_prospect = {
                "author": prospect.get("author", ""),
                "role": prospect.get("role", "Unknown"),
                "company": prospect.get("company", ""),
                "alignment_score": prospect.get("alignment_score", 0.0),
                "industry": prospect.get("industry", ""),
                "pain_points": prospect.get("pain_points", []),
                "solution_fit": prospect.get("solution_fit", ""),
                "insights": prospect.get("insights", "")
            }

            initial_state: EmailState = {
                "subject": "",
                "content": "",
                "refined_content": "",
                "final_email": "",
                "prospect": sanitized_prospect,
                "attempts": 0,
                "should_continue": True
            }

            final_state = await self.workflow.ainvoke(initial_state)
            
            return {
                "prospect": sanitized_prospect,
                "email": {
                    "subject": final_state["subject"],
                    "content": final_state["final_email"]
                }
            }

        except Exception as e:
            logger.error(f"Error processing email for prospect: {str(e)}")
            logger.error(f"Prospect data: {prospect}")
            raise

    async def process_with_streaming(self, prospect: Dict):
        """Process a single prospect through the workflow with streaming updates"""
        try:
            stages = {
                "create_subject": {"subject": ""},
                "build_content": {"content": ""},
                "refine_content": {"refined_content": ""},
                "create_final": {"final_email": ""}
            }

            sanitized_prospect = {
                "author": prospect.get("author", ""),
                "role": prospect.get("role", "Unknown"),
                "company": prospect.get("company", ""),
                "alignment_score": prospect.get("alignment_score", 0.0),
                "industry": prospect.get("industry", ""),
                "pain_points": prospect.get("pain_points", []),
                "solution_fit": prospect.get("solution_fit", ""),
                "insights": prospect.get("insights", "")
            }

            initial_state: EmailState = {
                "subject": "",
                "content": "",
                "refined_content": "",
                "final_email": "",
                "prospect": sanitized_prospect,
                "attempts": 0,
                "should_continue": True
            }

            async for stream_type, chunk in self.workflow.astream(
                initial_state,
                stream_mode=["updates"]
            ):
                if isinstance(chunk, dict):
                    node_name = list(chunk.keys())[0]
                    if node_name in stages:
                        formatted_chunk = {
                            node_name: self._format_chunk_data(chunk[node_name], stages[node_name])
                        }
                        yield "updates", formatted_chunk

        except Exception as e:
            logger.error(f"Error in streaming process: {str(e)}")
            logger.error(f"Prospect data: {prospect}")
            yield "error", {"error": str(e)}
    
    def _format_chunk_data(self, chunk_data: Any, stage_structure: Dict) -> Dict:
        """Format chunk data according to the stage structure"""
        if isinstance(chunk_data, (str, int, float, bool)):
            return chunk_data
        
        if isinstance(chunk_data, (list, tuple)):
            return list(chunk_data)
        
        if isinstance(chunk_data, dict):
            return chunk_data
        
        if hasattr(chunk_data, '__dict__'):
            return chunk_data.__dict__
        
        return str(chunk_data)

    async def send_email(self, email_drafts: List[Dict]):
        """Method to send the drafted emails"""
        
        # TODO: Implement email sending functionality
        # This would integrate with your email service provider
        pass 