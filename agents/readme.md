# AI SDR + Meeting AI + Knowledge Base System Design

## System Overview

Based on your requirements and the provided architecture diagram, I'll outline a comprehensive system design for an AI-powered sales development representative (SDR) system integrated with meeting tools and a knowledge base.

The system consists of four main components:
1. **AI Lead Generator & Analyzer**
2. **Personalized AI Email Generator**
3. **AI Follow-up & Meeting Scheduler**
4. **AI Meeting Notes & Knowledge Base**

Let's explore each component in detail, including the tech stack and architecture decisions.

## Architecture Diagram

## 1. AI Lead Generator & Analyzer

This component is responsible for finding and analyzing potential prospects from LinkedIn and other sources.

### Key Features:
- LinkedIn profile and post scraping
- Prospect analysis and qualification
- Pain point extraction and solution matching
- Storing prospect data

### Technical Implementation:

**Backend Services:**
```
/linkedin_service.py - LinkedIn data scraping and analysis
/linkedin_scraper.py - Selenium-based web scraper for LinkedIn
```

**APIs:**
```
GET /prospects - Fetch qualified prospects
GET /analyze - Analyze LinkedIn posts
```

**Data Flow:**
1. LinkedIn scraper collects posts and profiles
2. LLM analyzes content to identify pain points and fit
3. Qualified prospects are stored in Redis (cache) and Supabase (persistent)
4. Frontend displays prospects with AI-generated insights

**Key Code Components:**

The `LinkedInService` class handles scraping and analysis:
- Uses Selenium for web scraping
- Analyzes posts with the LLM service
- Calculates alignment scores to identify high-quality prospects
- Stores results in Redis for quick access

```python
# Key logic in analyze_posts method
async def analyze_posts(self):
    if self.posts is None:
        self.posts = await self._load_posts()
                
    insights = []
    
    for post in self.posts:
        # Use LLM service to analyze the post
        ai_analysis = await self.llm_service.get_json_response(
            system_prompt="You are an AI expert at analyzing LinkedIn posts...",
            user_prompt=f"Analyze this LinkedIn post for Atlan prospecting...",
            json_structure=json_structure
        )
        
        insights.append({
            "author": post["author"],
            "role": post.get("role", "Unknown"),
            "company": post["company"],
            "post": post["post"],
            "analysis": ai_analysis
        })
    
    return {"analyzed_posts": insights}
```

## 2. Personalized AI Email Generator

This component generates personalized email content based on prospect data and pain points.

### Key Features:
- Multi-step email drafting workflow
- Personalization based on prospect data
- Content refinement and optimization
- A/B testing capabilities (future)

### Technical Implementation:

**Backend Services:**
```
/email_service.py - Email generation and workflow
/llm_service.py - LLM integration for content generation
```

**APIs:**
```
POST /draft-emails - Generate email draft for a prospect
POST /send-email - Store and send drafted email
```

**Data Flow:**
1. Frontend sends prospect data to email generator
2. Email service processes through a multi-step workflow:
   - Subject line creation
   - Content building
   - Content refinement
   - Final formatting
3. Final email draft is returned to frontend
4. User can edit and send the email
5. Email is stored in Supabase for tracking

**Key Code Components:**

The `EmailService` uses a state graph workflow to generate personalized emails:
```python
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
```

Each agent (subject, content builder, refiner, final draft) uses LLM prompts tailored to its specific task.

## 3. AI Follow-up & Meeting Scheduler

This component monitors email responses, analyzes sentiment, and generates appropriate follow-ups.

### Key Features:
- Gmail integration for monitoring responses
- Sentiment and intent analysis
- Automated follow-up generation
- Meeting scheduling assistance

### Technical Implementation:

**Backend Services:**
```
/track_replies.py - Gmail reply monitoring
/reply_tracker.py - Reply analysis tools
```

**APIs:**
```
GET /track-replies - Fetch and analyze new email replies
```

**Data Flow:**
1. System fetches new replies from Gmail
2. LLM analyzes sentiment and intent
3. Follow-up suggestions are generated based on analysis
4. Results are stored in Redis and displayed in frontend
5. User can send suggested follow-ups

