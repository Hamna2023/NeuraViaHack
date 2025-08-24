-- Migration: Add missing columns to symptoms table
-- This migration adds the columns that the Pydantic model expects but are missing from the database

-- Add missing columns to symptoms table
ALTER TABLE public.symptoms 
ADD COLUMN IF NOT EXISTS location TEXT,
ADD COLUMN IF NOT EXISTS triggers TEXT[],
ADD COLUMN IF NOT EXISTS alleviators TEXT[],
ADD COLUMN IF NOT EXISTS associated_symptoms TEXT[],
ADD COLUMN IF NOT EXISTS impact_on_daily_life TEXT;

-- Update existing rows to have default values for new columns
UPDATE public.symptoms 
SET 
    location = NULL,
    triggers = '{}',
    alleviators = '{}',
    associated_symptoms = '{}',
    impact_on_daily_life = NULL
WHERE location IS NULL;

-- Add comments to document the new columns
COMMENT ON COLUMN public.symptoms.location IS 'Location of the symptom on the body';
COMMENT ON COLUMN public.symptoms.triggers IS 'Things that trigger or worsen the symptom';
COMMENT ON COLUMN public.symptoms.alleviators IS 'Things that help alleviate the symptom';
COMMENT ON COLUMN public.symptoms.associated_symptoms IS 'Other symptoms that occur with this one';
COMMENT ON COLUMN public.symptoms.impact_on_daily_life IS 'How the symptom affects daily activities';
