import base64
import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.params import Form
from fastapi.responses import RedirectResponse
import httpx
import os
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlencode

import requests


from services.reply_tracker import analyze_sentiment, generate_followup_email, get_gmail_service
from services.linkedin_service import LinkedInService
from services.email_service import EmailService
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Optional
from core.logger import logger
from supabase import create_client, Client
from redis import Redis
import logging

# from services.track_replies import GmailService
from datetime import datetime
from services.vector_service import VectorService
from services.meeting_analyzer import MeetingAnalyzer
from services.llm_service import LLMService

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Updated Pydantic model with optional fields
class Prospect(BaseModel):
    author: Optional[str] = None
    role: Optional[str] = "Unknown"
    company: Optional[str] = None
    isProspect: Optional[bool] = False
    alignment_score: Optional[float] = 0.0
    industry: Optional[str] = None
    pain_points: Optional[List[str]] = []
    solution_fit: Optional[str] = None
    insights: Optional[str] = None

    class Config:
        extra = "allow"


app = FastAPI()

import secrets  # Import the secrets module

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow only your frontend domain
    allow_credentials=True,  # Allow credentials (cookies, authorization headers)
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

redis_client = Redis(host=os.getenv("REDIS_HOST"), 
                    port=6379, 
                    db=0,
                    password=os.getenv("REDIS_PASSWORD"),
                    ssl=True,
                    decode_responses=True
                    )

CACHE_EXPIRY = 7 * 24 * 3600  # 7 days

# LinkedIn OAuth credentials
CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI")
SUPABASE_URL=os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY=os.getenv("SUPABASE_ANON_KEY")

# Initialize supabase 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def create_CSRF_token() -> str:
    """Generate a secure random CSRF token."""
    return secrets.token_urlsafe(32)  # Generate a secure token of 32 bytes



# LinkedIn OAuth URLs
# AUTHORIZATION_URL = (
#     "https://www.linkedin.com/oauth/v2/authorization"
#     "?response_type=code"
#     f"&client_id={CLIENT_ID}"
#     f"&redirect_uri={REDIRECT_URI}"
#     "&scope=openid%20profile%20email"
#     "&state=YOUR_RANDOM_STATE"
# )

AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/token"
PROFILE_URL = "https://api.linkedin.com/v2/me"

@app.get("/")
def home():
    return {"message": "Welcome to the AI SDR!"} 

# @app.get("/auth/linkedin")
# def linkedin_login():
#     params = {
#         "response_type": "code",
#         "client_id": CLIENT_ID,
#         "redirect_uri": REDIRECT_URI,
#         "scope": "openid profile email",
#         "state": create_CSRF_token()  # In production, generate a random state and validate it
#     }
#     url = f"{AUTHORIZATION_URL}?{urlencode(params)}"
#     return RedirectResponse(url)

# @app.get("/auth/callback")
# async def linkedin_callback(code: str, state: str):
#     if not code:
#         raise HTTPException(status_code=400, detail="Authorization code missing")
#     logger.info(code)
#     async with httpx.AsyncClient() as client:
#         # Exchange authorization code for access token
#         token_data = {
#             "grant_type": "authorization_code",
#             "code": code,
#             "redirect_uri": REDIRECT_URI,
#             "client_id": CLIENT_ID,
#             "client_secret": CLIENT_SECRET,
#         }
#         headers = {"Content-Type": "application/x-www-form-urlencoded"}
#         token_response = await client.post(TOKEN_URL, data=token_data, headers=headers)
#         logger.info(token_response)
#         if token_response.status_code != 200:
#             logger.error("Failed to obtain access token")
#             raise HTTPException(status_code=token_response.status_code, detail="Failed to obtain access token")

#         token_json = token_response.json()
#         access_token = token_json.get("access_token")

#         if not access_token:
#             logger.error("No access token found in the response")
#             raise HTTPException(status_code=400, detail="No access token found")

