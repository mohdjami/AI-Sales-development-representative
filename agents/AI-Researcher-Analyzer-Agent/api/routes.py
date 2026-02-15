from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List

from services.scraper_service import ScraperService
from models.schemas import SearchRequest, SearchResponse, Post
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search_posts(request: SearchRequest) -> SearchResponse:
    """
    Search LinkedIn posts based on keywords
    """
    try:
        logger.info(f"Received search request for keywords: {request.keywords}")
        scraper = ScraperService()
        posts = await scraper.search_posts(
            keywords=request.keywords,
            page=request.page,
            limit=request.limit
        )
        
        return SearchResponse(
            status="success",
            message=f"Found {len(posts)} posts",
            posts=posts
        )

    except Exception as e:
        logger.error(f"Error in search_posts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 