import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

logger = logging.getLogger(__name__)

# Google OAuth Config
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Add this for backend services


class GoogleService:
    """Handles Google OAuth, Gmail, and Calendar operations per user."""

    def __init__(self):
        # Use service role key for backend operations (bypasses RLS)
        key = SUPABASE_SERVICE_ROLE_KEY if SUPABASE_SERVICE_ROLE_KEY else SUPABASE_ANON_KEY
        self.supabase: Client = create_client(SUPABASE_URL, key)

    # ── OAuth Flow ──────────────────────────────────────────────

    def get_auth_url(self, state: str = "") -> str:
        """Generate the Google OAuth consent URL."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
                }
            },
            scopes=SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )
        return auth_url

    async def exchange_code(self, code: str, user_id: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens and store them."""
        print(f"\n[GoogleService] exchange_code called for user: {user_id}")
        
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [GOOGLE_REDIRECT_URI],
                    }
                },
                scopes=SCOPES,
                redirect_uri=GOOGLE_REDIRECT_URI,
            )
            print("[GoogleService] Flow created successfully")
            
            flow.fetch_token(code=code)
            print("[GoogleService] Token fetched successfully")
            
            credentials = flow.credentials
            print(f"[GoogleService] Got credentials, has refresh_token: {credentials.refresh_token is not None}")

            # Get the user's email from Gmail profile
            service = build("gmail", "v1", credentials=credentials)
            profile = service.users().getProfile(userId="me").execute()
            email = profile.get("emailAddress", "")
            print(f"[GoogleService] Got Gmail profile for: {email}")

            # Store tokens in Supabase (upsert)
            token_data = {
                "user_id": user_id,
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_expiry": credentials.expiry.isoformat() if credentials.expiry else None,
                "scopes": list(credentials.scopes) if credentials.scopes else SCOPES,
                "email": email,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            print(f"[GoogleService] Prepared token_data: user_id={user_id}, email={email}")

            result = self.supabase.table("google_tokens").upsert(
                token_data, on_conflict="user_id"
            ).execute()
            print(f"[GoogleService] Supabase upsert result: {result}")

            logger.info(f"Stored Google tokens for user {user_id} ({email})")
            print(f"[GoogleService] SUCCESS - Tokens stored for {email}")
            return {"email": email, "connected": True}
        
        except Exception as e:
            print(f"\n[GoogleService] ERROR in exchange_code:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            raise

    async def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """Retrieve and refresh Google credentials for a user."""
        result = (
            self.supabase.table("google_tokens")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        if not result.data:
            return None

        token_row = result.data[0]
        creds = Credentials(
            token=token_row["access_token"],
            refresh_token=token_row["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=token_row.get("scopes", SCOPES),
        )

        # Set expiry
        if token_row.get("token_expiry"):
            creds.expiry = datetime.fromisoformat(
                token_row["token_expiry"].replace("Z", "+00:00")
            ).replace(tzinfo=None)

        # Refresh if expired
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Update stored tokens
                self.supabase.table("google_tokens").update(
                    {
                        "access_token": creds.token,
                        "token_expiry": creds.expiry.isoformat() if creds.expiry else None,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                ).eq("user_id", user_id).execute()
                logger.info(f"Refreshed Google token for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to refresh Google token for {user_id}: {e}")
                return None

        return creds

    async def get_connection_status(self, user_id: str) -> Dict[str, Any]:
        """Check if a user has connected their Google account."""
        result = (
            self.supabase.table("google_tokens")
            .select("email, scopes, updated_at")
            .eq("user_id", user_id)
            .execute()
        )

        if not result.data:
            return {"connected": False}

        return {
            "connected": True,
            "email": result.data[0].get("email"),
            "scopes": result.data[0].get("scopes", []),
            "last_refreshed": result.data[0].get("updated_at"),
        }

    async def disconnect(self, user_id: str) -> bool:
        """Remove a user's Google tokens."""
        self.supabase.table("google_tokens").delete().eq(
            "user_id", user_id
        ).execute()
        logger.info(f"Disconnected Google account for user {user_id}")
        return True

    # ── Gmail Operations ────────────────────────────────────────

    async def send_email(
        self,
        user_id: str,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
    ) -> Dict[str, Any]:
        """Send an email via Gmail API."""
        creds = await self.get_credentials(user_id)
        if not creds:
            raise ValueError("Google account not connected. Please connect first.")

        service = build("gmail", "v1", credentials=creds)

        message = MIMEMultipart("alternative")
        message["to"] = to
        message["subject"] = subject

        content_type = "html" if html else "plain"
        message.attach(MIMEText(body, content_type))

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        sent = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )

        logger.info(f"Email sent to {to}, message ID: {sent['id']}")
        return {
            "message_id": sent["id"],
            "thread_id": sent.get("threadId", ""),
        }

    async def list_messages(
        self,
        user_id: str,
        query: str = "in:inbox",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """List Gmail messages matching a query."""
        creds = await self.get_credentials(user_id)
        if not creds:
            raise ValueError("Google account not connected.")

        service = build("gmail", "v1", credentials=creds)

        result = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )

        messages = []
        for msg_ref in result.get("messages", []):
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_ref["id"], format="full")
                .execute()
            )
            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

            # Extract body
            body_text = self._extract_body(msg["payload"])

            messages.append(
                {
                    "id": msg["id"],
                    "threadId": msg.get("threadId", ""),
                    "from": headers.get("From", ""),
                    "to": headers.get("To", ""),
                    "subject": headers.get("Subject", ""),
                    "date": headers.get("Date", ""),
                    "snippet": msg.get("snippet", ""),
                    "body": body_text,
                    "labelIds": msg.get("labelIds", []),
                }
            )

        return messages

    async def get_replies_for_sent_emails(
        self, user_id: str, max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Get replies to emails we've sent (threads with SENT + INBOX)."""
        creds = await self.get_credentials(user_id)
        if not creds:
            raise ValueError("Google account not connected.")

        service = build("gmail", "v1", credentials=creds)

        # Find threads where we sent an email and got a reply
        result = (
            service.users()
            .messages()
            .list(
                userId="me",
                q="in:inbox is:unread",
                maxResults=max_results,
            )
            .execute()
        )

        replies = []
        for msg_ref in result.get("messages", []):
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_ref["id"], format="full")
                .execute()
            )
            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            body_text = self._extract_body(msg["payload"])

            replies.append(
                {
                    "id": msg["id"],
                    "threadId": msg.get("threadId", ""),
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", ""),
                    "date": headers.get("Date", ""),
                    "body": body_text,
                    "snippet": msg.get("snippet", ""),
                }
            )

        return replies

    def _extract_body(self, payload: Dict) -> str:
        """Extract text body from Gmail message payload."""
        if "body" in payload and payload["body"].get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and part["body"].get("data"):
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8"
                    )
                if part["mimeType"] == "text/html" and part["body"].get("data"):
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8"
                    )
                # Nested parts
                if "parts" in part:
                    result = self._extract_body(part)
                    if result:
                        return result
        return ""

    # ── Calendar Operations ─────────────────────────────────────

    async def list_events(
        self,
        user_id: str,
        max_results: int = 10,
        time_min: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List upcoming Google Calendar events."""
        creds = await self.get_credentials(user_id)
        if not creds:
            raise ValueError("Google account not connected.")

        service = build("calendar", "v3", credentials=creds)

        if not time_min:
            time_min = datetime.now(timezone.utc).isoformat()

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = []
        for event in events_result.get("items", []):
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            events.append(
                {
                    "id": event["id"],
                    "summary": event.get("summary", ""),
                    "description": event.get("description", ""),
                    "start": start,
                    "end": end,
                    "location": event.get("location", ""),
                    "htmlLink": event.get("htmlLink", ""),
                    "attendees": [
                        {"email": a.get("email"), "status": a.get("responseStatus")}
                        for a in event.get("attendees", [])
                    ],
                }
            )

        return events

    async def create_event(
        self,
        user_id: str,
        summary: str,
        start_time: str,
        end_time: str,
        description: str = "",
        attendees: Optional[List[str]] = None,
        location: str = "",
    ) -> Dict[str, Any]:
        """Create a Google Calendar event."""
        creds = await self.get_credentials(user_id)
        if not creds:
            raise ValueError("Google account not connected.")

        service = build("calendar", "v3", credentials=creds)

        event = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {"dateTime": start_time, "timeZone": "UTC"},
            "end": {"dateTime": end_time, "timeZone": "UTC"},
            "conferenceData": {
                "createRequest": {
                    "requestId": f"meet-{datetime.now().timestamp()}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }

        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        created = (
            service.events()
            .insert(
                calendarId="primary",
                body=event,
                conferenceDataVersion=1,
                sendUpdates="all",
            )
            .execute()
        )

        logger.info(f"Created calendar event: {created['id']}")
        return {
            "id": created["id"],
            "summary": created.get("summary", ""),
            "htmlLink": created.get("htmlLink", ""),
            "start": created["start"].get("dateTime", ""),
            "end": created["end"].get("dateTime", ""),
            "meetLink": created.get("hangoutLink", ""),
        }
