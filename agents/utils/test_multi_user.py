import asyncio
import os
import sys
import logging
import time
from pinecone import Pinecone
from datetime import datetime
from dotenv import load_dotenv

# Load env immediately
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.vector_service import VectorService
from core.logger import logger

async def test_multi_user_isolation():
    # Pre-check index dimensions
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = "meetings-index"
    target_dim = 1536 # OpenAI text-embedding-3-small
    
    if pc.has_index(index_name):
        idx_desc = pc.describe_index(index_name)
        if hasattr(idx_desc, 'dimension') and idx_desc.dimension != target_dim:
            logger.warning(f"Index dimension mismatch (Found: {idx_desc.dimension}, Expected: {target_dim}). Deleting index...")
            pc.delete_index(index_name)
            time.sleep(20) # Wait for deletion to propagate
        elif hasattr(idx_desc, 'spec') and hasattr(idx_desc.spec, 'dimension') and idx_desc.spec.dimension != target_dim: # Handle different response structures
             logger.warning(f"Index dimension mismatch. Deleting index...")
             pc.delete_index(index_name)
             time.sleep(20)

    # Initialize service (will recreate index if missing)
    vector_service = VectorService()
    
    # Wait for index to be ready
    logger.info("Waiting for index to be ready...")
    while True:
        try:
            desc = pc.describe_index(index_name)
            is_ready = False
            if hasattr(desc, 'status'):
                status = desc.status
                if isinstance(status, dict):
                     is_ready = status.get('ready', False)
                else: 
                     is_ready = getattr(status, 'ready', False)
            
            if is_ready:
                logger.info("Index is ready!")
                break
        except Exception as e:
            logger.warning(f"Error checking index status: {e}")
        
        time.sleep(2)
    
    # Define test users
    user_a = "user_test_A"
    user_b = "user_test_B"
    
    # Define test meetings
    # --- Meeting A (User A) ---
    meeting_a = {
        "id": "meet_A_123",
        "title": "Project Alpha Sync",
        "date": "2026-02-15T10:00:00Z",
        "participants": ["Alice", "Bob"],
        "summary": "Alice and Bob discussed the timeline for Project Alpha. Bob raised concerns about the database migration.",
        "transcript": "Alice: How is Project Alpha going?\nBob: It's good, but the database migration is tricky.\nAlice: We need to fix that.",
        "action_items": ["Bob to check migration logs"],
        "topics": ["Project Alpha", "Database"],
        "insights": ["Migration is a risk"]
    }

    # --- Meeting B (User B) ---
    meeting_b = {
        "id": "meet_B_456",
        "title": "Marketing Weekly",
        "date": "2026-02-15T11:00:00Z",
        "participants": ["Charlie", "Dana"],
        "summary": "Charlie and Dana reviewed the Q3 marketing budget. Dana suggested increasing ad spend.",
        "transcript": "Charlie: Let's look at the budget.\nDana: We need more for ads.\nCharlie: Agreed.",
        "action_items": ["Dana to update budget"],
        "topics": ["Marketing", "Budget"],
        "insights": ["Ad spend increase needed"]
    }
    
    print("Storing Meeting A for user_test_A...")
    await vector_service.store_meeting_data(meeting_a, user_id=user_a)
    
    print("Storing Meeting B for user_test_B...")
    await vector_service.store_meeting_data(meeting_b, user_id=user_b)
    
    print("Waiting 10 seconds for indexing...")
    await asyncio.sleep(10)
    
    # --- Verification ---
    print("\n--- Test 1: Search as User A (Query: 'database') ---")
    results_a = await vector_service.search_meetings("database", user_id=user_a, top_k=5)
    
    found_a_in_a = any(m['metadata'].get('meeting_id') == 'meet_A_123' for m in results_a)
    found_b_in_a = any(m['metadata'].get('meeting_id') == 'meet_B_456' for m in results_a)
    
    print(f"Found Meeting A: {found_a_in_a}")
    print(f"Found Meeting B: {found_b_in_a}")
    
    assert found_a_in_a, "User A should see Meeting A"
    assert not found_b_in_a, "User A should NOT see Meeting B"
    print("✅ Test 1 PASSED: User A sees only their own data.")

    print("\n--- Test 2: Search as User B (Query: 'budget') ---")
    results_b = await vector_service.search_meetings("budget", user_id=user_b, top_k=5)
    
    found_a_in_b = any(m['metadata']['meeting_id'] == 'meet_A_123' for m in results_b)
    found_b_in_b = any(m['metadata']['meeting_id'] == 'meet_B_456' for m in results_b)
    
    print(f"Found Meeting A: {found_a_in_b}")
    print(f"Found Meeting B: {found_b_in_b}")
    
    assert found_b_in_b, "User B should see Meeting B"
    assert not found_a_in_b, "User B should NOT see Meeting A"
    print("✅ Test 2 PASSED: User B sees only their own data.")
    
    print("\n--- Test 3: Search as User A with Meeting ID Filter ---")
    # Search for something generic but filter by Meeting A ID
    results_filter = await vector_service.search_meetings("project", user_id=user_a, meeting_id="meet_A_123", top_k=5)
    assert len(results_filter) > 0, "Should find results with filter"
    assert all(m['metadata']['meeting_id'] == 'meet_A_123' for m in results_filter), "All results must match meeting ID"
    print("✅ Test 3 PASSED: Meeting ID filter works.")

if __name__ == "__main__":
    asyncio.run(test_multi_user_isolation())
