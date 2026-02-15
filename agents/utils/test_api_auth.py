import asyncio
import os
import sys
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
import random
import string

# Add parent directory to path to allow imports if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env vars
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))
# Also try loading from .env.local if .env didn't have what we need
if not os.getenv("SUPABASE_URL"):
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env.local'))

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("SUPABASE_URL or SUPABASE_KEY not found in environment variables")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_random_email():
    return f"test_user_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}@example.com"

async def test_api_auth():
    email = "mohdjamikhann@gmail.com"
    password = "SafePassword123!"
    
    logger.info(f"Creating test user: {email}")
    
    access_token = None
    try:
        # 1. Try Sign In first
        logger.info(f"Attempting to sign in user: {email}")
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
        except Exception as e:
             logger.info(f"Sign in failed ({e}), trying sign up")
             auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

        session = auth_response.session
        if session:
             access_token = session.access_token
             user_id = auth_response.user.id
             logger.info(f"Got access token for user {user_id}")
        else:
             logger.warning("Could not get access token (Signup/Signin failed or disabled). Skipping VALID token test.")

    except Exception as e:
        logger.warning(f"Signup/Signin failed: {e}. Skipping VALID token test.")

    # 2. Test API endpoint
    try:
        async with httpx.AsyncClient() as client:
            url = "http://localhost:8000/search-knowledge-base"
            payload = {
                "query": "test query",
                "max_results": 1
            }
            
            # A. Valid Token (Only if we have one)
            if access_token:
                logger.info("Testing with VALID token...")
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info("✅ Request with valid token succeeded")
                else:
                    logger.error(f"❌ Request with valid token failed: {response.status_code} {response.text}")

            # B. No Token
            logger.info("Testing with NO token...")
            response_no_token = await client.post(
                url,
                json=payload,
                headers={},
                timeout=10.0
            )
            
            # 403 Forbidden or 401 Unauthorized are acceptable for missing auth
            if response_no_token.status_code in [401, 403]:
                logger.info(f"✅ Request with no token correctly rejected: {response_no_token.status_code}")
            else:
                logger.error(f"❌ Request with no token should have failed but got: {response_no_token.status_code}")

            # C. Invalid Token
            logger.info("Testing with INVALID token...")
            response_invalid = await client.post(
                url,
                json=payload,
                headers={"Authorization": "Bearer invalid_token_123"},
                timeout=10.0
            )
            
            if response_invalid.status_code in [401, 403]:
                logger.info(f"✅ Request with invalid token correctly rejected: {response_invalid.status_code}")
            else:
                logger.error(f"❌ Request with invalid token should have failed but got: {response_invalid.status_code}")

    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_auth())
