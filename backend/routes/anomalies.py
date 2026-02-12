"""
Anomaly management routes
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone
import models
import schemas
from beanie import PydanticObjectId, WriteRules

router = APIRouter()


@router.get("", response_model=List[schemas.Anomaly])
async def get_anomalies(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get all anomalies with optional filters"""
    query = models.Anomaly.find_all()
    
    if status:
        query = query.find(models.Anomaly.status == status)
    if risk_level:
        query = query.find(models.Anomaly.risk_level == risk_level)
    
    anomalies = await query.sort(-models.Anomaly.detected_at).skip(skip).limit(limit).to_list()
    
    # Manually construct response with employee data
    result = []
    
    # Optimization: Fetch all employees referenced
    emp_ids = list(set([a.employee_id for a in anomalies if a.employee_id]))
    from beanie.operators import In
    employees = await models.Employee.find(In(models.Employee.id, emp_ids)).to_list()
    emp_map = {e.id: e for e in employees}
    
    for anomaly in anomalies:
        employee = emp_map.get(anomaly.employee_id)
        
        anomaly_dict = {
            'id': str(anomaly.id),
            'employee_id': str(anomaly.employee_id),
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
async def get_anomaly(anomaly_id: str):
    """Get specific anomaly details"""
    if not PydanticObjectId.is_valid(anomaly_id):
        raise HTTPException(status_code=404, detail="Invalid Anomaly ID")
        
    anomaly = await models.Anomaly.get(anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return anomaly


@router.get("/{anomaly_id}/mitre", response_model=List[schemas.MitreMapping])
async def get_anomaly_mitre(anomaly_id: str):
    """Get MITRE ATT&CK mappings for an anomaly"""
    try:
        if not PydanticObjectId.is_valid(anomaly_id):
             raise HTTPException(status_code=404, detail="Invalid Anomaly ID")

        # verify anomaly exists
        anomaly = await models.Anomaly.get(anomaly_id)
        if not anomaly:
            raise HTTPException(status_code=404, detail="Anomaly not found")
        
        mappings = await models.MitreMapping.find(
            models.MitreMapping.anomaly_id == anomaly.id
        ).sort("-confidence").to_list()
        
        return mappings
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching MITRE mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{anomaly_id}/mitigation", response_model=List[schemas.MitigationStrategy])
async def get_anomaly_mitigation(anomaly_id: str):
    """Get mitigation strategies for an anomaly"""
    try:
        if not PydanticObjectId.is_valid(anomaly_id):
             raise HTTPException(status_code=404, detail="Invalid Anomaly ID")

        anomaly = await models.Anomaly.get(anomaly_id)
        if not anomaly:
            raise HTTPException(status_code=404, detail="Anomaly not found")
        
        strategies = await models.MitigationStrategy.find(
            models.MitigationStrategy.anomaly_id == anomaly.id
        ).sort("priority").to_list()
        
        return strategies
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching mitigation strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{anomaly_id}/resolve")
async def resolve_anomaly(
    anomaly_id: str,
    resolution: schemas.AnomalyResolve
):
    """Mark anomaly as resolved"""
    if not PydanticObjectId.is_valid(anomaly_id):
         raise HTTPException(status_code=404, detail="Invalid Anomaly ID")
         
    anomaly = await models.Anomaly.get(anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    anomaly.status = resolution.status
    anomaly.resolved_at = datetime.now(timezone.utc)
    anomaly.resolved_by = resolution.resolved_by
    anomaly.resolution_notes = resolution.resolution_notes
    
    await anomaly.save()
    
    return {"message": "Anomaly resolved successfully", "anomaly": anomaly}


@router.post("/{anomaly_id}/mitigation/{strategy_id}/implement")
async def implement_mitigation(
    anomaly_id: str,
    strategy_id: str,
    implementation: schemas.MitigationImplement
):
    """Mark mitigation strategy as implemented"""
    if not PydanticObjectId.is_valid(anomaly_id) or not PydanticObjectId.is_valid(strategy_id):
         raise HTTPException(status_code=404, detail="Invalid ID")

    strategy = await models.MitigationStrategy.find_one(
        models.MitigationStrategy.id == PydanticObjectId(strategy_id),
        models.MitigationStrategy.anomaly_id == PydanticObjectId(anomaly_id)
    )
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Mitigation strategy not found")
    
    strategy.implemented = True
    strategy.implemented_at = datetime.now(timezone.utc)
    strategy.implemented_by = implementation.implemented_by
    
    await strategy.save()
    
    return {"message": "Mitigation strategy marked as implemented", "strategy": strategy}
