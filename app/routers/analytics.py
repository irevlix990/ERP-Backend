from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.database import get_supabase
from app.core.auth import get_current_user, has_permission
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/workspaces")

# --- Project Analytics ---
class ProjectAnalyticsInput(BaseModel):
    progress: float = None
    budget: float = None
    actual_cost: float = None
    kpi: dict = None
    
@router.post("/{workspace_id}/analytics/projects/{project_id}")
def create_or_update_project_analytics(
    workspace_id: int,
    project_id: str,
    data: ProjectAnalyticsInput,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    # Validasi project ada di workspace
    project = supabase.table("projects").select("id").eq("id", project_id).eq("workspace_id", workspace_id).execute()
    if not project.data:
        raise HTTPException(404, "Project not found")
    
    # Cek apakah analytics sudah ada
    existing = supabase.table("project_analytics").select("id").eq("project_id", project_id).eq("workspace_id", workspace_id).execute()
    
    payload = data.dict(exclude_unset=True)
    payload["project_id"] = project_id
    payload["workspace_id"] = workspace_id
    payload["updated_at"] = datetime.now().isoformat()
    
    if existing.data:
        # Update
        response = supabase.table("project_analytics").update(payload).eq("project_id", project_id).eq("workspace_id", workspace_id).execute()
    else:
        # Create
        payload["created_at"] = datetime.now().isoformat()
        response = supabase.table("project_analytics").insert(payload).execute()
        
    return response.data[0]

@router.get("/{workspace_id}/analytics/projects/{project_id}")
def get_project_analytics(
    workspace_id: int,
    project_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("project_analytics").select("*").eq("project_id", project_id).eq("workspace_id", workspace_id).execute()
    return response.data[0] if response.data else {}

# --- Employee Analytics ---
class EmployeeAnalyticsInput(BaseModel):
    performance_store: float = None
    task_completion: float = None
    evaluations: dict = None # Contoh: {"attendance": 4.5, "initiative": "excellent"}
    
@router.post("/{workspace_id}/analytics/employees/{employee_id}")
def create_or_update_employee_analytics(
    workspace_id: int,
    employee_id: str,
    data: EmployeeAnalyticsInput,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    # Validasi employee ada di workspace
    employee = supabase.table("employees").select("id").eq("employee_id", employee_id).eq("workspace_id", workspace_id).execute()
    if not employee.data:
        raise HTTPException(404, "Employee not found")
    
    if data.progress is not None and (data.progress < 0 or data.progress > 100):
        raise HTTPException(400, "Progress must be between 0-100%")
    
    if data.performance_store is not None and (data.performance_store < 0 or data.performance_store > 100):
        raise HTTPException(400, "Performance score must be between 0-100")
    
    existing = supabase.table("employee_analytics").select("id").eq("employee_id", employee_id).eq("workspace_id", workspace_id).execute()
    
    payload = data.dict(exclude_unset=True)
    payload["employee_id"] = employee_id
    payload["workspace_id"] = workspace_id
    payload["updated_at"] = datetime.now().isoformat()
    
    if existing.data:
        # Update
        response = supabase.table("employee_analytics").update(payload).eq("employee_id", employee_id).eq("workspace_id", workspace_id).execute()
    else:
        # Create
        payload["created_at"] = datetime.now().isoformat()
        response = supabase.table("employee_analytics").insert(payload).execute()
        
    return response.data[0]

@router.get("/{workspace_id}/analytics/employees/{employee_id}")
def get_employee_analytics(
    workspace_id: int,
    employee_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("employee_analytics").select("*").eq("employee_id", employee_id).eq("workspace_id", workspace_id).execute()
    return response.data[0] if response.data else {}

# --- Dashboard Analytics ---
@router.get("/{workspace_id}/analytics")
def get_workspace_analytics(
    workspace_id: int,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    # Ambil analytics proyek
    project_analytics = supabase.table("project_analytics").select(
        "project_id, progress, budget, actual_cost, kpi"
    ).eq("workspace_id", workspace_id).execute()
    
    # Ambil analytics karyawan
    employee_analytics = supabase.table("employee_analytics").select(
        "employee_id, performance_score, task_completion, evaluations"
    ).eq("workspace_id", workspace_id).execute()
    
    return {
        "projects": project_analytics.data,
        "employees": employee_analytics.data
    }
    
@router.get("/{workspace_id}/analytics/projects")
def get_all_project_analytics(
    workspace_id: int,
    min_progress: float = None, # Filter proyek dengan progress >= X%
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    query = supabase.table("project_analytics").select("*").eq("workspace_id", workspace_id)
    
    if min_progress is not None:
        query = query.gte("progress", min_progress)
        
    response = query.execute()
    return response.data

@router.get("/{workspace_id}/analytics/dashboard")
def get_dashboard_analytics(
    workspace_id: int,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    # Rata - rata progress proyek.
    avg_progress = supabase.table("project_analytics").select("avg(progress)").eq("workspace_id", workspace_id).execute()
    
    # Jumlah karyawan dengan skor diatas 80
    top_employees = supabase.table("employee_analytics").select("employee_id").eq("workspace_id", workspace_id).execute()
    
    return {
        "average_project_progress": avg_progress.data[0]["avg"] if avg_progress.data else 0,
        "top_employees_count": len(top_employees.data)
    }
