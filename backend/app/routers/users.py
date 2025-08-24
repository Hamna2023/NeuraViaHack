from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator, ConfigDict
from typing import Optional
from app.database import db
import uuid

router = APIRouter()

class UserProfileCreate(BaseModel):
    email: str
    age: Optional[int] = None
    gender: Optional[str] = None
    
    @validator('gender')
    def validate_gender(cls, v):
        if v is not None:
            valid_genders = ['male', 'female', 'nonbinary', 'prefer_not_say']
            if v.lower() not in valid_genders:
                raise ValueError(f'gender must be one of: {", ".join(valid_genders)}')
            return v.lower()
        return v
    
    model_config = ConfigDict(
        schema_extra={
            "example": {
                "email": "user@example.com",
                "age": 25,
                "gender": "male"  # lowercase values: male, female, nonbinary, prefer_not_say
            }
        }
    )

class UserProfileCreateWithId(BaseModel):
    user_id: str
    email: str
    age: Optional[int] = None
    gender: Optional[str] = None
    
    @validator('gender')
    def validate_gender(cls, v):
        if v is not None:
            valid_genders = ['male', 'female', 'nonbinary', 'prefer_not_say']
            if v.lower() not in valid_genders:
                raise ValueError(f'gender must be one of: {", ".join(valid_genders)}')
            return v.lower()
        return v

class UserProfileResponse(BaseModel):
    id: str
    email: str
    age: Optional[int] = None
    gender: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True
    )

@router.post("/profile", response_model=UserProfileResponse)
async def create_user_profile(profile: UserProfileCreate):
    """Create a new user profile with backend-generated user_id"""
    try:
        user_id = str(uuid.uuid4())
        
        created_profile = await db.create_user_profile(
            user_id=user_id,
            email=profile.email,
            age=profile.age,
            gender=profile.gender  # Already normalized by validator
        )
        
        if created_profile:
            return UserProfileResponse(**created_profile)
        else:
            raise HTTPException(status_code=500, detail="Failed to create user profile")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/profile/auth", response_model=UserProfileResponse)
async def create_auth_user_profile(profile: UserProfileCreateWithId):
    """Create a user profile for an authenticated user (from Supabase auth)"""
    try:
        # Check if profile already exists
        existing_profile = await db.get_user_profile(profile.user_id)
        if existing_profile:
            return UserProfileResponse(**existing_profile)
        
        created_profile = await db.create_user_profile(
            user_id=profile.user_id,
            email=profile.email,
            age=profile.age,
            gender=profile.gender
        )
        
        if created_profile:
            return UserProfileResponse(**created_profile)
        else:
            raise HTTPException(status_code=500, detail="Failed to create user profile")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: str):
    """Get user profile by ID"""
    try:
        profile = await db.get_user_profile(user_id)
        if profile:
            return UserProfileResponse(**profile)
        else:
            raise HTTPException(status_code=404, detail="User profile not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile/{user_id}", response_model=UserProfileResponse)
async def update_user_profile(user_id: str, updates: dict):
    """Update user profile"""
    try:
        # Normalize gender to lowercase if it's being updated
        if 'gender' in updates and updates['gender']:
            updates['gender'] = updates['gender'].lower()
            
        updated_profile = await db.update_user_profile(user_id, updates)
        if updated_profile:
            return UserProfileResponse(**updated_profile)
        else:
            raise HTTPException(status_code=404, detail="User profile not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
