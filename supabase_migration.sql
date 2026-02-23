-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    company_description TEXT NOT NULL,
    goal TEXT NOT NULL,
    target_job_titles TEXT[] NOT NULL,
    target_industries TEXT[],
    target_company_sizes TEXT[], 
    target_locations TEXT[],
    pain_points TEXT[],
    value_proposition TEXT,
    exclude_keywords TEXT[],
    min_alignment_score DECIMAL DEFAULT 0.7,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create discovery_jobs table
CREATE TABLE IF NOT EXISTS discovery_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    preferences_id UUID REFERENCES user_preferences(id),
    status TEXT NOT NULL, -- 'pending', 'running', 'completed', 'failed'
    total_searched INT DEFAULT 0,
    total_prospects_found INT DEFAULT 0,
    sources_used TEXT[], -- ['serp_api', 'reddit', 'twitter']
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Modify prospects table to add new columns
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'prospects' AND column_name = 'source') THEN
        ALTER TABLE prospects ADD COLUMN source TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'prospects' AND column_name = 'search_query') THEN
        ALTER TABLE prospects ADD COLUMN search_query TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'prospects' AND column_name = 'discovery_job_id') THEN
        ALTER TABLE prospects ADD COLUMN discovery_job_id UUID REFERENCES discovery_jobs(id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'prospects' AND column_name = 'raw_data') THEN
        ALTER TABLE prospects ADD COLUMN raw_data JSONB;
    END IF;
END $$;
