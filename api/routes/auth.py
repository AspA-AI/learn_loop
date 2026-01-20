"""
Parent authentication routes (registration and login).
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from services.supabase_service import supabase_service
from models.schemas import ParentProfile
from utils.auth import hash_password, verify_password, create_access_token, decode_access_token
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Password validation constants
MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 8

# Request/Response Models
class ParentRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    preferred_language: str = "English"
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets requirements"""
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
        if len(v) > MAX_PASSWORD_LENGTH:
            raise ValueError(f"Password must be no more than {MAX_PASSWORD_LENGTH} characters long")
        return v

class ParentLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    parent_id: str
    email: str
    preferred_language: str = "English"

# Dependency to get current authenticated parent
async def get_current_parent(token: str = Depends(oauth2_scheme)) -> dict:
    """Get the current authenticated parent from JWT token"""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    parent_id = payload.get("sub")
    if parent_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    parent = supabase_service.get_parent_by_id(parent_id)
    if parent is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Parent not found",
        )
    
    return parent

@router.post("/register", response_model=TokenResponse)
async def register_parent(request: ParentRegister):
    """Register a new parent account"""
    try:
        # Hash password
        password_hash = hash_password(request.password)
        
        # Create parent account
        parent = supabase_service.create_parent(
            email=request.email,
            password_hash=password_hash,
            name=request.name,
            preferred_language=request.preferred_language
        )
        
        # Create access token
        access_token = create_access_token(data={"sub": str(parent["id"])})
        
        return TokenResponse(
            access_token=access_token,
            parent_id=str(parent["id"]),
            email=parent["email"],
            preferred_language=parent.get("preferred_language", "English")
        )
    except ValueError as e:
        error_msg = str(e)
        # Check if it's an email already exists error
        if "already registered" in error_msg.lower() or "email already" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This email address ({request.email}) is already registered. Please use a different email or try logging in."
            )
        # Password validation errors (from validator or hash_password)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Error registering parent: {e}", exc_info=True)
        # Check if it's a password length error
        error_msg = str(e)
        if "too long" in error_msg.lower() or "no more than" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be between 6 and 8 characters long."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register parent. Please try again later."
        )

@router.post("/login", response_model=TokenResponse)
async def login_parent(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login parent and get access token"""
    try:
        # Get parent by email
        parent = supabase_service.get_parent_by_email(form_data.username)  # OAuth2 uses 'username' for email
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(form_data.password, parent["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": str(parent["id"])})
        
        return TokenResponse(
            access_token=access_token,
            parent_id=str(parent["id"]),
            email=parent["email"],
            preferred_language=parent.get("preferred_language", "English")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in parent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to login")

@router.get("/me", response_model=ParentProfile)
async def get_current_parent_profile(current_parent: dict = Depends(get_current_parent)):
    """Get current authenticated parent's profile"""
    return ParentProfile(
        id=str(current_parent["id"]),
        email=current_parent["email"],
        name=current_parent.get("name"),
        preferred_language=current_parent.get("preferred_language", "English")
    )

