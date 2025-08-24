#!/usr/bin/env python3
"""
Migration script to add missing columns to the symptoms table.
Run this script to update your database schema.
"""

import asyncio
import sys
import os

# Add the app directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import db
from app.config import settings

async def run_migration():
    """Run the migration to add missing columns to symptoms table"""
    
    if not db.is_connected():
        print("❌ Database not connected. Please check your Supabase credentials.")
        return False
    
    try:
        print("🔄 Running migration: Adding missing columns to symptoms table...")
        
        # SQL commands to add the missing columns
        migration_sql = """
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
        """
        
        # Execute the migration using raw SQL
        # Note: This requires the postgrest client to support raw SQL execution
        # If it doesn't, you'll need to run this manually in your Supabase dashboard
        
        print("✅ Migration SQL prepared. Please run the following SQL in your Supabase dashboard:")
        print("\n" + "="*60)
        print(migration_sql)
        print("="*60)
        
        print("\n📋 Instructions:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Paste the SQL above and run it")
        print("4. After running the migration, uncomment the fields in symptoms.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 NeuraVia Symptoms Table Migration")
    print("=" * 40)
    
    success = asyncio.run(run_migration())
    
    if success:
        print("\n✅ Migration script completed successfully!")
        print("Please run the SQL commands in your Supabase dashboard.")
    else:
        print("\n❌ Migration script failed!")
        sys.exit(1)
