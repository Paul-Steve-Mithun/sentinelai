"""
Employee management routes
"""
from fastapi import APIRouter, HTTPException
from typing import List
import models
import schemas
from ml.feature_engineering import calculate_behavioral_fingerprint
from beanie import PydanticObjectId

router = APIRouter()


@router.get("", response_model=List[schemas.Employee])
async def get_employees(skip: int = 0, limit: int = 100):
    """Get list of all employees"""
    employees = await models.Employee.find_all().skip(skip).limit(limit).to_list()
    return employees


@router.get("/{employee_id}", response_model=schemas.Employee)
async def get_employee(employee_id: str):
    """Get specific employee by ID"""
    if PydanticObjectId.is_valid(employee_id):
        employee = await models.Employee.get(employee_id)
    else:
         # Try finding by string id if not object id
         employee = await models.Employee.find_one(models.Employee.employee_id == employee_id)

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.post("", response_model=schemas.Employee)
async def create_employee(employee: schemas.EmployeeCreate):
    """Create new employee"""
    # Check if employee_id already exists
    existing = await models.Employee.find_one(models.Employee.employee_id == employee.employee_id)
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    
    # Check if email already exists
    existing_email = await models.Employee.find_one(models.Employee.email == employee.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    db_employee = models.Employee(**employee.model_dump())
    await db_employee.create()
    return db_employee


@router.get("/{employee_id}/profile", response_model=schemas.BehavioralFingerprint)
async def get_employee_profile(employee_id: str):
    """Get behavioral fingerprint for employee"""
    # Check if employee exists
    if PydanticObjectId.is_valid(employee_id):
        employee = await models.Employee.get(employee_id)
    else:
        employee = await models.Employee.find_one(models.Employee.employee_id == employee_id)
        
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get latest fingerprint
    fingerprint = await models.BehavioralFingerprint.find(
        models.BehavioralFingerprint.employee_id == employee.id
    ).sort(-models.BehavioralFingerprint.computed_at).first_or_none()
    
    if not fingerprint:
        # Calculate fingerprint if not exists
        features = await calculate_behavioral_fingerprint(str(employee.id))
        if features:
            fingerprint = models.BehavioralFingerprint(
                employee_id=employee.id,
                **features
            )
            await fingerprint.create()
        else:
            raise HTTPException(status_code=404, detail="No behavioral data available")
    
    return fingerprint


@router.get("/{employee_id}/anomalies", response_model=List[schemas.Anomaly])
async def get_employee_anomalies(employee_id: str):
    """Get all anomalies for an employee"""
    if PydanticObjectId.is_valid(employee_id):
        employee = await models.Employee.get(employee_id)
    else:
        employee = await models.Employee.find_one(models.Employee.employee_id == employee_id)

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    anomalies = await models.Anomaly.find(
        models.Anomaly.employee_id == employee.id
    ).sort(-models.Anomaly.detected_at).to_list()
    
    return anomalies
