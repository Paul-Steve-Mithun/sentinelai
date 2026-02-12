"""
Anomaly management routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import models
import schemas
from database import get_db

router = APIRouter()


@router.get("", response_model=List[schemas.Anomaly])
def get_anomalies(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all anomalies with optional filters"""
    query = db.query(models.Anomaly)
    
    if status:
        query = query.filter(models.Anomaly.status == status)
    if risk_level:
        query = query.filter(models.Anomaly.risk_level == risk_level)
    
    anomalies = query.order_by(
        models.Anomaly.detected_at.desc()
    ).offset(skip).limit(limit).all()
    
    # Manually construct response with employee data
    result = []
    for anomaly in anomalies:
        employee = db.query(models.Employee).filter(
            models.Employee.id == anomaly.employee_id
        ).first()
        
        anomaly_dict = {
            'id': anomaly.id,
            'employee_id': anomaly.employee_id,
            'detected_at': anomaly.detected_at,
            'anomaly_score': anomaly.anomaly_score,
            'risk_level': anomaly.risk_level,
            'risk_score': anomaly.risk_score,
            'description': anomaly.description,
            'anomaly_type': anomaly.anomaly_type,
            'shap_values': anomaly.shap_values,
            'top_features': anomaly.top_features,
            'status': anomaly.status,
            'resolved_at': anomaly.resolved_at,
            'resolved_by': anomaly.resolved_by,
            'resolution_notes': anomaly.resolution_notes,
            'employee': employee
        }
        result.append(anomaly_dict)
    
    return result


@router.get("/{anomaly_id}", response_model=schemas.Anomaly)
def get_anomaly(anomaly_id: int, db: Session = Depends(get_db)):
    """Get specific anomaly details"""
    anomaly = db.query(models.Anomaly).filter(models.Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return anomaly


@router.get("/{anomaly_id}/mitre", response_model=List[schemas.MitreMapping])
def get_anomaly_mitre(anomaly_id: int, db: Session = Depends(get_db)):
    """Get MITRE ATT&CK mappings for an anomaly"""
    anomaly = db.query(models.Anomaly).filter(models.Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    mappings = db.query(models.MitreMapping).filter(
        models.MitreMapping.anomaly_id == anomaly_id
    ).order_by(models.MitreMapping.confidence.desc()).all()
    
    return mappings


@router.get("/{anomaly_id}/mitigation", response_model=List[schemas.MitigationStrategy])
def get_anomaly_mitigation(anomaly_id: int, db: Session = Depends(get_db)):
    """Get mitigation strategies for an anomaly"""
    anomaly = db.query(models.Anomaly).filter(models.Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    strategies = db.query(models.MitigationStrategy).filter(
        models.MitigationStrategy.anomaly_id == anomaly_id
    ).order_by(models.MitigationStrategy.priority).all()
    
    return strategies


@router.post("/{anomaly_id}/resolve")
def resolve_anomaly(
    anomaly_id: int,
    resolution: schemas.AnomalyResolve,
    db: Session = Depends(get_db)
):
    """Mark anomaly as resolved"""
    anomaly = db.query(models.Anomaly).filter(models.Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    anomaly.status = resolution.status
    anomaly.resolved_at = datetime.now(timezone.utc)
    anomaly.resolved_by = resolution.resolved_by
    anomaly.resolution_notes = resolution.resolution_notes
    
    db.commit()
    db.refresh(anomaly)
    
    return {"message": "Anomaly resolved successfully", "anomaly": anomaly}


@router.post("/{anomaly_id}/mitigation/{strategy_id}/implement")
def implement_mitigation(
    anomaly_id: int,
    strategy_id: int,
    implementation: schemas.MitigationImplement,
    db: Session = Depends(get_db)
):
    """Mark mitigation strategy as implemented"""
    strategy = db.query(models.MitigationStrategy).filter(
        models.MitigationStrategy.id == strategy_id,
        models.MitigationStrategy.anomaly_id == anomaly_id
    ).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Mitigation strategy not found")
    
    strategy.implemented = True
    strategy.implemented_at = datetime.now(timezone.utc)
    strategy.implemented_by = implementation.implemented_by
    
    db.commit()
    db.refresh(strategy)
    
    return {"message": "Mitigation strategy marked as implemented", "strategy": strategy}
