"""
Agent management routes for real-time monitoring
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from datetime import datetime
import models
import schemas
from ml.feature_engineering import calculate_behavioral_fingerprint
from ml.anomaly_detector import AnomalyDetector
from ml.explainability import ExplainabilityEngine
from ml.mitre_mapper import MitreMapper
from ml.mitigation_engine import MitigationEngine
import numpy as np
from beanie import PydanticObjectId
from beanie.operators import In

router = APIRouter(prefix="/api/agent", tags=["agent"])

# Initialize ML components
detector = AnomalyDetector()
# Note: ExplainabilityEngine needs a trained model. 
# If model is not trained/loaded, this might fail or need handling.
# For now instantiating with None or handle inside methods if possible.
# Ideally we load this when needed or on startup.
# We will instantiate inside the route to pick up the latest model.

mitre_mapper = MitreMapper()
mitigation_engine = MitigationEngine()


@router.post("/register")
async def register_agent(agent_info: Dict):
    """
    Register a new monitoring agent
    
    Creates a new employee record for the monitored machine
    """
    # Check if employee already exists by hostname
    existing = await models.Employee.find_one(
        models.Employee.name == agent_info.get('hostname')
    )
    
    if existing:
        return {
            "employee_id": str(existing.id),
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
    
    await employee.create()
    
    return {
        "employee_id": str(employee.id),
        "message": "Agent registered successfully",
        "status": "new"
    }


@router.get("/{employee_id}/status")
async def get_agent_status(employee_id: str):
    """
    Get agent status including isolation state
    """
    if PydanticObjectId.is_valid(employee_id):
        employee = await models.Employee.get(employee_id)
    else:
        employee = await models.Employee.find_one(models.Employee.employee_id == employee_id)

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if there are any open critical/high anomalies
    critical_anomalies_count = await models.Anomaly.find(
        models.Anomaly.employee_id == employee.id,
        models.Anomaly.status == "open",
        In(models.Anomaly.risk_level, ["critical", "high"])
    ).count()
    
    # Isolation is now MANUAL controlled by the is_isolated field
    # We no longer auto-isolate based on anomalies
    isolated = employee.is_isolated
    
    return {
        "employee_id": str(employee.id),
        "isolated": isolated,
        "active_threats": critical_anomalies_count,
        "status": "online"
    }


@router.post("/events/batch")
async def receive_batch_events(payload: Dict):
    """
    Receive a batch of events from monitoring agent
    
    Processes events and triggers anomaly detection
    """
    employee_id_raw = payload.get('employee_id')
    events = payload.get('events', [])
    
    if not employee_id_raw:
        raise HTTPException(status_code=400, detail="employee_id required")
    
    # Verify employee exists
    if PydanticObjectId.is_valid(employee_id_raw):
        employee = await models.Employee.get(employee_id_raw)
    else:
        # Fallback to check if it's the raw ID string
        employee = await models.Employee.find_one(models.Employee.id == employee_id_raw)
        if not employee:
             # Fallback to check if it matches employee_id string field
             employee = await models.Employee.find_one(models.Employee.employee_id == employee_id_raw)

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    emp_obj_id = employee.id

    # Store events
    for event_data in events:
        event = models.BehavioralEvent(
            employee_id=emp_obj_id,
            event_type=event_data.get('event_type'),
            timestamp=datetime.fromisoformat(event_data.get('timestamp')),
            location=event_data.get('location'),
            ip_address=event_data.get('ip_address'),
            port=event_data.get('port'),
            file_path=event_data.get('file_path'),
            action=event_data.get('action'),
            success=event_data.get('success', True)
        )
        await event.create()
    
    # Trigger anomaly detection
    try:
        from ml.feature_engineering import get_feature_names
        
        # Calculate behavioral features
        # Assuming calculate_behavioral_fingerprint takes the string ID or PydanticObjectId
        # Our updated feature_engineering expects string id to lookup employee
        features = await calculate_behavioral_fingerprint(str(emp_obj_id), days_back=7)
        
        # Reload detector to check if model exists
        detector = AnomalyDetector()

        if features and detector.isolation_forest is not None:
            # Convert to array
            feature_names = get_feature_names()
            feature_array = np.array([[features.get(name, 0.0) for name in feature_names]])
            
            # Predict anomaly
            result = detector.predict_single(feature_array)
            
            if result['is_anomaly']:
                # Get SHAP explanation
                explainer = ExplainabilityEngine(detector.isolation_forest)
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
                    employee_id=emp_obj_id,
                    anomaly_score=result['anomaly_score'],
                    risk_level=result['risk_level'],
                    risk_score=result['risk_score'],
                    description=description,
                    anomaly_type=anomaly_type,
                    shap_values=explanation['shap_values'],
                    top_features=explanation['top_features'],
                    status='open'
                )
                await anomaly.create()
                
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
                    await mitre_record.create()
                
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
                    await mitigation.create()
                
                return {
                    "status": "success",
                    "events_received": len(events),
                    "anomaly_detected": True,
                    "risk_level": result['risk_level'],
                    "anomaly_id": str(anomaly.id)
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
async def isolate_agent(employee_id: str):
    """
    Command to isolate an agent from the network
    """
    if PydanticObjectId.is_valid(employee_id):
         employee = await models.Employee.get(employee_id)
    else:
         employee = await models.Employee.find_one(models.Employee.employee_id == employee_id)

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Update isolation status
    employee.is_isolated = True
    await employee.save()
    
    # Mark open anomalies as investigating
    anomalies = await models.Anomaly.find(
        models.Anomaly.employee_id == employee.id,
        models.Anomaly.status == "open"
    ).to_list()
    
    for anomaly in anomalies:
        anomaly.status = "investigating"
        await anomaly.save()
    
    return {
        "status": "success",
        "message": f"Isolation command sent for {employee.name}",
        "isolated": True
    }


@router.post("/{employee_id}/restore")
async def restore_agent(employee_id: str):
    """
    Command to restore agent network connectivity
    """
    if PydanticObjectId.is_valid(employee_id):
         employee = await models.Employee.get(employee_id)
    else:
         employee = await models.Employee.find_one(models.Employee.employee_id == employee_id)
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Update isolation status
    employee.is_isolated = False
    await employee.save()
    
    return {
        "status": "success",
        "message": f"Network restored for {employee.name}",
        "isolated": False
    }
