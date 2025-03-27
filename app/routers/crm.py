from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.database import get_supabase
from app.core.auth import get_current_user, has_permission
from datetime import datetime

router = APIRouter(prefix="/workspaces")

# --- CRM Contacts ---
@router.post("/{workspace_id}/crm/contacts")
def create_contact(
    workspace_id: int,
    name: str,
    email: str,
    phone: str = None,
    company: str = None,
    lead_status: str = "prospect",
    source: str = "website",
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    data = {
        "name": name,
        "email": email,
        "phone": phone,
        "company": company,
        "lead_status": lead_status,
        "source": source,
        "workspace_id": workspace_id
    }
    
    response = supabase.table("crm_contacts").insert(data).execute()
    return response.data[0]

@router.get("/{workspace_id}/crm/contacts/{contact_id}")
def get_contact(
    workspace_id: int,
    contact_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("crm_contacts").select(
        "id, name, email, phone, company, lead_status, source"
    ).eq("id", contact_id).eq("workspace_id", workspace_id).execute()
    
    return response.data[0] if response.data else {}

# --- CRM Opportunities ---
@router.post("/{workspace_id}/crm/opportunities")
def create_opportunity(
    workspace_id: int,
    contact_id: str,
    title: str,
    estimated_value: float = 0.0,
    project_id: str = None, # Terkait proyek
    status: str = "open",
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    # Validasi contact id
    contact = supabase.table("crm_contacts").select("id").eq("id", contact_id).eq("workspace_id", workspace_id).execute()
    if not contact.data:
        raise HTTPException(400, "Contact not found")
    
    data = {
        "contact_id": contact_id,
        "title": title,
        "estimated_value": estimated_value,
        "project_id": project_id,
        "status": status,
        "workspace_id": workspace_id
    }
    
    response = supabase.table("crm_opportunities").insert(data).execute()
    return response.data[0]

# --- CRM Interactions ---
@router.post("/{workspace_id}/crm/interactions")
def create_interactions(
    workspace_id: int,
    contact_id: str,
    type: str,
    notes: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    # Validasi contact_id
    contact = supabase.table("crm_contacts").select("id").eq("id", contact_id).eq("workspace_id", workspace_id).execute()
    if not contact.data:
        raise HTTPException(400, "Contact not found")
    
    data = {
        "contact_id": contact_id,
        "type": type,
        "notes": notes,
        "workspace_id": workspace_id
    }
    
    response = supabase.table("crm_interactions").insert(data).execute()
    return response.data[0]

# --- Integrasi dengan modul lainnya ---
@router.get("/{workspace_id}/projects/{project_id}/crm")
def get_project_crm_data(
    workspace_id: int,
    project_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    # Dapatkan kontrak terkait proyek
    contracts = supabase.table("contracts").select(
        "id, title, customer_id, project_id, status"
    ).eq("project_id", project_id).eq("workspace_id", workspace_id).execute()
    
    # Dapatkan interaksi terkait proyek
    interactions = supabase.table("crm_interactions").select(
        "id, contact_id, type, notes, interactions_date"
    ).join("crm_contacts", "crm_interactions.contact_id", "=", "crm_contacts.id").execute()
    
    return {
        "contracts": contracts.data,
        "interactions": interactions.data
    }
    
@router.get("/{workspace_id}/crm/contacts")
def search_contacts(
    workspace_id: int,
    company: str = None,
    lead_status: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    query = supabase.table("crm_contacts").select(
        "id, name, email, company, lead_status"
    ).eq("workspace_id", workspace_id)
    
    if company:
        query = query.ilike("company", f"%{company}%")
    if lead_status:
        query = query.eq("lead_status", lead_status)
        
    return query.execute().data

@router.get("/{workspace_id}/crm/dashboard")
def get_crm_dashboard(
    workspace_id: int,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    return {
        "total_contacts": 100,
        "total_oppotunities": 30,
        "closed_opportunities": 15,
        "recent_interactions": [
            # Data interaksi terkini
        ]
    }

@router.get("/{workspace_id}/crm/reports/conversion")
def get_lead_conversion_report(
    workspace_id: int,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    # Hitung konversi lead dari prospect ke closed
    conversion = supabase.table("crm_contacts").select(
        "lead_status",
        "count(*)",
        group="lead_status"
    ).eq("workspace_id", workspace_id).execute()
    
    return {
        "conversion_rates": conversion.data
    }
    
@router.get("/{workspace_id}/crm/opportunities")
def get_opportunities(
    workspace_id: int,
    status: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    query = supabase.table("crm_opportunities").select(
        "id, title, estimated_value, status"
    ).eq("workspace_id", workspace_id)
    
    if status:
        query = query.eq("status", status)
    
    return query.execute().data

@router.get("/{workspace_id}/crm/reports/lead-conversion")
def get_lead_conversion_report(
    workspace_id: int,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    conversion = supabase.table("crm_contacts").select(
        "lead_status",
        "count(*)",
        group="lead_status"
    ).eq("workspace_id", workspace_id).execute()
    
    return {
        "prospect": 20,
        "qualified": 15,
        "closed": 5
    }

@router.get("/{workspace_id}/crm/reports/opportunity-project")
def get_opportunity_project_report(
    workspace_id: int,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    opportunities = supabase.table("crm_opportunities").select(
        "title, estimated_value, project_id"
    ).eq("workspace_id", workspace_id).execute()
    
    return {
        "opportunities": opportunities.data,
        "total_value": sum(opportunity.estimated_value for opportunity in opportunities.data)
    }
    
@router.put("/{workspace_id}/crm/opportunities/{opportunity_id}")
def update_opportunity(
    workspace_id: int,
    opportunity_id: str,
    status: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("crm_opportunities").update({"status": status}).eq("id", opportunity_id).execute()
    return response.data[0]