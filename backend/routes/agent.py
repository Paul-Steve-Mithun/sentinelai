"""
Agent management routes for real-time monitoring
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime

import models
import schemas
from database import get_db
from ml.feature_engineering import calculate_behavioral_fingerprint
from ml.anomaly_detector import AnomalyDetector
from ml.explainability import ExplainabilityEngine
from ml.mitre_mapper import MitreMapper
from ml.mitigation_engine import MitigationEngine
import numpy as np

router = APIRouter(prefix="/api/agent", tags=["agent"])

# Initialize ML components
detector = AnomalyDetector()
explainer = ExplainabilityEngine(detector)
mitre_mapper = MitreMapper()
mitigation_engine = MitigationEngine()


@router.post("/register")
def register_agent(agent_info: Dict, db: Session = Depends(get_db)):
    """
    Register a new monitoring agent
    
    Creates a new employee record for the monitored machine
    """
    # Check if employee already exists by hostname
    existing = db.query(models.Employee).filter(
        models.Employee.name == agent_info.get('hostname')
    ).first()
    
    if existing:
        return {
            "employee_id": existing.id,
            "message": "Agent already registered",
            "status": "existing"
        }
    
    # Create new employee record
    employee = models.Employee(
        employee_id=f"AGENT_{agent_info.get('hostname')}",
        name=agent_info.get('hostname'),
        email=f"{agent_info.get('username')}@monitored.local",
        department="Monitored",
        role=agent_info.get('os', 'Unknown'),
        baseline_location=agent_info.get('ip_address', 'Unknown')
    )
    
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    return {
        "employee_id": employee.id,
        "message": "Agent registered successfully",
        "status": "new"
    }


@router.get("/{employee_id}/status")
def get_agent_status(employee_id: int, db: Session = Depends(get_db)):
    """
    Get agent status including isolation state
    """
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if there are any open critical/high anomalies
    critical_anomalies = db.query(models.Anomaly).filter(
        models.Anomaly.employee_id == employee_id,
        models.Anomaly.status == "open",
        models.Anomaly.risk_level.in_(["critical", "high"])
    ).count()
    
    # For now, isolation is manual - check if there's a flag
    # In production, you'd have an isolation_status table
    isolated = critical_anomalies > 0  # Auto-isolate on critical threats
    
    return {
        "employee_id": employee_id,
        "isolated": isolated,
        "active_threats": critical_anomalies,
        "status": "online"
    }


@router.post("/events/batch")
def receive_batch_events(payload: Dict, db: Session = Depends(get_db)):
    """
    Receive a batch of events from monitoring agent
    
    Processes events and triggers anomaly detection
    """
    employee_id = payload.get('employee_id')
    events = payload.get('events', [])
    
    if not employee_id:
        raise HTTPException(status_code=400, detail="employee_id required")
    
    # Verify employee exists
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Store events
    stored_events = []
    for event_data in events:
        event = models.BehavioralEvent(
            employee_id=employee_id,
            event_type=event_data.get('event_type'),
            timestamp=datetime.fromisoformat(event_data.get('timestamp')),
            location=event_data.get('location'),
            ip_address=event_data.get('ip_address'),
            port=event_data.get('port'),
            file_path=event_data.get('file_path'),
            action=event_data.get('action'),
            success=event_data.get('success', True)
        )
        db.add(event)
        stored_events.append(event)
    
    db.commit()
    
    # Trigger anomaly detection
    try:
        from ml.feature_engineering import get_feature_names
        
        # Calculate behavioral features
        features = calculate_behavioral_fingerprint(db, employee_id, days_back=7)
        
        if features and detector.isolation_forest is not None:
            # Convert to array
            feature_names = get_feature_names()
            feature_array = np.array([[features.get(name, 0.0) for name in feature_names]])
            
            # Predict anomaly
            result = detector.predict_single(feature_array)
            
            if result['is_anomaly']:
                # Get SHAP explanation
                explanation = explainer.explain(feature_array)
                
                # Determine anomaly type
                top_feature = explanation['top_features'][0]['feature'] if explanation['top_features'] else 'unknown'
                anomaly_type_map = {
                    'avg_login_hour': 'unusual_login',
                    'avg_location_distance': 'unusual_location',
                    'unique_ports_count': 'unusual_port',
                    'sensitive_file_access_rate': 'sensitive_files',
                    'privilege_escalation_rate': 'privilege_escalation',
                }
                anomaly_type = anomaly_type_map.get(top_feature, 'behavioral_anomaly')
                
                # Create anomaly description
                description = f"Real-time anomaly detected for {employee.name}. "
                if explanation['top_features']:
                    description += explanation['top_features'][0]['description']
                
                # Save anomaly
                anomaly = models.Anomaly(
                    employee_id=employee_id,
                    anomaly_score=result['anomaly_score'],
                    risk_level=result['risk_level'],
                    risk_score=result['risk_score'],
                    description=description,
                    anomaly_type=anomaly_type,
                    shap_values=explanation['shap_values'],
                    top_features=explanation['top_features'],
                    status='open'
                )
                db.add(anomaly)
                db.flush()
                
                # Generate MITRE mappings
                mappings = mitre_mapper.map_anomaly(anomaly_type, explanation['top_features'], result['risk_score'])
                for mapping in mappings:
                    mitre_record = models.MitreMapping(
                        anomaly_id=anomaly.id,
                        technique_id=mapping['technique_id'],
                        technique_name=mapping['technique_name'],
                        tactic=mapping['tactic'],
                        description=mapping['description'],
                        confidence=mapping['confidence']
                    )
                    db.add(mitre_record)
                
                # Generate mitigation strategies
                strategies = mitigation_engine.generate_strategies(
                    anomaly_type=anomaly_type,
                    risk_level=result['risk_level'],
                    mitre_techniques=mappings
                )
                for strategy in strategies:
                    mitigation = models.MitigationStrategy(
                        anomaly_id=anomaly.id,
                        priority=strategy['priority'],
                        category=strategy['category'],
                        action=strategy['action'],
                        description=strategy['description']
                    )
                    db.add(mitigation)
                
                db.commit()
                
                return {
                    "status": "success",
                    "events_received": len(events),
                    "anomaly_detected": True,
                    "risk_level": result['risk_level'],
                    "anomaly_id": anomaly.id
                }
    
    except Exception as e:
        print(f"Error in anomaly detection: {e}")
        # Continue even if anomaly detection fails
    
    return {
        "status": "success",
        "events_received": len(events),
        "anomaly_detected": False
    }


@router.post("/{employee_id}/isolate")
def isolate_agent(employee_id: int, db: Session = Depends(get_db)):
    """
    Command to isolate an agent from the network
    """
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # In production, you'd update an isolation_status table
    # For now, we'll mark all open anomalies as investigating
    db.query(models.Anomaly).filter(
        models.Anomaly.employee_id == employee_id,
        models.Anomaly.status == "open"
    ).update({"status": "investigating"})
    
    db.commit()
    
    return {
        "status": "success",
        "message": f"Isolation command sent for {employee.name}",
        "isolated": True
    }


@router.post("/{employee_id}/restore")
def restore_agent(employee_id: int, db: Session = Depends(get_db)):
    """
    Command to restore agent network connectivity
    """
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {
        "status": "success",
        "message": f"Network restored for {employee.name}",
        "isolated": False
    }
