from fastapi import APIRouter, HTTPException, Depends
from supabase import Client
from app.core.auth import oauth2_scheme
from app.database import get_supabase
import re

router = APIRouter(prefix="/auth")

def validate_password(password: str):
    # Contoh kriteria:
    # - Minimal harus 8 karakter
    # - Harus ada huruf besar, kecil, dan angka
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="Password must contain uppercase letters")
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=400, detail="Password must contain lowercase letters")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="password must contain number")

@router.post("/register")
async def register(email: str, password: str):
    validate_password(password)
    
    supabase: Client = get_supabase()
    try:
        response = supabase.auth.sign_up(
            email=email,
            password=password
        )
        if response.status_code == 200:
            return {"message": "Registration successful", "user_id": response.data.user.id}
        else:
            raise HTTPException(status_code=400, detail="Registration failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login(username: str, password: str):
    supabase: Client = get_supabase()
    response = supabase.auth.sign_in_with_password(
        email=username,
        password=password
    )
    if response.status_code == 200:
        return {"access_token": response.data.session.access_token}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/profile")
def create_profile(
    full_name: str,
    workspace_id: int,
    token: str = Depends(oauth2_scheme)
):
    supabase: Client = get_supabase()
    user = supabase.auth.get_user(token)
    user_id = user.data.user.id
    
    data = {
        "id": user_id,
        "full_name": full_name,
        "workspace_id": workspace_id,
        "role": "member"
    }
    
    response = supabase.table("users").insert(data).execute()
    return {"message": "Profile created", "user": response.data[0]}