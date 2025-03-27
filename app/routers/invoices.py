from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.database import get_supabase
from app.core.auth import get_current_user, has_permission
from datetime import datetime

router = APIRouter(prefix="/workspaces")

def validate_due_date(due_date):
    try:
        due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
        if due_date_obj < datetime.now().date():
            raise ValueError("Due date must be in the future")
    except ValueError as e:
        raise HTTPException(400, str(e))

# --- Endpoint untuk Invoice ---
@router.post("/{workspace_id}/invoices")
def create_invoices(
    workspace_id: int,
    amount: float,
    due_date: str,
    payment_method: str,
    notes: str = None,
    project_id: str = None,
    contract_id: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    # Validasi tanggal
    validate_due_date(due_date)
    
    # validasi project_id / contract_id jika diberikan
    if project_id:
        project = supabase.table("projects").select("id").eq("id", project_id).eq("workspace_id", workspace_id).execute()
        if not project.data:
            raise HTTPException(400, "Project not found")
        
    if contract_id:
        contract = supabase.table("contracts").select("id").eq("id", contract_id).eq("workspace_id", workspace_id).execute()
        if not contract.data:
            raise HTTPException(400, "Contract not found")
        
    data = {
        "project_id": project_id,
        "contract_id": contract_id,
        "amount": amount,
        "due_date": due_date,
        "payment_method": payment_method,
        "notes": notes,
        "workspace_id": workspace_id,
        "status": "pending" # Default status
    }
    
    response = supabase.table("invoices").insert(data).execute()
    return response.data[0]

@router.get ("/{workspace_id}/invoices")
def get_invoices(
    workspace_id: int,
    project_id: str = None,
    contract_id: str = None,
    status: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    query = supabase.table("invoices").select(
        "id, project_id, contract_id, amount, due_date, status, payment_method, notes"
    ).eq("workspace_id", workspace_id)
    
    if project_id:
        query = query.eq("project_id", project_id)
    if contract_id:
        query = query.eq("contract_id", contract_id)
    if status:
        query = query.eq("status", status)
        
    response = query.execute()
    return response.data

@router.put("/{workspace_id}/invoices/{invoice_id}")
def update_invoice(
    workspace_id: int,
    invoice_id: str,
    status: str = None,
    notes: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    updates = {}
    if status:
        updates["status"] = status
    if notes:
        updates["notes"] = notes
        
    response = supabase.table("invoices").update(updates).eq("id", invoice_id).eq("workspace_id", workspace_id).execute()
    if not response.data:
        raise HTTPException(404, "Invoice not found")
    
    return response.data[0]

@router.delete("/{workspace_id}/invoices/{invoice_id}")
def delete_invoice(
    workspace_id: int,
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("invoices").delete().eq("id", invoice_id).eq("workspace_id", workspace_id).execute()
    if not response.data:
        raise HTTPException(404, "Invoice not found")
    
    return {"message": "Invoice deleted"}

#--- Endpoint untuk tracking pembayaran ---
@router.post("/{workspace_id}/invoices/{invoice_id}/mark-paid")
def mark_invoice_paid(
    workspace_id: int,
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("invoices").update({"status": "paid"}).eq("id", invoice_id).eq("workspace_id", workspace_id).execute()
    if not response.data:
        raise HTTPException(404, "Invoice not found")
    
    return {"message": "Invoice marked as paid"}

#--- Endpoint untuk Laporan Invoice ---
@router.get("/{workspace_id}/invoices/reports")
def get_invoice_report(
    workspace_id: int,
    start_date: str = None,
    end_date: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    query = supabase.table("invoices").select(
        "id, amount, due_date, status, payment_method"
    ).eq("workspace_id", workspace_id)
    
    if start_date:
        query = query.gte("due_date", start_date)
    if end_date:
        query = query.lte("due_date", end_date)
        
    response = query.execute()
    return {
        "total_invoices": len(response.data),
        "total_amount": sum(inv["amount"] for inv in response.data),
        "data": response.data
    }
