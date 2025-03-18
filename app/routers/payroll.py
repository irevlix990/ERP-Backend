from fastapi import APIRouter, Depends, HTTPException, Response
from datetime import datetime
from supabase import Client
from app.database import get_supabase
from app.core.auth import get_current_user, has_permission

router = APIRouter(prefix="/workspaces")

@router.get("/{workspace_id}/payroll")
def get_payroll(
    workspace_id: int,
    start_date: str = None,
    end_date: str = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    query = supabase.table("payroll").select(
        "id, employee_id, gross_salary, deductions, net_salary, pay_date"
    ).eq("workspace_id", workspace_id)
    
    if start_date:
        query = query.gte("pay_date", start_date)
    if end_date:
        query = query.lte("pay_date", end_date)
        
    response = query.execute()
    return response.data

@router.post("/{workspace_id}/payroll")
def create_payroll(
    workspace_id: int,
    employee_id: str,
    gross_salary: float,
    pay_date: str, # Format: YYYY-MM-DD
    hours_rate_a: float,
    hours_rate_b: float = 0.0,
    hours_rate_c: float = 0.0,
    deductions: float = 0.0,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    # Validasi employee_id
    employee = supabase.table("employees").select("id").eq("id", employee_id).eq("workspace_id", workspace_id).execute()
    if not employee.data:
        raise HTTPException(400, "Employee not found")
    # validasi jam kerja
    if hours_rate_a < 0 or hours_rate_b < 0 or hours_rate_c < 0:
        raise HTTPException(400, "Work hours cannot negative value!")
    
    # Hitung gaji
    RATE_A = 20000
    RATE_B = RATE_A * 2
    RATE_C = RATE_A * 3
    
    gross_salary = (
        (hours_rate_a * RATE_A) +
        (hours_rate_b * RATE_B) +
        (hours_rate_c * RATE_C) 
    )
    
    deductions = gross_salary * 0.03
    net_salary = gross_salary - deductions
    
    data = {
        "employee_id": employee_id,
        "workspace_id": workspace_id,
        "gross_salary": gross_salary,
        "deductions": deductions,
        "net_salary": net_salary,
        "pay_date": pay_date
    }
    
    response = supabase.table("payroll").insert(data).execute()
    return response.data[0]

@router.put("/{workspace_id}/payroll/{payroll_id}")
def update_payroll(
    workspace_id: int,
    payroll_id: str,
    gross_salary: float = None,
    deductions: float = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    updates = {}
    if gross_salary is not None:
        updates["gross_salary"] = gross_salary
    if deductions is not None:
        updates["deductions"] = deductions
    if "gross_salary" in updates or "deductions" in updates:
        # Hitung net_salary setiap kali ada perubahan
        updates["net_salary"] = (
            updates.get("gross_salary", gross_salary) -
            updates.get("deductions", deductions)
        )
        
    response = supabase.table("payroll").update(updates).eq("id", payroll_id).eq("workspace_id", workspace_id).execute()
    if not response.data:
        raise HTTPException(404, "Payroll entry not found")
    return response.data[0]

@router.delete("/{workspace_id}/payroll/{payroll_id}")
def delete_payroll(
    workspace_id: int,
    payroll_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("payroll").delete().eq("id", payroll_id).eq("workspace_id", workspace_id).execute()
    if not response.data:
        raise HTTPException(404, "Payroll entry not found")
    return {"message": "Payroll entry deleted"}

@router.get("/{workspace_id}/payroll/{payroll_id}/slip")
def generate_payslip(
    workspace_id: int,
    payroll_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    if not has_permission(current_user, workspace_id):
        raise HTTPException(403, "Forbidden")
    
    response = supabase.table("payroll").select(
        "id, employee_id, gross_salary, deductions, net_salary, pay_date"
    ).eq("id", payroll_id).eq("workspace_id", workspace_id).execute()
    
    if not response.data:
        raise HTTPException(404, "Payroll entry not found")
    
    # Respons slip gaji (JSON)
    payslip = response.data[0]
    return {
        "employee_id": payslip["employee_id"],
        "pay_date": payslip["pay_date"],
        "details": {
            "gross_salary": payslip["gross_salary"],
            "deductions": payslip["deductions"],
            "net_salary": payslip["net_salary"]
        }
    }