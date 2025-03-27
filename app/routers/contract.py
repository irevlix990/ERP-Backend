from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from datetime import datetime
from app.database import get_supabase
from app.core.auth import get_current_user, has_permission

router = APIRouter(prefix="/workspaces")

@router.get("/{workspace_id}/contracts")
def get_contracts(
    workspace_id: int,
    status: str = None,
    contract_type: str = None,
    customer_id: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    query = supabase.table("contracts").select(
        "id, title, customer_id, project_id, start_date, end_date, status, contract_type"
    ).eq("workspace_id", workspace_id)
    
    if status:
        query = query.eq("status", status)
    if contract_type:
        query = query.eq("contract_type", contract_type)
    if customer_id:
        query = query.eq("customer_id", customer_id)

    response = query.execute()
    return response.data

@router.post("/{workspace_id}/contracts")
def create_contracts(
    workspace_id: int,
    title: str,
    contact_id: str,
    customer_id: str,
    start_date: str,
    end_date:str,
    contract_type: str,
    project_id: str = None,
    status: str = "pending",
    description: str = None,
    terms: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    # validasi contact ada di workspace
    contact = supabase.table("crm_contacts").select("id").eq("id", contact_id).eq("workspace_id", workspace_id).execute()
    if not contact.data:
        raise HTTPException(400, "Contact not found")
    
    # Validasi customer dan project
    customer = supabase.table("customers").select("id").eq("id", customer_id).eq("workspace_id", workspace_id).execute()
    if not customer.data:
        raise HTTPException(400, "Customer not found")
    
    if project_id:
        project = supabase.table("projects").select("id").eq("id", project_id).eq("workspace_id", workspace_id).execute()
        if not project.data:
            raise HTTPException(400, "Project not found")
        
    data = {
        "title": title,
        "customer_id": customer_id,
        "project_id": project_id,
        "start_date": start_date,
        "end_date": end_date,
        "status": status,
        "contract_type": contract_type,
        "description": description,
        "terms": terms,
        "workspace_id": workspace_id
    }
    
    response = supabase.table("contracts").insert(data).execute()
    return response.data[0]

@router.put("/{workspace.id}/contracts/{contract_id}")
def update_contract(
    workspace_id: int,
    contract_id: str,
    title: str = None,
    status: str = None,
    description: str = None,
    terms: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    updates = {}
    if title:
        updates["title"] = title
    if status:
        updates["status"] = status
    if description:
        updates["description"] = description
    if terms:
        updates["terms"] = terms
        
    response = supabase.table("contracts").update(updates).eq("id", contract_id).eq("workspace_id", workspace_id).execute()
    if not response.data:
        raise HTTPException(404, "Contract not found")
    return response.data[0]

@router.delete("/{workspace_id}/contracts/{contract_id}")
def delete_contract(
    workspace_id: int,
    contract_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("contracts").delete().eq("id", contract_id).eq("workspace_id", workspace_id).execute()
    if not response.data:
        raise HTTPException(404, "Contract not found")
    return {"message": "Contract deleted"}

@router.get("/{workspace_id}/contracts/{contract_id}/details")
def get_contract_details(
    workspace_id: int,
    contract_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("contracts").select(
        "id, title, description, customer_id, project_id, start_date, end_date, status, contract_type, terms"
    ).eq("id", contract_id).eq("workspace_id", workspace_id).execute()
    
    if not response.data:
        raise HTTPException(404, "Contract not found")
    
    return response.data[0]

@router.post("/{workspace_id}/contracts/update-status")
def trigger_auto_update(
    workspace_id: int,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    current_date = datetime.now().date().isoformat()
    response = supabase.table("contracts").update({"status": "expired"}).lt("end_date", current_date).execute()
    return {"message": f"{len(response.data)} contracts updated to expired!"}

@router.get("/{workspace_id}/contracts/{contract_id}/crm")
def get_contract_crm_data(
    workspace_id: int,
    contract_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("contracts").select(
        "contact_id, crm_contacts!inner(*)" # Join dengan contact
    ).eq("id", contract_id).execute()
    
    return response.data[0]

@router.get("/{workspace_id}/contracts/{contract_id}/invoices")
def get_contract_invoices(
    workspace_id: int,
    contract_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("invoices").select(
        "id, amount, due_date, status"
    ).eq("contract_id", contract_id).eq("workspace_id", workspace_id).execute()
    
    return response.data
