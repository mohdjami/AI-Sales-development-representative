from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from urllib.parse import urlencode
import json
import aiohttp
from langchain_core.messages import SystemMessage, HumanMessage
from services.llm_service import LLMService
from typing import Dict, List
import logging
from redis import Redis


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

redis_client = Redis(host=os.getenv("REDIS_HOST"), 
                    port=6379, 
                    db=0,
                    password=os.getenv("REDIS_PASSWORD"),
                    ssl=True,
                    decode_responses=True
                    )
                    
CACHE_EXPIRY = 7 * 24 * 3600  # 7 days

class LinkedInService:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize LLM
        self.llm_service = LLMService()
        self.logger = logger 
        self.redis_client = Redis(host=os.getenv("REDIS_HOST"), 
                    port=6379, 
                    db=0,
                    password=os.getenv("REDIS_PASSWORD"),
                    ssl=True,
                    decode_responses=True
                    )
        # Initialize posts as None
        self.posts = None

    async def _fetch_linkedin_posts(self) -> List[Dict]:
        """Fetch posts from LinkedIn scraper"""
        # Define fallback posts outside the try block to ensure they're always available
        fallback_posts = [
            {
                "author": "Shivam Awasthi",
                "role": "Sr. Technical Recruiter @ Stellar Consulting | Certified Technical Recruiter",
                "company": "Stellar Consulting Solutions, LLC",
                "post": """Data Governance Manager
📍 Location: Wayne, PA
💼 Employment Type: Full-Time

About the Role:
We are seeking a Data Governance Manager to play a critical role in ensuring data quality, integrity, and compliance across our core systems...
[Rest of the post content]""",
                "location": "Wayne, PA",
                "post_type": "job"
            },
            {
                "author": "Tirtharaj Bhowmick",
                "role": "Recruitment Services Professional | MBA in Human Resource and Marketing",
                "company": "IBM",
                "post": """We are hiring for the position of Data Engineer – Data Governance in Hyderabad with 3.5 to 5 years of relevant experience.
[Rest of the post content]""",
                "location": "Hyderabad",
                "post_type": "job"
            },
            {
                "author": "Mahek Ashok",
                "role": "Senior Manager Talent Acquisition",
                "company": "Tiger Analytics",
                "post": "Looking for efficient ways to manage large-scale hiring processes.",
            },
            {
                "author": "Arijit Chatterjee",
                "role": "MDM and DG CoE",
                "company": "AI for Data",
                "post": "Seeking solutions to streamline data governance and quality assurance.",
            },
            {
                "author": "Deevya Naresh Kumar",
                "role": "Data Governance Manager",
                "company": "Jetstar Airways",
                "post": "Needs robust solutions for managing data governance in cloud settings.",
            },
            {
                "author": "Ravi Kumar",
                "role": "Data Lineage Specialist",
                "company": "Data Insights Inc.",
                "post": "Looking for innovative tools to enhance data lineage tracking and reporting.",
            },
            {
                "author": "Anjali Verma",
                "role": "Data Governance Consultant",
                "company": "Consulting Group",
                "post": "Seeking partnerships to improve data governance frameworks for clients.",
            },
            {
                "author": "Suresh Patel",
                "role": "Chief Data Officer",
                "company": "Tech Innovations",
                "post": "Exploring solutions for comprehensive data governance and lineage management.",
            },
            {
                "author": "Nisha Reddy",
                "role": "Data Quality Analyst",
                "company": "Quality Data Solutions",
                "post": "Looking for strategies to enhance data quality and lineage tracking.",
            }
        ]
        
        try:
            logger.info("Starting LinkedIn posts fetch operation")
            
            async with aiohttp.ClientSession() as session:
                logger.debug("Making request to LinkedIn scraper service")
                try:
                    async with session.post(
                        "http://localhost:8000/scrape",
                        json={
                            "keywords": ["data governance"],
                            "page": 1,
                            "limit": 20
                        },
                        timeout=10  # Add timeout to prevent hanging
                    ) as response:
                        logger.info(f"Scraper service response status: {response.status}")
                        
                        if response.status == 200:
                            try:
                                data = await response.json()
                                posts = data.get("posts", [])
                                
                                # Check if posts is not empty
                                if posts:
                                    logger.info(f"Successfully fetched {len(posts)} posts from scraper service")
                                    logger.debug(f"Post authors: {[post.get('author') for post in posts]}")
                                    return posts
                                else:
                                    logger.warning("Scraper service returned empty posts list, using fallback posts")
                                    return fallback_posts
                            except Exception as e:
                                logger.error(f"Error parsing response JSON: {str(e)}")
                                logger.warning("Using fallback posts due to JSON parsing error")
                                return fallback_posts
                        else:
                            logger.warning(f"Scraper service returned status {response.status}, using fallback posts")
                            return fallback_posts
                except aiohttp.ClientError as e:
                    logger.error(f"Connection error while accessing scraper service: {str(e)}")
                    logger.warning("Using fallback posts due to connection error")
                    return fallback_posts
                except Exception as e:
                    logger.error(f"Unexpected error while connecting to scraper: {str(e)}")
                    logger.warning("Using fallback posts due to unexpected error")
                    return fallback_posts

        except Exception as e:
            logger.error(f"Unexpected error in _fetch_linkedin_posts: {str(e)}", exc_info=True)
            logger.warning("Using fallback posts due to exception")
            return fallback_posts
        finally:
            logger.info("LinkedIn posts fetch operation completed")

    async def _load_posts(self):
        """Load posts from scraper"""
        try:
            return await self._fetch_linkedin_posts()
        except Exception as e:
            logger.error(f"Error loading posts: {str(e)}")
            return []

    async def analyze_posts(self):
        """Analyze LinkedIn posts and extract insights"""
        try:
            # Load posts if not already loaded
            if self.posts is None:
                self.posts = await self._load_posts()
            logger.info(f"posts: {self.posts}")
            insights = []
            
            # Define the expected JSON structure
            json_structure = {
                "author": "string",
                "role":"string",
                "alignment_score": 0.0,
                "is_prospect": False,
                "industry": "string",
                "pain_points": ["string"],
                "solution_fit": "string",
                "insights": "string"
            }
            
            for post in self.posts:
                system_prompt = """You are an AI expert at analyzing LinkedIn posts to identify potential prospects for Atlan, a modern data catalog company.

                About Atlan:
                - Modern data catalog and governance platform
                - Helps companies manage their data assets, lineage, and metadata
                - Target audience: Data teams, Analytics leaders, Data Governance managers
                - Key solutions: Data discovery, governance, collaboration, and lineage
                - Ideal prospects: Companies dealing with data governance, metadata management, or building data cultures

                Analyze each post to:
                1. Determine if the person/company is a potential Atlan prospect
                2. Calculate alignment score (0-1) based on:
                   - Role relevance to data governance/catalog
                   - Company's likely data maturity
                   - Mentioned pain points that Atlan solves
                3. Extract specific pain points that Atlan can address
                4. Suggest how Atlan's solutions fit their needs"""

                user_prompt = f"""Analyze this LinkedIn post for Atlan prospecting:

                Author: {post['author']}
                Role: {post.get('role', 'Unknown')}
                Company: {post['company']}
                Content: {post['post']}

                Please provide:
                1. Alignment Score (0-1): How well they align with Atlan's target audience
                2. Is Prospect (true/false): Whether they're a viable prospect for Atlan
                3. Pain Points: Specific data-related challenges mentioned
                4. Solution Fit: How Atlan's capabilities address their needs
                5. Insights: Key observations about their data maturity and needs
                6. Outreach Priority (High/Medium/Low): Based on role and pain points
                7. Refined Role: Clarify/standardize the person's role if needed"""

                try:
                    ai_analysis = await self.llm_service.get_json_response(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        json_structure=json_structure
                    )
                    
                    insights.append({
                        "author": post["author"],
                        "role": post.get("role", "Unknown"),
                        "company": post["company"],
                        "post": post["post"],
                        "analysis": ai_analysis
                    })
                
                except Exception as e:
                    self.logger.error(f"Error analyzing post: {str(e)}")
                    continue
            
            return {"analyzed_posts": insights}
        except Exception as e:
            self.logger.error(f"Error analyzing posts: {str(e)}")
            raise

    async def get_prospects(self, min_alignment_score: float = 0.7):
        """Get prospective leads based on analysis"""
        try:
            analyzed_posts = await self.analyze_posts()
            prospects = []
            
            for post in analyzed_posts["analyzed_posts"]:
                analysis = post["analysis"]
                logger.info(analysis)
                if analysis.get("alignment_score", 0) >= min_alignment_score and analysis.get("is_prospect", False):
                    prospects.append({
                        "author": analysis["author"],
                        "role": analysis["role"],
                        "company": post["company"],
                        "isProspect": analysis["is_prospect"],
                        "alignment_score": analysis["alignment_score"],
                        "industry": analysis["industry"] if analysis.get("industry") else "unknown",
                        "pain_points": analysis["pain_points"],
                        "solution_fit": analysis["solution_fit"],
                        "insights": analysis["insights"]
                    })
            await self.store_analyzed_prospects(sorted(prospects, key=lambda x: x["alignment_score"], reverse=True))
            return {"prospects": sorted(prospects, key=lambda x: x["alignment_score"], reverse=True)}
        except Exception as e:
            logger.error(f"Error getting prospects: {str(e)}")
            raise

    async def finalize_post(self, post_id: str):
        """Finalize and store processed post"""
        try:
            # Add logic to mark post as processed
            # Store results in database
            # Update status
            return {"status": "success", "post_id": post_id}
        except Exception as e:
            logger.error(f"Error finalizing post: {str(e)}")
            raise

    async def store_analyzed_prospects(self, prospects: List[Dict]):
        """Store only the final analyzed prospects in Redis"""
        try:
            # Add LinkedIn post links to the known prospects
            final_prospects = []
            for prospect in prospects:
                prospect_data = prospect.copy()
                
                # Add known LinkedIn post links
                if prospect['author'] == "Shivam Awasthi":
                    prospect_data['post_link'] = "https://www.linkedin.com/posts/shivam-awasthi-3a2183186_data-governance-fulltime-activity-7297645657035608065-gTQY"
                elif prospect['author'] == "Tirtharaj Bhowmick":
                    prospect_data['post_link'] = "https://www.linkedin.com/posts/tirtharaj-bhowmick_jobopening-dataengineer-datagovernance-activity-7297645657035608065-gTQY"
                else:
                    prospect_data['post_link'] = ""
                
                final_prospects.append(prospect_data)

            # Store in Redis with 1-week expiry
            self.redis_client.set(
                "atlan_prospects",
                json.dumps(final_prospects),
                ex=CACHE_EXPIRY
            )
            
            logger.info(f"Stored {len(final_prospects)} analyzed prospects in Redis")
            
        except Exception as e:
            logger.error(f"Error storing prospects in Redis: {str(e)}")










