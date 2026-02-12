"""
Event ingestion and retrieval routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
import models
import schemas
from database import get_db

router = APIRouter()


@router.post("/", response_model=schemas.BehavioralEvent)
def create_event(event: schemas.BehavioralEventCreate, db: Session = Depends(get_db)):
    """Submit a new behavioral event"""
    # Verify employee exists
    employee = db.query(models.Employee).filter(models.Employee.id == event.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Create event
    db_event = models.BehavioralEvent(**event.model_dump())
    if db_event.timestamp is None:
        db_event.timestamp = datetime.now(timezone.utc)
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # Trigger anomaly detection for this event
    from ml.feature_engineering import extract_features_from_recent_events, features_to_array
    from ml.anomaly_detector import AnomalyDetector
    from ml.explainability import ExplainabilityEngine
    from ml.mitre_mapper import MitreMapper, determine_anomaly_type, generate_anomaly_description
    from ml.mitigation_engine import MitigationEngine
    
    try:
        # Extract recent features
        features = extract_features_from_recent_events(db, event.employee_id, hours_back=24)
        feature_array = features_to_array(features)
        
        # Load detector and predict
        detector = AnomalyDetector()
        if detector.isolation_forest is not None:
            prediction = detector.predict_single(feature_array)
            
            # Only create anomaly record if detected
            if prediction['is_anomaly']:
                # Get SHAP explanation
                explainer = ExplainabilityEngine(detector.isolation_forest)
                explanation = explainer.explain(feature_array)
                
                # Determine anomaly type
                anomaly_type = determine_anomaly_type(explanation['top_features'])
                description = generate_anomaly_description(
                    anomaly_type,
                    explanation['top_features'],
                    employee.name
                )
                
                # Create anomaly record
                anomaly = models.Anomaly(
                    employee_id=event.employee_id,
                    anomaly_score=prediction['anomaly_score'],
                    risk_level=prediction['risk_level'],
                    risk_score=prediction['risk_score'],
                    trigger_event_id=db_event.id,
                    description=description,
                    anomaly_type=anomaly_type,
                    shap_values=explanation['shap_values'],
                    top_features=explanation['top_features']
                )
                db.add(anomaly)
                db.commit()
                db.refresh(anomaly)
                
                # Map to MITRE ATT&CK
                mitre_mapper = MitreMapper()
                mitre_mappings = mitre_mapper.map_anomaly(
                    anomaly_type,
                    explanation['top_features'],
                    prediction['risk_score']
                )
                
                for mapping in mitre_mappings:
                    db_mapping = models.MitreMapping(
                        anomaly_id=anomaly.id,
                        **mapping
                    )
                    db.add(db_mapping)
                
                # Generate mitigation strategies
                mitigation_engine = MitigationEngine()
                strategies = mitigation_engine.generate_strategies(
                    anomaly_type,
                    prediction['risk_level'],
                    mitre_mappings
                )
                
                for strategy in strategies:
                    db_strategy = models.MitigationStrategy(
                        anomaly_id=anomaly.id,
                        **strategy
                    )
                    db.add(db_strategy)
                
                db.commit()
    except Exception as e:
        print(f"Error in anomaly detection: {e}")
        # Don't fail the event creation if anomaly detection fails
    
    return db_event


@router.post("/bulk")
def create_events_bulk(events: List[schemas.BehavioralEventCreate], db: Session = Depends(get_db)):
    """Bulk event ingestion"""
    created_events = []
    
    for event_data in events:
        # Verify employee exists
        employee = db.query(models.Employee).filter(
            models.Employee.id == event_data.employee_id
        ).first()
        if not employee:
            continue  # Skip invalid employees
        
        db_event = models.BehavioralEvent(**event_data.model_dump())
        if db_event.timestamp is None:
            db_event.timestamp = datetime.now(timezone.utc)
        
        db.add(db_event)
        created_events.append(db_event)
    
    db.commit()
    
    return {"created": len(created_events), "total": len(events)}


@router.get("/{employee_id}", response_model=List[schemas.BehavioralEvent])
def get_employee_events(
    employee_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get events for a specific employee"""
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    events = db.query(models.BehavioralEvent).filter(
        models.BehavioralEvent.employee_id == employee_id
    ).order_by(models.BehavioralEvent.timestamp.desc()).offset(skip).limit(limit).all()
    
    return events
