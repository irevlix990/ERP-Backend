from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.database import get_supabase
from Backend.app.core.auth import oauth2_scheme

router = APIRouter(prefix="/workspaces")

def get_current_user(token: str = Depends(oauth2_scheme)):
    supabase: Client = get_supabase()
    try:
        user = supabase.auth.get_user(token)
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/")
def get_workspaces():
    supabase: Client = get_supabase()
    response = supabase.table("workspaces").select("*").execute()
    return response.data

@router.post("/")
def create_workspaces(name: str, theme:str = "light"):
    supabase: Client = get_supabase()
    data = {
        "name": name,
        "theme": theme
    }
    response = supabase.table("workspaces").insert("*").execute()
    return response.data[0]