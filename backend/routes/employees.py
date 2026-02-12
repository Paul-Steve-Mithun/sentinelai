"""
Employee management routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from database import get_db
from ml.feature_engineering import calculate_behavioral_fingerprint

router = APIRouter()


@router.get("/", response_model=List[schemas.Employee])
def get_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of all employees"""
    employees = db.query(models.Employee).offset(skip).limit(limit).all()
    return employees


@router.get("/{employee_id}", response_model=schemas.Employee)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """Get specific employee by ID"""
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.post("/", response_model=schemas.Employee)
def create_employee(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    """Create new employee"""
    # Check if employee_id already exists
    existing = db.query(models.Employee).filter(
        models.Employee.employee_id == employee.employee_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    
    # Check if email already exists
    existing_email = db.query(models.Employee).filter(
        models.Employee.email == employee.email
    ).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    db_employee = models.Employee(**employee.model_dump())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


@router.get("/{employee_id}/profile", response_model=schemas.BehavioralFingerprint)
def get_employee_profile(employee_id: int, db: Session = Depends(get_db)):
    """Get behavioral fingerprint for employee"""
    # Check if employee exists
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get latest fingerprint
    fingerprint = db.query(models.BehavioralFingerprint).filter(
        models.BehavioralFingerprint.employee_id == employee_id
    ).order_by(models.BehavioralFingerprint.computed_at.desc()).first()
    
    if not fingerprint:
        # Calculate fingerprint if not exists
        features = calculate_behavioral_fingerprint(db, employee_id)
        if features:
            fingerprint = models.BehavioralFingerprint(
                employee_id=employee_id,
                **features
            )
            db.add(fingerprint)
            db.commit()
            db.refresh(fingerprint)
        else:
            raise HTTPException(status_code=404, detail="No behavioral data available")
    
    return fingerprint


@router.get("/{employee_id}/anomalies", response_model=List[schemas.Anomaly])
def get_employee_anomalies(employee_id: int, db: Session = Depends(get_db)):
    """Get all anomalies for an employee"""
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    anomalies = db.query(models.Anomaly).filter(
        models.Anomaly.employee_id == employee_id
    ).order_by(models.Anomaly.detected_at.desc()).all()
    
    return anomalies