dummy_mixed_replies = [
    {
        "type": "linkedin_post",
        "from": "Shivam Awasthi",
        "role": "Sr. Technical Recruiter @ Stellar Consulting",
        "company": "Stellar Consulting Solutions, LLC",
        "subject": "Data Governance Manager Position",
        "body": """Data Governance Manager
📍 Location: Wayne, PA
💼 Employment Type: Full-Time

About the Role:
We are seeking a Data Governance Manager to play a critical role in ensuring data quality, integrity, and compliance across our core systems...""",
        "post_link": "https://www.linkedin.com/posts/shivam-awasthi-3a2183186_data-governance-fulltime-activity-7297645657035608065-gTQY",
        "sentiment": "Positive",
        "intent": "Hiring",
        "alignment_score": 0.85
    },
    {
        "type": "email",
        "from": "example1@gmail.com",
        "role": "Data Team Lead",
        "company": "Tech Corp",
        "subject": "Re: Meeting Request",
        "body": "I'm interested in discussing this further. When can we meet?",
        "post_link": "",
        "sentiment": "Positive",
        "intent": "Follow-Up Required",
        "alignment_score": 0.75
    },
    {
        "type": "linkedin_post",
        "from": "Tirtharaj Bhowmick",
        "role": "Recruitment Services Professional",
        "company": "IBM",
        "subject": "Data Engineer – Data Governance Position",
        "body": """We are hiring for the position of Data Engineer – Data Governance in Hyderabad with 3.5 to 5 years of relevant experience...""",
        "post_link": "https://www.linkedin.com/posts/tirtharaj-bhowmick_jobopening-dataengineer-datagovernance-activity-7297645657035608065-gTQY",
        "sentiment": "Positive",
        "intent": "Hiring",
        "alignment_score": 0.9
    },
    {
        "type": "email",
        "from": "example2@gmail.com",
        "role": "Data Governance Specialist",
        "company": "Data Corp",
        "subject": "Re: Project Update",
        "body": "Thanks for the update. I need more information before proceeding.",
        "post_link": "",
        "sentiment": "Neutral",
        "intent": "Need More Info",
        "alignment_score": 0.6
    },
    {
        "type": "linkedin_post",
        "from": "Arijit Chatterjee",
        "role": "MDM and DG CoE",
        "company": "AI for Data",
        "subject": "Data Governance Implementation",
        "body": "Seeking solutions to streamline data governance and quality assurance.",
        "post_link": "",
        "sentiment": "Positive",
        "intent": "Seeking Solutions",
        "alignment_score": 0.75
    },
    {
        "type": "email",
        "from": "example3@gmail.com",
        "role": "Analytics Manager",
        "company": "Analytics Inc",
        "subject": "Re: Proposal",
        "body": "I'm not interested in your proposal at this time.",
        "post_link": "",
        "sentiment": "Negative",
        "intent": "Not Interested",
        "alignment_score": 0.3
    },
    {
        "type": "linkedin_post",
        "from": "Deevya Naresh Kumar",
        "role": "Data Governance Manager",
        "company": "Jetstar Airways",
        "subject": "Cloud Data Governance",
        "body": "Needs robust solutions for managing data governance in cloud settings.",
        "post_link": "",
        "sentiment": "Neutral",
        "intent": "Seeking Solutions",
        "alignment_score": 0.65
    }
]