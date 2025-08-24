-- Migration script to safely add new fields to existing NeuraVia database
-- This script can be run on existing databases without losing data

-- Add name column to user_profiles table
ALTER TABLE public.user_profiles ADD COLUMN IF NOT EXISTS name TEXT;

-- Add assessment_complete column to chat_sessions table
ALTER TABLE public.chat_sessions ADD COLUMN IF NOT EXISTS assessment_complete BOOLEAN DEFAULT FALSE;

-- Add new fields to chat_sessions table if they don't exist
DO $$ 
BEGIN
    -- Add assessment_complete column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'chat_sessions' AND column_name = 'assessment_complete') THEN
        ALTER TABLE public.chat_sessions ADD COLUMN assessment_complete BOOLEAN DEFAULT FALSE;
    END IF;
    
    -- Add completion_score column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'chat_sessions' AND column_name = 'completion_score') THEN
        ALTER TABLE public.chat_sessions ADD COLUMN completion_score INTEGER DEFAULT 0;
        -- Add constraint after adding column
        ALTER TABLE public.chat_sessions ADD CONSTRAINT check_completion_score 
            CHECK (completion_score >= 0 AND completion_score <= 100);
    END IF;
END $$;

-- Add new fields to patient_reports table if they don't exist
DO $$ 
BEGIN
    -- Add user_context column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'patient_reports' AND column_name = 'user_context') THEN
        ALTER TABLE public.patient_reports ADD COLUMN user_context JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Create new indexes if they don't exist
DO $$ 
BEGIN
    -- Add chat_sessions user_id index if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_chat_sessions_user_id') THEN
        CREATE INDEX idx_chat_sessions_user_id ON public.chat_sessions(user_id);
    END IF;
    
    -- Add chat_sessions is_active index if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_chat_sessions_is_active') THEN
        CREATE INDEX idx_chat_sessions_is_active ON public.chat_sessions(is_active);
    END IF;
END $$;

-- Update existing sessions to have default values
UPDATE public.chat_sessions 
SET assessment_complete = COALESCE(assessment_complete, FALSE),
    completion_score = COALESCE(completion_score, 0)
WHERE assessment_complete IS NULL OR completion_score IS NULL;

-- Update existing reports to have default user_context
UPDATE public.patient_reports 
SET user_context = COALESCE(user_context, '{}'::jsonb)
WHERE user_context IS NULL;

-- Grant permissions to all users (hackathon mode)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO anon;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Migration script to add missing chat_locked column
-- This script is safe to run on existing databases

-- Add chat_locked column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chat_sessions' 
        AND column_name = 'chat_locked'
    ) THEN
        ALTER TABLE public.chat_sessions 
        ADD COLUMN chat_locked BOOLEAN DEFAULT FALSE;
        
        RAISE NOTICE 'Added chat_locked column to chat_sessions table';
    ELSE
        RAISE NOTICE 'chat_locked column already exists in chat_sessions table';
    END IF;
END $$;

-- Update existing sessions to have chat_locked = false
UPDATE public.chat_sessions 
SET chat_locked = FALSE 
WHERE chat_locked IS NULL;
