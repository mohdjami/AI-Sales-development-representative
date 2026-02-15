from pydantic import BaseModel
from typing import List, Optional

class Post(BaseModel):
    author: str
    role: Optional[str]
    company: str
    post: str
    keyword: str
    profile_url: Optional[str] = None
    username: Optional[str] = None

class SearchRequest(BaseModel):
    keywords: List[str]
    page: int = 1
    limit: int = 10

class SearchResponse(BaseModel):
    status: str
    message: str
    posts: List[Post] 