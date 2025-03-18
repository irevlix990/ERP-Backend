from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from app.database import get_supabase
from app.core.auth import get_current_user, has_permission

router = APIRouter(prefix="/workspaces")

@router.get("/{workspace_id}/customers")
def get_customers(
    workspace_id: int,
    search: str = None,
    company: str = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    offset = (page - 1) * limit
    
    query = supabase.table("customers").select("*").eq("workspace_id", workspace_id).range(offset, offset + limit)
    
    if search:
        query = query.or_(
            supabase.table("customers").filter("name", "ilike", f"%{search}%"),
            supabase.table("customers").filter("email", "ilike", f"%{search}%")
        )
    if company:
        query = query.eq("company", company)
    
    response = query.execute()
    return response.data

@router.get("/{workspace_id}/customers/{customers_id}/projects")
def get_customer_project(
    workspace_id: int,
    customer_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    offset = (page - 1) * limit
    
    response = supabase.table("projects").select("*") \
        .eq("workspace_id", workspace_id) \
        .eq("customer_id", customer_id) \
        .range(offset, offset + limit) \
        .execute()
    return response.data

@router.post("/{workspace_id}/customers")
def create_customers(
    workspace_id: int,
    name: str,
    email: str,
    phone: str = None,
    address: str = None,
    company: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    data = {
        "name": name,
        "email": email,
        "phone": phone,
        "address": address,
        "company": company,
        "workspace_id": workspace_id
    }
    if not name or not email:
        raise HTTPException(400, "Name or Email is required")
    
    existing = supabase.table("customers").select("id").eq("email", email).eq("workspace_id", workspace_id).execute()
    if existing.data:
        raise HTTPException(400, "Email already exists")
    else:
        response = supabase.table("customers").insert(data).execute()
    return response.data[0]

@router.put("/{workspace_id}/customers/{customer_id}")
def update_customers(
    workspace_id: str,
    customer_id: str,
    name: str = None,
    email: str = None,
    phone: str = None,
    address: str = None,
    company: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    updates = {}
    if name:
        updates["name"] = name,
    if email:
        updates["email"] = email,
    if phone:
        updates["phone"] = phone,
    if address:
        updates["address"] = address,
    if company:
        updates["company"] = company
        
    response = supabase.table("customers").update(updates).eq("id", customer_id).eq("workspace_id", workspace_id).execute()
    if not response.data:
        raise HTTPException(404, "Customer not found")
    return response.data[0]

@router.delete("/{workspaces_id}/customers/{customer_id}")
def delete_customer(
    workspace_id: int,
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("customers").delete().eq("id", customer_id).eq("workspace_id", workspace_id).execute()
    if not response.data:
        raise HTTPException(404, "Customer not found")
    return {"message": "Customer deleted"}