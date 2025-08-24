from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator, ConfigDict
from typing import Optional
from datetime import datetime
from app.database import db
from app.pydantic_config import get_model_config
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Simple user models
class UserSignup(BaseModel):
    email: str
    password: str  # In production, this should be hashed
    name: str
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
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 1 or v > 120):
            raise ValueError('age must be between 1 and 120')
        return v

class UserLogin(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = get_model_config()

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
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
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 1 or v > 120):
            raise ValueError('age must be between 1 and 120')
        return v

# Simple in-memory user storage for hackathon (replace with database in production)
# In production, use proper password hashing and JWT tokens
users_db = {}  # email -> user_data

@router.post("/signup", response_model=UserProfile)
async def signup(user_data: UserSignup):
    """Create a new user account"""
    try:
        # Check if user already exists in database
        existing_user = await db.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Generate UUID for user
        user_id = str(uuid.uuid4())
        
        # Create user profile in database
        created_profile = await db.create_user_profile(
            user_id=user_id,
            email=user_data.email,
            name=user_data.name,
            age=user_data.age,
            gender=user_data.gender
        )
        
        if not created_profile:
            raise HTTPException(status_code=500, detail="Failed to create user profile in database")
        
        # Store user in memory (for hackathon - replace with proper auth in production)
        users_db[user_data.email] = {
            "id": user_id,
            "email": user_data.email,
            "password": user_data.password,  # In production, hash this
            "name": user_data.name,
            "age": user_data.age,
            "gender": user_data.gender
        }
        
        logger.info(f"Successfully created user: {user_id}")
        return UserProfile(**created_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user account")

@router.post("/login", response_model=UserProfile)
async def login(credentials: UserLogin):
    """Authenticate user and return profile"""
    try:
        # Check if user exists in database first
        db_user = await db.get_user_by_email(credentials.email)
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if user exists in memory storage (for password verification)
        if credentials.email not in users_db:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user_data = users_db[credentials.email]
        
        # Check password (in production, use proper password hashing)
        if user_data["password"] != credentials.password:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        logger.info(f"User logged in successfully: {user_data['id']}")
        return UserProfile(**db_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """Get user profile by ID"""
    try:
        profile = await db.get_or_create_user_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        return UserProfile(**profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")

@router.put("/profile/{user_id}", response_model=UserProfile)
async def update_user_profile(user_id: str, updates: UserProfileUpdate):
    """Update user profile"""
    try:
        # Convert Pydantic model to dict, excluding None values
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid updates provided")
        
        updated_profile = await db.update_user_profile(user_id, update_data)
        
        if not updated_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Update in-memory storage as well
        for email, user_data in users_db.items():
            if user_data["id"] == user_id:
                for key, value in update_data.items():
                    user_data[key] = value
                break
        
        logger.info(f"Successfully updated user profile: {user_id}")
        return UserProfile(**updated_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user profile")

@router.get("/users", response_model=list[UserProfile])
async def list_users():
    """List all users (for hackathon demo purposes)"""
    try:
        # This would typically be restricted in production
        all_profiles = []
        
        for user_data in users_db.values():
            profile = await db.get_user_profile(user_data["id"])
            if profile:
                all_profiles.append(UserProfile(**profile))
        
        return all_profiles
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")

@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete user account (for hackathon demo purposes)"""
    try:
        # Find user in memory storage
        user_email = None
        for email, user_data in users_db.items():
            if user_data["id"] == user_id:
                user_email = email
                break
        
        if not user_email:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Remove from memory storage
        del users_db[user_email]
        
        # In production, you would also delete from database
        # For now, we'll just return success
        
        logger.info(f"User deleted: {user_id}")
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")
