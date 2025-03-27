from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.database import get_supabase
from app.core.config import settings
from app.core.auth import get_current_user, has_permission

router = APIRouter(prefix="/workspaces")
    
@router.get("/{workspace_id}/employees")
def get_employees(
    workspace_id: int,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    # Hanya user dari workspace yang bisa melihat data
    if not has_permission(current_user, workspace_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    response = supabase.table("employees").select("*").eq("workspace_id", workspace_id).execute()
    return response.data

@router.post("/{workspace_id}/employees")
def create_employees(
    workspace_id: int,
    name: str,
    position: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    data = {
        "name": name,
        "position": position,
        "workspace_id": workspace_id
    }
    response = supabase.table("employees").insert(data).execute()
    return response.data[0]

@router.put("/{workspace_id}/employees/{employee_id}")
def update_employee(
    workspace_id: int,
    employee_id: str,
    name: str = None,
    position: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    updates = {}
    if name:
        updates["name"] = name
    if position:
        updates["position"] = position
        
    response = supabase.table("employees").update(updates).eq("id", employee_id).eq("workspace_id", workspace_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Employee not found")
    return response.data[0]

@router.detele("/{workspace_id}/employees/{employee_id}")
def delete_employee(
    workspace_id: int,
    employee_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    response = supabase.table("employees").delete().eq("id", employee_id).eq("workspace_id", workspace_id).execute()
    if not response.data:
        raise HTTPException(404, "Employee not found")
    return {"message": "Employee deleted"}