#         # Fetch user profile
#         profile_headers = {"Authorization": f"Bearer {access_token}"}
#         profile_response = await client.get(PROFILE_URL, headers=profile_headers)

#         if profile_response.status_code != 200:
#             logger.error("Failed to fetch user profile")
#             raise HTTPException(status_code=profile_response.status_code, detail="Failed to fetch user profile")

#         user_data = profile_response.json()
#         return {"user": user_data}

@app.get('/analyze')
async def analyze():
    linkedin_service = LinkedInService()
    ans = await linkedin_service.analyze_posts()
    return ans

@app.get('/prospects')
async def get_prospects(min_alignment_score: float = 0.7):
    linkedin_service = LinkedInService()
    prospects = await linkedin_service.get_prospects(min_alignment_score)
    logger.info(f"prospects: {prospects}")
    redis_client.setex("prospects", 1800, json.dumps(prospects))
    return prospects


@app.post('/draft-emails')
async def draft_emails(prospect: Prospect):
    try:
        logger.info(f"prospect 1: {prospect}")
        email_service = EmailService()
        draft = await email_service.process(prospect=prospect.dict())
        return draft
    except Exception as e:
        logger.error(f"Error in draft_emails endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate email draft: {str(e)}"
        )
    
@app.post("/send-email")
def send_email(data: Dict):
    """Store lead in Supabase, then send email"""
    try:
        logger.info("Starting email send process")
        logger.debug(f"Received data: {data}")

        # Extract data
        lead = data.get("prospect")
        if not lead:
            logger.error("No prospect data provided")
            raise HTTPException(status_code=400, detail="Prospect data is required")

        recipient = data.get("recipient")
        subject = data.get("subject")
        body = data.get("body")

        logger.info(f"Preparing to send email to {recipient} from {lead['company']}")

        # Step 1: Store the lead in Supabase
        lead_data = {
            "author": lead["author"],
            "role": lead["role"],
            "company": lead["company"],
            "pain_point": lead["pain_points"],
            "alignment_score": lead["alignment_score"],
            "status": "contacted"
        }
        
        logger.debug(f"Storing lead data in Supabase: {lead_data}")
        try:
            inserted_lead, _ = supabase.table("prospects").insert(lead_data).execute()
            lead_id = inserted_lead[1][0]["id"]
            logger.info(f"Successfully stored lead with ID: {lead_id}")
        except Exception as e:
            logger.error(f"Failed to store lead in Supabase: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to store lead data")

        # Step 2: Store the email metadata
        email_record = {
            "prospect_id": lead_id,
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "status": "sent"
        }
        
        logger.debug(f"Storing email record: {email_record}")
        try:
            supabase.table("emails").insert(email_record).execute()
            logger.info("Successfully stored email record")
        except Exception as e:
            logger.error(f"Failed to store email record: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to store email record")

        # Step 3: Send the email (commented out for now)
        logger.info(f"Would send email to {recipient} with subject: {subject}")
        # Uncomment when ready to send actual emails
        # try:
        #     msg = MIMEMultipart()
        #     msg["From"] = SMTP_EMAIL
        #     msg["To"] = recipient
        #     msg["Subject"] = subject
        #     msg.attach(MIMEText(body, "plain"))
        #
        #     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        #         server.starttls()
        #         server.login(SMTP_EMAIL, SMTP_PASSWORD)
        #         server.sendmail(SMTP_EMAIL, recipient, msg.as_string())
        #     logger.info("Email sent successfully")
        # except Exception as e:
        #     logger.error(f"Failed to send email: {str(e)}")
        #     raise HTTPException(status_code=500, detail="Failed to send email")

        logger.info("Email process completed successfully")
        return {
            "status": "success", 
            "message": "Email sent & lead stored",
            "lead_id": lead_id
        }

    except HTTPException as he:
        logger.error(f"HTTP Exception: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in send_email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/track-replies")
