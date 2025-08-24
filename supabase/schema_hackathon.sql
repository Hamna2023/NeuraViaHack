-- NeuraVia Hackathon Schema - Simplified for Development
-- This schema removes strict security policies for easier development

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (independent of Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    age INTEGER,
    gender TEXT CHECK (gender IN ('male', 'female', 'nonbinary', 'prefer_not_say')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat sessions table for better conversation management
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    session_name TEXT DEFAULT 'Chat Session',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    assessment_complete BOOLEAN DEFAULT FALSE,
    completion_score INTEGER DEFAULT 0 CHECK (completion_score >= 0 AND completion_score <= 100),
    chat_locked BOOLEAN DEFAULT FALSE
);

-- Chat messages table (FIXED: includes session_id)
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    message TEXT NOT NULL,
    response TEXT,
    is_doctor BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id UUID REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Hearing tests table
CREATE TABLE IF NOT EXISTS public.hearing_tests (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    test_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    left_ear_score INTEGER CHECK (left_ear_score >= 0 AND left_ear_score <= 100),
    right_ear_score INTEGER CHECK (right_ear_score >= 0 AND right_ear_score <= 100),
    overall_score INTEGER CHECK (overall_score >= 0 AND overall_score <= 100),
    test_type TEXT DEFAULT 'standard',
    notes TEXT,
    detailed_results JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Symptoms table
CREATE TABLE IF NOT EXISTS public.symptoms (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    symptom_name TEXT NOT NULL,
    severity INTEGER CHECK (severity >= 1 AND severity <= 10),
    description TEXT,
    duration_days INTEGER,
    location TEXT,
    triggers TEXT[],
    alleviators TEXT[],
    associated_symptoms TEXT[],
    impact_on_daily_life TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Patient Reports table for comprehensive medical reports
CREATE TABLE IF NOT EXISTS public.patient_reports (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE NOT NULL,
    session_id UUID REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    report_title TEXT NOT NULL,
    executive_summary TEXT,
    symptom_analysis TEXT,
    risk_assessment TEXT,
    hearing_assessment_summary TEXT,
    recommendations TEXT,
    follow_up_actions TEXT,
    collected_data JSONB DEFAULT '{}'::jsonb,
    hearing_results JSONB DEFAULT '{}'::jsonb,
    user_context JSONB DEFAULT '{}'::jsonb,
    assessment_stage TEXT DEFAULT 'initial',
    is_complete BOOLEAN DEFAULT FALSE,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON public.chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON public.chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON public.chat_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_hearing_tests_user_id ON public.hearing_tests(user_id);
CREATE INDEX IF NOT EXISTS idx_symptoms_user_id ON public.symptoms(user_id);
CREATE INDEX IF NOT EXISTS idx_symptoms_created_at ON public.symptoms(created_at);
CREATE INDEX IF NOT EXISTS idx_patient_reports_user_id ON public.patient_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_patient_reports_session_id ON public.patient_reports(session_id);
CREATE INDEX IF NOT EXISTS idx_patient_reports_created_at ON public.patient_reports(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON public.chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_is_active ON public.chat_sessions(is_active);

-- HACKATHON MODE: Disable Row Level Security for easier development
-- This makes all tables accessible without strict authentication
ALTER TABLE public.user_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.hearing_tests DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.symptoms DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_reports DISABLE ROW LEVEL SECURITY;

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_symptoms_updated_at BEFORE UPDATE ON public.symptoms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON public.chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patient_reports_updated_at BEFORE UPDATE ON public.patient_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data for testing (optional)
INSERT INTO public.user_profiles (id, email, age, gender) VALUES 
    ('550e8400-e29b-41d4-a716-446655440000', 'demo@neuravia.com', 30, 'prefer_not_say')
ON CONFLICT (email) DO NOTHING;

-- Grant permissions to all users (hackathon mode)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO anon;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO authenticated;
