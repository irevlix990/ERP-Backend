from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.database import get_supabase
from app.core.config import settings
from app.core.auth import oauth2_scheme, get_current_user
from typing import List

router = APIRouter(prefix="/users")
    
def is_workspace_admin(user):
    return user.role == 'admin'

def is_manager(user):
    return user.role == 'manager'

def is_staff(user):
    return user.role == 'guest'

@router.get("/", response_model=List[dict])
def get_users(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if current_user['role'] == 'admin':
        # Admin bisa melihat semua user
        response = supabase.table("users").select("*").execute()
    else:
        # User lain hanya bisa melihat diri sendiri
        response = supabase.table("users").select("*").eq("id", current_user['id']).execute()
    return response.data

@router.post("/", response_model=dict)
def create_user(
    full_name: str,
    email: str,
    workspace_id: int,
    role: str = 'guest',
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not is_workspace_admin(current_user):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    data = {
        "full_name": full_name,
        "email": email,
        "role": role,
        "workspace_id": workspace_id
    }
    response = supabase.table("users").insert(data).execute()
    return response.data[0]

@router.put("/{user_id}", response_model=dict)
def update_user(
    user_id: str,
    full_name: str = None,
    role: str = None,
    workspace_id: int = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not is_workspace_admin(current_user):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    updates = {}
    if full_name:
        updates["full_name"] = full_name
    if role:
        updates["role"] = role
    if workspace_id:
        updates["workspace_id"] = workspace_id
        
    response = supabase.table("users").update(updates).eq("id", user_id).execute()
    if response.data:
        return response.data[0]
    else:
        raise HTTPException(status_code=404, detail="User not found") 
    
@router.delete("/{user_id}", response_model=dict)
def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not is_workspace_admin(current_user):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    response = supabase.table("users").delete().eq("id", user_id).execute()
    if response.data:
        return {"message": "User deleted"}
    else:
        raise HTTPException(status_code=404, detail="User not found")
    
@router.get("/me")
def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user

@router.put("/me")
def update_profile(
    full_name: str = None,
    workspace_id: int = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    user_id = current_user["id"]
    updates = {}
    if full_name:
        updates["full_name"] = full_name
    if workspace_id:
        updates["workspace_id"] = workspace_id
        
    response = supabase.table("users").update(updates).eq("id", user_id).execute()
    if response.data:
        return {"message": "Profile updated", "data": response.data[0]}
    else:
        raise HTTPException(404, "User not found")
    
@router.get("/all")
def get_all_users(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if current_user["role"] != "admin":
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("users").select("*").execute()
    return response.data[0]