async def track_replies():
    """Fetch new replies, analyze responses, and update Supabase"""
    dummy_replies = [
        {
            "from": "example1@gmail.com",
            "subject": "Re: Data Catalog Demo",
            "body": "The demo was excellent! I'm very interested in moving forward with Atlan. Can we schedule a follow-up meeting to discuss pricing and implementation timeline?",
        },
        {
            "from": "example2@gmail.com",
            "subject": "Re: Atlan Data Governance Proposal",
            "body": "Thanks for the proposal. While the features look good, we need more information about security compliance and integration capabilities. Could you provide details?",
        },
        {
            "from": "example3@gmail.com",
            "subject": "Re: Data Catalog Implementation",
            "body": "I regret to inform you that we've decided to go with another vendor. Thank you for your time and detailed presentations.",
        },
        {
            "from": "example4@gmail.com",
            "subject": "Re: Atlan Features",
            "body": "The data lineage features look promising. However, I'm concerned about the migration process from our current system. What's your typical timeline for such transitions?",
        },
        {
            "from": "example5@gmail.com",
            "subject": "Re: Quick Question",
            "body": "This is exactly what we've been looking for! The metadata management capabilities are perfect for our use case. Let's set up a call with our technical team.",
        }
    ]
    
    try:
        analyzed_emails = []
        # service = get_gmail_service()
        # results = service.users().messages().list(userId="me", q="in:inbox -category:promotions").execute()
        # messages = results.get("messages", [])
        # logger.info("messages", messages)
        # for msg in messages:
        #     email_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        #     headers = email_data["payload"]["headers"]
        #     body_data = email_data["payload"]["body"].get("data", "")

            # if body_data:
            #     body = base64.urlsafe_b64decode(body_data).decode("utf-8")

            #     # Step 1: AI Sentiment & Intent Analysis
            #     sentiment, intent = analyze_sentiment(body)

            #     # Step 2: Store in Supabase
            #     supabase.table("emails").update({"status": "replied", "replied_at": "NOW()", "sentiment": sentiment}).eq("recipient", sender).execute()

            #     # Step 3: Trigger Follow-Up if Required
            #     if intent == "Follow-Up":
            #         generate_followup_email(sender, subject, body)
        for reply in dummy_replies:
            sender = reply["from"]
            subject = reply["subject"]
            body = reply["body"]
          
            # Step 1: AI Sentiment & Intent Analysis
            # data = await analyze_sentiment(body)
            sentiment, intent = await analyze_sentiment(body) 

            # Print the data in the desired format
            print(f"data Sentiment: {sentiment} intent: {intent}")
            # Step 2: Store in Supabase
            # supabase.table("emails").update({
            #     "status": "replied",
            #     "replied_at": "NOW()",
            #     "sentiment": sentiment
            # }).eq("recipient", sender).execute()
            analyzed_email = {
                            "email": {
                                "from": sender,
                                "subject": subject,
                                "body": body
                            },
                            "analysis": {
                                "sentiment": sentiment,
                                "intent": intent
                            }
                        }
            # Step 3: Trigger Follow-Up if Required
            if intent == "Follow-Up Required":
                follow_up = await generate_followup_email(sender, subject, body)
                analyzed_email["suggested_followup"] = follow_up

                print("follow-up", follow_up)
            analyzed_emails.append(analyzed_email)
        try:
            redis_client.set(
                "analyzed_emails",
                json.dumps(analyzed_emails),
                ex=CACHE_EXPIRY
            )
            logger.info(f"Stored {len(analyzed_emails)} analyzed emails in Redis")
        except Exception as e:
            logger.error(f"Error storing in Redis: {str(e)}")

        return {
            "status": "success", 
            "message": f"{len(dummy_replies)} replies analyzed",
            "analyzed_emails": analyzed_emails
        }    
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

EXPECTED_API_KEY = os.getenv("BOT_API_KEY")  # Set this to your expected API key
# Define the request model
class MeetingRequest(BaseModel):
    meeting_url: str
    title: str

