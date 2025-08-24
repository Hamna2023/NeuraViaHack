-- Safe Migration Script for NeuraVia
-- This script safely adds missing columns without affecting existing data
-- Run this AFTER running the main schema to ensure compatibility

-- Check if detailed_results column exists in hearing_tests, add if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'hearing_tests' 
        AND column_name = 'detailed_results'
    ) THEN
        ALTER TABLE public.hearing_tests ADD COLUMN detailed_results JSONB DEFAULT '{}'::jsonb;
        RAISE NOTICE 'Added detailed_results column to hearing_tests table';
    ELSE
        RAISE NOTICE 'detailed_results column already exists in hearing_tests table';
    END IF;
END $$;

-- Check if session_id column exists in chat_messages, add if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chat_messages' 
        AND column_name = 'session_id'
    ) THEN
        ALTER TABLE public.chat_messages ADD COLUMN session_id UUID;
        RAISE NOTICE 'Added session_id column to chat_messages table';
    ELSE
        RAISE NOTICE 'session_id column already exists in chat_messages table';
    END IF;
END $$;

-- Check if session_id column exists in chat_sessions, add if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chat_sessions' 
        AND column_name = 'session_id'
    ) THEN
        ALTER TABLE public.chat_sessions ADD COLUMN session_id UUID;
        RAISE NOTICE 'Added session_id column to chat_sessions table';
    ELSE
        RAISE NOTICE 'session_id column already exists in chat_sessions table';
    END IF;
END $$;

-- Check if metadata column exists in chat_messages, add if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chat_messages' 
        AND column_name = 'metadata'
    ) THEN
        ALTER TABLE public.chat_messages ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;
        RAISE NOTICE 'Added metadata column to chat_messages table';
    ELSE
        RAISE NOTICE 'metadata column already exists in chat_messages table';
    END IF;
END $$;

-- Check if updated_at columns exist, add if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_profiles' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE public.user_profiles ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        RAISE NOTICE 'Added updated_at column to user_profiles table';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'symptoms' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE public.symptoms ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        RAISE NOTICE 'Added updated_at column to symptoms table';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chat_sessions' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE public.chat_sessions ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        RAISE NOTICE 'Added updated_at column to chat_sessions table';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'patient_reports' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE public.patient_reports ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        RAISE NOTICE 'Added updated_at column to patient_reports table';
    END IF;
END $$;

-- Create missing indexes safely
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON public.chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON public.chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON public.chat_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_hearing_tests_user_id ON public.hearing_tests(user_id);
CREATE INDEX IF NOT EXISTS idx_symptoms_user_id ON public.symptoms(user_id);
CREATE INDEX IF NOT EXISTS idx_symptoms_created_at ON public.symptoms(created_at);
CREATE INDEX IF NOT EXISTS idx_patient_reports_user_id ON public.patient_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_patient_reports_session_id ON public.patient_reports(session_id);
CREATE INDEX IF NOT EXISTS idx_patient_reports_created_at ON public.patient_reports(created_at);

-- Disable RLS for hackathon mode (safe to run multiple times)
ALTER TABLE public.user_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.hearing_tests DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.symptoms DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_reports DISABLE ROW LEVEL SECURITY;

-- Grant permissions (safe to run multiple times)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO anon;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Create or replace the timestamp update function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers safely (will fail if already exist, but that's okay)
DO $$ 
BEGIN
    -- Drop existing triggers if they exist
    DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON public.user_profiles;
    DROP TRIGGER IF EXISTS update_symptoms_updated_at ON public.symptoms;
    DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON public.chat_sessions;
    DROP TRIGGER IF EXISTS update_patient_reports_updated_at ON public.patient_reports;
    
    -- Create new triggers
    CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON public.user_profiles
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    CREATE TRIGGER update_symptoms_updated_at BEFORE UPDATE ON public.symptoms
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON public.chat_sessions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    CREATE TRIGGER update_patient_reports_updated_at BEFORE UPDATE ON public.patient_reports
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    RAISE NOTICE 'All triggers created successfully';
END $$;

RAISE NOTICE 'Migration completed successfully! All tables are now compatible with the new schema.';
