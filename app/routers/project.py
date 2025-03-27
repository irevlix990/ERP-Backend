from fastapi import APIRouter, HTTPException, Depends
from supabase import Client
from app.database import get_supabase
from app.core.auth import get_current_user, has_permission

router = APIRouter(prefix="/workspaces")

@router.get("/{workspace_id}/projects")
def get_projects(
    workspace_id: int,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("projects").select("*").eq("workspace_id", workspace_id).execute()
    return response.data

@router.post("/{workspace_id}/projects")
def create_project(
    workspace_id: int,
    name: str,
    contact_id: str = None, # Baru: terkait CRM contact
    description: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    if contact_id:
        # validasi contact ada di workspace
        contact = supabase.table("crm_contacts").select("id").eq("id", contact_id).eq("workspace_id", workspace_id).execute()
        if not contact.data:
            raise HTTPException(400, "Contact not found")
    
    data = {
        "name": name,
        "description": description,
        "workspace_id": workspace_id
    }
    response = supabase.table("projects").insert(data).execute()
    return response.data[0]

@router.put("/{workspace_id}/projects/{project_id}")
def update_project(
    workspace_id: int,
    project_id: int,
    name: str = None,
    description: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = get_supabase()

):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
        
    # Data yang akan di update
    updates = {}
    if name:
        updates["name"] = name
    if description:
        updates["description"] = description
        
    # Lakukan update
    response = supabase.table("projects").update(updates).eq("id", project_id).eq("workspace_id", workspace_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Project not found")
    return response.data[0]
    
@router.delete("/{workspace_id}/projects/{project_id}")
def delete_project(
    workspace_id: int,
    project_id: int,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    # Hapus proyek
    response = supabase.table("projects").delete().eq("id", project_id).eq("workspace_id", workspace_id).execute()
    
    if response.data:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted"}

@router.get("/{workspace_id}/projects/{project_id}/contracts")
def get_project_contracts(
    workspace_id: int,
    project_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("contracts").select(
        "*"
    ).eq("workspace_id", workspace_id).eq("project_id", project_id).execute()
    return response.data

@router.get("/{workspace_id}/projects/{project_id}/crm")
def get_project_crm(
    workspace_id: int,
    project_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("projects").select(
        "contact_id, contracts!inner(*)" # Join dengan kontrak
    ).eq("id", project_id).eq("workspace_id", workspace_id).execute()
    
    return response.data[0]

@router.get("/{workspace_id}/projects/{project_id}/invoices")
def get_project_invoices(
    workspace_id: int,
    project_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("invoices").select(
        "id, amount, due_date, status"
    ).eq("project_id", project_id).eq("workspace_id", workspace_id).execute()
    
    return response.data
    