@app.post("/add-bot")
async def add_bot(meeting: MeetingRequest):
    """Add a bot to the meeting and store meeting details"""
    try:
        logger.info(f"Adding bot to meeting: {meeting.meeting_url}")
        
        url = "https://api.meetingbaas.com/bots"
        headers = {
            "Content-Type": "application/json",
            # "x-meeting-baas-api-key": "51a9fe8967eab1e85e5e975ddaa10e536e7af03d67bac4cd00aff249bb413f07",
            'x-meeting-baas-api-key': EXPECTED_API_KEY
        }
        
        config = {
            "meeting_url": meeting.meeting_url,
            "bot_name": "AI Notetaker",
            "recording_mode": "speaker_view",
            "bot_image": "https://example.com/bot.jpg",
            "entry_message": "Hi I am Atlan's bot :)",
            "reserved": False,
            "speech_to_text": {
                "provider": "Default"
            },
            "automatic_leave": {
                "waiting_room_timeout": 600
            }
        }
        
        # Create bot
        response = requests.post(url, json=config, headers=headers)
        data = response.json()
        
        logger.info(f"Bot creation response: {data}")
        
        bot_id = data.get('bot_id')
        if not bot_id:
            raise HTTPException(status_code=500, detail="Bot ID not found in response")

        # Create meeting record in Supabase
        meeting_data = {
            "id": f"meet_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{bot_id[:8]}",
            "bot_id": bot_id,
            "meeting_url": meeting.meeting_url,
            "title": meeting.title,
            "status": "active",
        }

        try:
            result = supabase.table("meetings").insert(meeting_data).execute()
            created_meeting = result.data[0]
            logger.info(f"Meeting created in Supabase with ID: {created_meeting['id']}")
            
            return {
                "status": "success",
                "meeting": {
                    "id": created_meeting["id"],
                    "botId": created_meeting["bot_id"],
                    "meeting_url": created_meeting["meeting_url"],
                    "status": created_meeting["status"],
                }
            }

        except Exception as e:
            logger.error(f"Error creating meeting in Supabase: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create meeting record")

    except Exception as e:
        logger.error(f"Error in add_bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/remove-bot')
async def remove_bot(meeting: Dict):
    url = f"https://api.meetingbaas.com/bots/{meeting['bot_id']}"  # Use bot_id from the meeting dictionary
    headers = {
        "Content-Type": "application/json",
        "x-meeting-baas-api-key": EXPECTED_API_KEY
    }

    response = requests.delete(url, headers=headers)  # Send DELETE request
    if response.status_code == 200:
        data = response.json()
        return {"status": "success", "data": data}
    else:
        return {"status": "error", "message": response.text}

@app.post("/webhook")
async def meeting_webhook(request: Request):
    # Validate the API key from the header
    api_key = request.headers.get("x-meeting-baas-api-key")
    if api_key != EXPECTED_API_KEY:
        logger.error("Invalid API key: %s", api_key)
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    # Parse the incoming JSON data
    payload = await request.json()
    event_type = payload.get("event")
    data = payload.get("data", {})

    # Process different event types
    if event_type == "bot.status_change":
        bot_id = data.get("bot_id")
        status = data.get("status", {})
        code = status.get("code")
        created_at = status.get("created_at")
        logger.info("Bot %s status changed to %s at %s", bot_id, code, created_at)
        # Optionally, store or process the live status updates

    elif event_type == "complete":
        bot_id = data.get("bot_id")
        mp4_url = data.get("mp4")
        speakers = data.get("speakers")
        transcript = data.get("transcript")
        logger.info("Meeting complete for bot %s. Recording URL: %s", bot_id, mp4_url, transcript)

        result = supabase.table("meetings").select("*").eq("bot_id", bot_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail=f"No meeting found for bot_id: {bot_id}")
            
        meeting = result.data[0]
                    # Analyze meeting
        analyzer = MeetingAnalyzer()
        logger.info(transcript, speakers)
        analysis = await analyzer.analyze_meeting(transcript, meeting)


        meeting_id = meeting['id']
        
        logger.info(f"Found meeting: {meeting_id} for bot_id: {bot_id}")
        
        # Update meeting with analysis
        update_data = {
                "status": "completed",
                "transcript": transcript,
                "ai_summary": analysis["ai_summary"],
                "date": datetime.now().isoformat(),
                "duration": int(data.get('duration', 0)),
            }
        # Update the meeting record
        result = supabase.table("meetings").update(update_data).eq("id", meeting_id).execute()
        updated_meeting = result.data[0]
        logger.info(f"Updated meeting {meeting_id} with transcript and summary")
        # Save the meeting data (recording, speakers, transcript) into your knowledge base
        # Store in vector database
        vector_service = VectorService()
        await vector_service.store_meeting_data(updated_meeting)

        # Give the transcript to the AI agent it will summarize everything and give action points based on it
        
        # Create vector embeddings and store them to Pinecone

        # Use all the data to save in the supabase and the transcription also

        # e.g., insert into your database here
        return {"status": "success", "meeting_id": meeting["id"]}

    elif event_type == "failed":
        bot_id = data.get("bot_id")
        error_msg = data.get("error")
        logger.error("Meeting failed for bot %s: %s", bot_id, error_msg)
        # Handle failure (log, notify user, etc.)

    else:
        logger.error("Unknown event type received: %s", event_type)
        raise HTTPException(status_code=400, detail="Unknown event type")

    return {"status": "success"}


# @app.get('/emails')
# def get_emails(
#     query: Optional[str] = None,
#     max_results: Optional[int] = 10
# ) -> Dict:
#     """
#     Fetch emails from Gmail
    
#     Args:
#         query: Optional Gmail search query
#         max_results: Maximum number of emails to fetch
#     """
#     try:
#         gmail_service = GmailService()
#         messages = gmail_service.get_messages(query, max_results)
        
#         return {
#             "status": "success",
#             "count": len(messages),
#             "messages": [msg.dict() for msg in messages]
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    
    
    

# @app.post("/schedule-meeting")
# async def schedule_meeting(request: MeetingRequest):
#     """Schedule a meeting with the provided URL"""
#     try:
#         logger.info(f"Received meeting scheduling request with URL: {request.meeting_url}")
        
#         # Process the meeting URL
#         meeting_url = request.meeting_url
        
#         # Your existing meeting scheduling logic here
        
#         return {
#             "status": "success",
#             "message": "Meeting scheduled successfully",
#             "meeting_url": meeting_url
#         }
        
#     except Exception as e:
#         logger.error(f"Error scheduling meeting: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# Add this near your other model definitions
class SearchQuery(BaseModel):
    query: str
    max_results: Optional[int] = 5

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the Supabase JWT and return the user ID"""
    token = credentials.credentials
    try:
        user = supabase.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user.user
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Add this endpoint to your FastAPI app
@app.post("/search-knowledge-base")
async def search_knowledge_base(
    search_query: SearchQuery,
    user: object = Depends(get_current_user)
):
    """Search the meeting knowledge base using RAG"""
    try:
        user_id = user.id
        logger.info(f"Searching knowledge base for user {user_id}: {search_query.query}")
        
        vector_service = VectorService()
        llm_service = LLMService()
        
        # Use the RAG method to generate a response
        response = await vector_service.generate_rag_response(
            query=search_query.query,
            llm_service=llm_service,
            user_id=user_id,
            top_k=search_query.max_results
        )
        
        return {
            "status": "success",
            "response": response["answer"],
            "sources": response["sources"]
        }
    
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Add this endpoint to get all meetings
@app.get("/meetings")
async def get_meetings(status: Optional[str] = Query(None, description="Filter by meeting status (active/completed)")):
    """
    Get all meetings or filter by status
    
    Returns a list of meetings with their metadata and analysis results
    """
    try:
        logger.info(f"Fetching meetings with status filter: {status}")
        
        # Connect to the database
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_ANON_KEY")
        supabase_client = create_client(supabase_url, supabase_key)
        
        # Build the query
        query = supabase_client.table("meetings")
        
        # Apply status filter if provided
        if status:
            query = query.eq("status", status)
            
        # Execute the query and get results
        response = query.select("*").execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Supabase error: {response.error}")
            raise HTTPException(status_code=500, detail=f"Database error: {response.error}")
            
        meetings = response.data if hasattr(response, "data") else []
        
        # Process the meetings to ensure consistency
        processed_meetings = []
        for meeting in meetings:
            # Ensure all expected fields exist
            processed_meeting = {
                "id": meeting.get("id", ""),
                "bot_id": meeting.get("bot_id", ""),
                "meeting_url": meeting.get("meeting_url", ""),
                "status": meeting.get("status", "completed"),
                "title": meeting.get("title", "Untitled Meeting"),
                "date": meeting.get("date"),
                "transcript": meeting.get("transcript", ""),
                "ai_summary": meeting.get("ai_summary", "")
            }
            
            # Handle action items and insights (ensure they're properly formatted)
            if "action_items" in meeting:
                # If stored as string, keep as is; if stored as list, convert to JSON string
                if isinstance(meeting["action_items"], list):
                    processed_meeting["action_items"] = json.dumps(meeting["action_items"])
                else:
                    processed_meeting["action_items"] = meeting["action_items"]
            
            if "insights" in meeting:
                # If stored as string, keep as is; if stored as list, convert to JSON string
                if isinstance(meeting["insights"], list):
                    processed_meeting["insights"] = json.dumps(meeting["insights"])
                else:
                    processed_meeting["insights"] = meeting["insights"]
                    
            processed_meetings.append(processed_meeting)
        
        return {
            "status": "success",
            "meetings": processed_meetings
        }
        
    except Exception as e:
        logger.error(f"Error fetching meetings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify the service is running
    
    Returns basic service status information
    """
    return {
        "status": "healthy",
        "service": "AI SDR",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/store-in-vector-db")
async def store_in_vector_db():
    """
    Store a predefined meeting in the vector database
    
    This endpoint bypasses the normal flow and directly stores a hardcoded meeting
    in the vector database for testing purposes
    """
    try:
        logger.info("Starting vector database storage process")
        
        # Hardcoded meeting data based on existing record
        meeting_data = {
            "id": "meet_20250407_152504_89f13387",
            "title": "Atlan Interview",
            "meeting_url": "https://meet.google.com/amd-nfzf-imd",
            "status": "completed",
            "date": datetime.now().isoformat(),
            "duration": 8,
            # Shorten transcript for testing to avoid timeouts
            "transcript": "Mohd Jami: We create all the embeddings using Gini AI model and store in Supabase.\nAnshul Mehta: Can you go deeper into this embeddings model?\nMohd Jami: We use it for semantic search functionality.",
            "ai_summary": "Discussion about AI embeddings model and Supabase storage for semantic search.",
            "action_items": ["Test the system with actual meeting transcript data"],
            "insights": ["The team uses embeddings for semantic search"]
        }
        
        # Initialize vector service
        try:
            vector_service = VectorService()
            logger.info("Successfully initialized vector service")
        except Exception as e:
            logger.error(f"Error initializing vector service: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Vector service initialization failed: {str(e)}")
        
        # Store the meeting data directly in the vector database
        try:
            await vector_service.store_meeting_data(meeting_data)
            logger.info(f"Successfully stored meeting {meeting_data['id']} in vector database")
        except Exception as e:
            logger.error(f"Error in vector_service.store_meeting_data: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to store meeting data: {str(e)}")
        
        return {
            "status": "success",
            "message": f"Meeting {meeting_data['id']} stored in vector database",
            "meeting_id": meeting_data["id"]
        }
        
    except Exception as e:
        logger.error(f"Error storing meeting in vector database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
