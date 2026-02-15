import os
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from supabase import create_client
from services.llm_service import LLMService
from google_auth_oauthlib.flow import InstalledAppFlow
import os
from google.auth.transport.requests import Request
from langchain_core.messages import SystemMessage, HumanMessage
import logging
from typing import List, Dict, Optional, Set


load_dotenv()

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Path to your credentials file
GMAIL_CREDENTIALS = "credentials.json"

# Define the required scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Groq AI Model for Sentiment & Intent Analysis
AI_MODEL = LLMService()

# Gmail API Credentials
GMAIL_CREDENTIALS = "credentials.json"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reply_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_gmail_service():
    """Authenticate and return a Gmail API service instance."""
    try:
        logger.info("Initializing Gmail service")
        
        creds = None

        # Check if token.json exists (stores refreshed credentials)
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        # If no valid credentials, request new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())  # Refresh the expired token
            else:
                # Start OAuth flow to generate new credentials
                flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS, SCOPES)
                creds = flow.run_local_server(port=0, prompt="select_account")

                # Save the credentials for future use
                with open("token.json", "w") as token_file:
                    token_file.write(creds.to_json())

        # Build the Gmail service
        service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail service successfully initialized")
        return service

    except Exception as e:
        logger.error(f"Error initializing Gmail service: {str(e)}")
        raise

async def analyze_sentiment(text):
    """Use AI to analyze sentiment & intent of email responses for Atlan's data catalog/governance solutions"""
    try:
        logger.info("Starting sentiment analysis for text")
        logger.debug(f"Input text for analysis: {text[:100]}...")
        
        prompt = [
            SystemMessage(content="""You are an AI that analyzes email responses specifically for Atlan, a modern data catalog and governance platform. 
            
            About Atlan:
            - Modern data catalog and governance platform
            - Helps companies manage data assets, lineage, and metadata
            - Key solutions: Data discovery, governance, collaboration
            
            Analyze responses for:
            1. Sentiment towards Atlan's solution
            2. Intent regarding next steps
            3. Potential fit with Atlan
            
            Format your response exactly as:
            Sentiment: [Positive/Neutral/Negative]
            Intent: [Interested/Need More Info/Follow-Up Required/Not Interested]"""),
            
            HumanMessage(content=f"""Analyze this email response to Atlan's outreach: '{text}'
            
            Respond ONLY with Sentiment and Intent labels exactly as specified.""")
        ]
        
        logger.debug("Sending prompt to AI model")
        response = await AI_MODEL.get_completion(prompt)
        logger.debug(f"Received response from AI model: {response}")

        # Parse the response more robustly
        try:
            lines = response.strip().split('\n')
            sentiment = None
            intent = None
            
            for line in lines:
                if line.startswith('Sentiment:'):
                    sentiment = line.replace('Sentiment:', '').strip()
                elif line.startswith('Intent:'):
                    intent = line.replace('Intent:', '').strip()
            
            if not sentiment or not intent:
                raise ValueError("Missing sentiment or intent in response")
                
            # Validate sentiment
            valid_sentiments = ['Positive', 'Neutral', 'Negative']
            if sentiment not in valid_sentiments:
                sentiment = 'Neutral'  # fallback
                
            # Validate intent
            valid_intents = ['Interested', 'Need More Info', 'Follow-Up Required', 'Not Interested']
            if intent not in valid_intents:
                intent = 'Need More Info'  # fallback
                
            logger.info(f"Successfully extracted sentiment: {sentiment} and intent: {intent}")
            return sentiment, intent
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return 'Neutral', 'Need More Info'  # safe fallback

    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}")
        return 'Neutral', 'Need More Info'  # safe fallback

async def generate_followup_email(recipient, subject, reply_text):
    """AI generates a follow-up email for interested prospects"""
    try:
        logger.info(f"Generating follow-up email for recipient: {recipient}")
        logger.debug(f"Original subject: {subject}")
        
        prompt = [
            SystemMessage(content="You are an AI assistant that generates professional follow-up emails. "
                                "Your responses should be concise, engaging, and appropriate for business communication."),
            HumanMessage(content=f"Generate a professional follow-up email for {recipient}. "
                                f"Their response was: '{reply_text}'. "
                                "If they showed interest in Atlan, send them my calender to schedule a meet https://cal.com/mohdjami. Keep it concise and engaging.")
        ]
        
        logger.debug("Sending prompt to AI model for email generation")
        response = await AI_MODEL.get_completion(prompt)
        logger.debug("Received email response from AI model")

        # Store follow-up email in Supabase
        followup_email = {
            "recipient": recipient,
            "subject": f"Re: {subject}",
            "body": response,
            "status": "draft"
        }
        
        logger.info("Storing follow-up email in Supabase")
        # supabase.table("emails").insert(followup_email).execute()
        logger.info("Successfully stored follow-up email")

        return followup_email

    except Exception as e:
        logger.error(f"Error generating follow-up email: {str(e)}")
        raise
