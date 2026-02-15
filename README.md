# AI SDR + Meeting AI + Knowledge Base(code is private)

A comprehensive AI-powered system that integrates multiple AI capabilities to enhance sales and customer relationship management. The platform helps sales teams identify prospects, generate personalized outreach, automate follow-ups, and capture meeting insights.

![System Architecture](https://app.eraser.io/workspace/NjlgvzEzm0bygGKFcO9f?origin=share)

![image](https://github.com/user-attachments/assets/04c0259c-a959-4024-8784-dff9e215e2b1)

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Module Details](#module-details)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Testing the System](#testing-the-system)
- [Deployment](#deployment)
- [Technologies Used](#technologies-used)
- [Contributing](#contributing)
- [License](#license)

## Overview

This system is designed to transform the traditional sales development process by leveraging AI at every stage:

1. **AI Lead Generator & Analyzer**: Scrapes LinkedIn and other platforms to find and analyze potential leads.
2. **Personalized AI Email Generator**: Creates highly personalized emails based on prospect data and pain points.
3. **AI Follow-up & Meeting Scheduler**: Monitors email responses and automates follow-ups.
4. **AI Meeting Notes & Knowledge Base**: Captures, summarizes, and makes searchable all meeting knowledge.

## Architecture

The system uses a modern microservices architecture:

```
├── Frontend (Next.js)
│   ├── Dashboard
│   ├── Prospect Management
│   ├── Email Editor
│   ├── Meeting Management
│   └── Knowledge Search
│
├── Backend (FastAPI)
│   ├── AI SDR Services
│   ├── Meeting AI Services
│   ├── Knowledge Base Services
│   └── Authentication/Authorization
│
├── Storage
│   ├── Supabase (Persistent Storage)
│   ├── Redis (Caching)
│   └── Pinecone (Vector Database)
│
└── External Services
    ├── Groq (LLM Provider)
    ├── MeetingBaaS (Meeting Bot)
    └── Jina AI (Vector Embeddings)
```

## Module Details

### AI SDR Module

The AI SDR module is responsible for finding, analyzing, and engaging with prospects.

#### LinkedIn Service (`agents/services/linkedin_service.py`)

- **Functionality**: Scrapes LinkedIn for potential leads, analyzes posts for pain points, and identifies promising prospects.
- **Key Components**:
  - `LinkedInPublicScraper`: Scrapes LinkedIn content
  - `analyze_posts()`: Extracts insights from posts using LLM
  - `get_prospects()`: Filters and scores leads based on alignment
- **Technologies**: Selenium, BeautifulSoup, Groq LLM

#### Email Service (`agents/services/email_service.py`)

- **Functionality**: Generates personalized email drafts using a multi-stage LangGraph workflow.
- **Key Components**:
  - `build_workflow()`: Creates the email generation state graph
  - `subject_agent()`: Generates compelling subject lines
  - `content_builder_agent()`: Creates initial email content
  - `content_refiner_agent()`: Refines and improves the draft
  - `final_draft_agent()`: Formats the final email
- **Technologies**: LangGraph, Groq LLM

#### Reply Tracker (`agents/services/reply_tracker.py`)

- **Functionality**: Analyzes email responses for sentiment and intent, generates follow-ups.
- **Key Components**:
  - `analyze_sentiment()`: Determines email sentiment and intent
  - `generate_followup_email()`: Creates contextual follow-up emails
  - `GmailService`: Handles Gmail API integration
- **Technologies**: Google Gmail API, Groq LLM

### Meeting AI Module

The Meeting AI module handles meeting participation, transcription, and analysis.

#### Meeting Analyzer (`agents/services/meeting_analyzer.py`)

- **Functionality**: Analyzes meeting transcripts to extract summaries, action items, and insights.
- **Key Components**:
  - `analyze_meeting()`: Processes transcripts to generate structured insights
  - Few-shot examples for consistent output formatting
- **Technologies**: Groq LLM, MeetingBaaS API

#### Meeting Bot Integration (`agents/main.py`)

- **Functionality**: Adds bots to meetings, receives webhooks with transcripts.
- **Key Components**:
  - `/add-bot`: Endpoint to add a bot to a meeting
  - `/webhook`: Receives meeting completion events
  - Meeting status management
- **Technologies**: MeetingBaaS API, FastAPI

### Knowledge Base Module

The Knowledge Base module stores and retrieves meeting knowledge.

#### Vector Service (`agents/services/vector_service.py`)

- **Functionality**: Creates embeddings, stores meeting data, and enables semantic search.
- **Key Components**:
  - `create_embedding()`: Generates vector embeddings using Jina AI
  - `store_meeting_data()`: Chunks and stores meeting content
  - `search_meetings()`: Performs vector similarity search
  - `generate_rag_response()`: Creates RAG-based answers from meetings
- **Technologies**: Pinecone, Jina AI Embeddings, RAG

#### LLM Service (`agents/services/llm_service.py`)

- **Functionality**: Provides a unified interface for LLM interactions.
- **Key Components**:
  - `get_json_response()`: Gets structured JSON responses
  - `get_streaming_response()`: Streams responses for UI
  - `get_completion()`: Gets regular text completions
- **Technologies**: Groq, LangChain

### Frontend Module

The frontend provides a user-friendly interface for the system.

#### Dashboard (`components/dashboard/`)

- **Functionality**: Displays key metrics, recent activities, and insights.
- **Key Components**:
  - `DashboardOverview`: Shows statistics and activity
  - `FollowUps`: Manages email responses
  - `MeetingNotes`: Displays meeting summaries
  - `MeetingSearch`: Searches knowledge base
- **Technologies**: Next.js, Recharts, shadcn/ui

#### Prospect Management (`components/ProspectList.tsx`)

- **Functionality**: Displays and manages prospects found by the AI.
- **Key Components**:
  - `ProspectList`: Lists all prospects with filtering
  - `ProspectCard`: Displays prospect details
  - `ProspectModal`: Shows detailed prospect information
  - `EmailDrafts`: Manages email generation and sending
- **Technologies**: Next.js, shadcn/ui

#### Authentication (`app/(auth)/`)

- **Functionality**: Handles user authentication and authorization.
- **Key Components**:
  - `login/page.tsx`: Login/signup interface
  - `login/actions.ts`: Server actions for auth
  - Supabase integration
- **Technologies**: Next.js, Supabase Auth

## Prerequisites

- Python 3.9+
- Node.js 18+
- Docker and Docker Compose (optional but recommended)
- Supabase account
- Redis instance
- Pinecone account
- Groq API key (or other LLM provider)
- Gmail API credentials (for email monitoring)

## Installation

You can set up this project using Docker Compose (recommended) or manual installation.

### Backend Setup

#### Option 1: Using Docker Compose

1. Clone the repository:
   ```bash
   git clone https://github.com/mohdjami/AI-Sales-development-representative.git
   cd AI-Sales-development-representative/backend
   ```

2. Create environment variables file:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file with your configuration (API keys, database URLs, etc.)

4. Run the Docker Compose:
   ```bash
   docker-compose up -d
   ```

#### Option 2: Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mohdjami/AI-Sales-development-representative.git
   cd AI-Sales-development-representative/backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create environment variables file:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file with your configuration

6. Run Redis (if not using external instance):
   ```bash
   docker run -d -p 6379:6379 redis
   ```

7. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd AI-Sales-development-representative/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create environment variables file:
   ```bash
   cp .env.example .env.local
   ```

4. Edit the `.env.local` file with your configuration (API URL, Supabase keys, etc.)

5. Start the development server:
   ```bash
   npm run dev
   ```

## Configuration

### Required Environment Variables

#### Backend (.env)

```
# FastAPI
PORT=8000

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Pinecone
PINECONE_API_KEY=your-api-key

# LLM Service
GROQ_API_KEY=your-api-key

# LinkedIn Credentials (for scraping)
LINKEDIN_EMAIL=your-email
LINKEDIN_PASSWORD=your-password

# Gmail API
GMAIL_CREDENTIALS=path-to-credentials.json

# Meeting Service
MEETING_API_KEY=your-api-key
```

#### Frontend (.env.local)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## Usage

After installation and configuration, the system will be accessible at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Getting Started

1. **Login to the system** using your Supabase credentials
2. **Generate leads** by going to the Prospects tab and clicking "Find Leads"
3. **Create personalized emails** by selecting a prospect and clicking "Draft Email"
4. **Monitor responses** in the Reply Tracker tab
5. **Schedule meetings** with interested prospects
6. **View meeting transcripts and insights** in the Knowledge Base tab

## Testing the System

You can test the system using the following credentials:

**Login Credentials:**
- Email: jamikhann7@gmail.com
- Password: abcd1234

### Testing Workflow

1. **Login** using the credentials above
2. **Find leads** by going to the Prospects tab
3. **Draft emails** for any prospect you find interesting
4. **Track replies** in the Reply Tracker (demo data will be shown)
5. **Schedule meetings** and add bots to test the transcription feature

> **Note**: When adding a meeting bot, please be patient as it takes approximately 1 minute for the bot to join the meeting and begin processing.

### Test Meetings

For testing the meeting bot feature, you can use the following steps:

1. Create a Zoom/Google Meet/Microsoft Teams meeting
2. On the Meetings tab, click "Add Bot to Meeting"
3. Paste your meeting URL and provide a title
4. Click "Add Bot" and wait approximately 1 minute for the bot to join
5. You'll receive a notification once the bot has successfully joined
6. Conduct your meeting as normal
7. After the meeting, transcripts and insights will be available in the Knowledge Base

## Deployment

### Frontend (Vercel)

1. Push your code to GitHub
2. Connect your repository to Vercel
3. Configure environment variables
4. Deploy

### Backend (Railway)

1. Push your code to GitHub
2. Connect your repository to Railway
3. Configure environment variables
4. Set the start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Deploy

## Technologies Used

### Backend

- **FastAPI**: Web framework for building APIs
- **LangChain**: Framework for LLM applications
- **LangGraph**: State machines for LLM workflows
- **Groq**: LLM provider for text generation
- **Selenium & BeautifulSoup**: Web scraping
- **Pinecone**: Vector database for embeddings
- **Jina AI**: Embedding model provider
- **Redis**: Caching and temporary storage
- **Supabase**: PostgreSQL database and authentication

### Frontend

- **Next.js 15**: React framework with App Router
- **TypeScript**: Typed JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Component library
- **Recharts**: Charting library
- **Sonner**: Toast notifications
- **React Hook Form**: Form handling

### DevOps

- **Docker**: Containerization
- **Railway**: Backend deployment
- **Vercel**: Frontend deployment

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

For questions or support, please contact [mohdjamikhann@gmail.com](mailto:mohdjamikhann@gmail.com).