**Key Code Components:**

The sentiment analysis function:
```python
async def analyze_sentiment(body):
    """Analyze the sentiment and intent of an email reply"""
    # Implementation with LLM
    sentiment = "Positive"  # Example result
    intent = "Follow-Up Required"  # Example result
    return sentiment, intent
```

## 4. AI Meeting Notes & Knowledge Base

This component handles meeting transcription, summarization, and knowledge management.

### Key Features:
- Meeting bot integration
- Automated transcription and summarization
- Action item extraction
- Vector database for knowledge storage and retrieval

### Technical Implementation:

**Backend Services:**
```
/meeting_analyzer.py - Meeting analysis tools
/vector_service.py - Vector database integration
```

**APIs:**
```
POST /add-bot - Add bot to meeting and store details
POST /webhook - Receive meeting data from third-party service
```

**Data Flow:**
1. Meeting bot joins meetings via API
2. Transcripts are processed by meeting analyzer
3. Key insights are extracted and summarized
4. Meeting data is stored in vector database (Pinecone)
5. Users can search and retrieve meeting knowledge

**Key Code Components:**

The `MeetingAnalyzer` processes meeting transcripts:
```python
async def analyze_meeting(self, transcript: str, meeting_info: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze meeting transcript and generate insights"""
    # Construct the system prompt
    system_prompt = """You are an AI meeting analyzer. Your task is to:
    1. Create a concise summary of the meeting.
    2. Extract key action items and decisions.
    3. Identify main topics discussed.
    4. Highlight important insights.
    5. Format the transcript for better readability."""

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
```

The `VectorService` stores and retrieves meeting data:
```python
async def store_meeting_data(self, meeting_data: Dict[str, Any]):
    """Store meeting data in Pinecone"""
    # Create embeddings for different parts of the meeting
    transcript_embedding = await self.create_embedding(meeting_data["transcript"])
    
    # Prepare metadata
    metadata = {
        "meeting_id": meeting_data["id"],
        "title": meeting_data["title"],
        "date": meeting_data["date"],
        "participants": meeting_data["participants"],
        "summary": meeting_data.get("ai_summary", ""),
        "transcript": meeting_data["transcript"]
    }

    # Store in Pinecone
    self.index.upsert(
        vectors=[
            {
                "id": f"meeting_{meeting_data['id']}",
                "values": transcript_embedding,
                "metadata": metadata
            }
        ]
    )
```

## 5. Database & Storage Layer

The system uses multiple storage solutions for different needs:

### Supabase
- User authentication and management
- Persistent storage for prospects, emails, meetings
- Relational data with PostgreSQL

### Redis
- Caching for fast access to frequently needed data
- Temporary storage for analysis results
- Sessions and rate limiting

### Pinecone
- Vector storage for semantic search
- Meeting transcript embeddings
- Knowledge base search functionality

## 6. Frontend (Next.js)

The frontend will be built with Next.js, providing a modern and responsive interface.

### Key Pages:
- Dashboard with prospect analytics
- Prospect list and details
- Email editor with AI suggestions
- Reply monitoring and follow-up interface
- Meeting calendar and scheduler
- Knowledge base search and browsing

### API Integration:
- Direct integration with FastAPI backend
- Real-time updates with WebSockets
- Authentication with Supabase

## 7. Deployment Architecture

### Deployment Considerations:

1. **Frontend**: Deploy Next.js application on Vercel or Netlify for optimal performance and easy CI/CD.

2. **Backend**: Deploy FastAPI in containerized environment using Docker and Kubernetes for scalability.

3. **Database Services**:
   - Supabase: Managed PostgreSQL service
   - Redis: In-memory cache with persistence
   - Pinecone: Vector database for embeddings

4. **Scalability**:
   - Use horizontal scaling for FastAPI backend
   - Implement caching strategies with Redis
   - Optimize database queries and indexing

5. **Security**:
   - Implement JWT authentication with Supabase
   - Use HTTPS for all communications
   - Set up proper CORS policies
   - Implement rate limiting
