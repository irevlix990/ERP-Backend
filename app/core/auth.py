from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from supabase import Client
from app.core.config import settings
from app.database import get_supabase
import re

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(supabase: Client = Depends(get_supabase), token: str = Depends(oauth2_scheme)):
    try:
        user = supabase.auth.get_user(token)
        return user.data.user
    except Exception:
        raise HTTPException(401, "Invalid token")