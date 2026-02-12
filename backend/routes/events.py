"""
Event ingestion and retrieval routes
"""
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timezone
import models
import schemas
from beanie import PydanticObjectId

router = APIRouter()


@router.post("/", response_model=schemas.BehavioralEvent)
async def create_event(event: schemas.BehavioralEventCreate):
    """Submit a new behavioral event"""
    # Verify employee exists
    if PydanticObjectId.is_valid(event.employee_id):
        employee = await models.Employee.get(event.employee_id)
    else:
        employee = await models.Employee.find_one(models.Employee.employee_id == event.employee_id)
        
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Create event
    # Ensure employee_id in event is the PydanticObjectId string
    event_data = event.model_dump()
    event_data['employee_id'] = str(employee.id)
    
    db_event = models.BehavioralEvent(**event_data)
    if db_event.timestamp is None:
        db_event.timestamp = datetime.now(timezone.utc)
    
    await db_event.create()
    
    # Trigger anomaly detection
    await process_event_anomaly(str(employee.id), db_event, employee.name)
    
    return db_event


@router.post("/bulk")
async def create_events_bulk(events: List[schemas.BehavioralEventCreate]):
    """Bulk event ingestion"""
    created_events = []
    
    # Pre-fetch employees to optimize
    # For now, just simplistic approach
    
    for event_data in events:
        # Verify employee exists
        if PydanticObjectId.is_valid(event_data.employee_id):
            employee = await models.Employee.get(event_data.employee_id)
        else:
            employee = await models.Employee.find_one(models.Employee.employee_id == event_data.employee_id)
            
        if not employee:
            continue  # Skip invalid employees
        
        data = event_data.model_dump()
        data['employee_id'] = str(employee.id)
        
        db_event = models.BehavioralEvent(**data)
        if db_event.timestamp is None:
            db_event.timestamp = datetime.now(timezone.utc)
        
        await db_event.create()
        created_events.append(db_event)
        
        # Trigger anomaly detection for each event
        # In production this should be async/background task
        await process_event_anomaly(str(employee.id), db_event, employee.name)
        

    
    return {"created": len(created_events), "total": len(events)}





@router.get("/{employee_id}", response_model=List[schemas.BehavioralEvent])
async def get_employee_events(
    employee_id: str,
    skip: int = 0,
    limit: int = 100
):
    """Get events for a specific employee"""
    if PydanticObjectId.is_valid(employee_id):
        employee = await models.Employee.get(employee_id)
    else:
        employee = await models.Employee.find_one(models.Employee.employee_id == employee_id)
        
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    events = await models.BehavioralEvent.find(
        models.BehavioralEvent.employee_id == employee.id
    ).sort(-models.BehavioralEvent.timestamp).skip(skip).limit(limit).to_list()
    
    return events


async def process_event_anomaly(employee_id: str, db_event: models.BehavioralEvent, employee_name: str):
    """Process a single event for anomaly detection"""
    from ml.feature_engineering import extract_features_from_recent_events, features_to_array
    from ml.anomaly_detector import AnomalyDetector
    from ml.explainability import ExplainabilityEngine
    from ml.mitre_mapper import MitreMapper, determine_anomaly_type, generate_anomaly_description
    from ml.mitigation_engine import MitigationEngine
    
    try:
        # Extract recent features
        features = await extract_features_from_recent_events(employee_id, hours_back=24)
        feature_array = features_to_array(features)
        
        # Load detector and predict
        detector = AnomalyDetector()
        
        # Need to check if model is trained
        if detector.isolation_forest is None:
            # Try loading model if not in memory
            if not detector.load_model():
                return
                
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
                    employee_name
                )
                
                # Create anomaly record
                anomaly = models.Anomaly(
                    employee_id=employee_id,
                    anomaly_score=prediction['anomaly_score'],
                    risk_level=prediction['risk_level'],
                    risk_score=prediction['risk_score'],
                    trigger_event_id=db_event.id,
                    description=description,
                    anomaly_type=anomaly_type,
                    shap_values=explanation['shap_values'],
                    top_features=explanation['top_features']
                )
                await anomaly.create()
                
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
                    await db_mapping.create()
                
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
                    await db_strategy.create()
                
    except Exception as e:
        print(f"Error in anomaly detection: {e}")
        # Don't fail the event creation if anomaly detection fails


async def process_event_anomaly(employee_id: str, db_event: models.BehavioralEvent, employee_name: str):
    """Process a single event for anomaly detection"""
    from ml.feature_engineering import extract_features_from_recent_events, features_to_array
    from ml.anomaly_detector import AnomalyDetector
    from ml.explainability import ExplainabilityEngine
    from ml.mitre_mapper import MitreMapper, determine_anomaly_type, generate_anomaly_description
    from ml.mitigation_engine import MitigationEngine
    
    try:
        # 0. Immediate Rule-Based Checks (Bypass ML for specific violations)
        if db_event.event_type == 'policy_violation':
            print(f"🚨 Immediate Policy Violation Detected: {db_event.description}")
            
            # Create anomaly record immediately
            anomaly = models.Anomaly(
                employee_id=employee_id,
                anomaly_score=-1.0, # High anomaly score
                risk_level='critical',
                risk_score=100,
                trigger_event_id=db_event.id,
                description=f"Policy Violation: {db_event.description}",
                anomaly_type='policy_violation',
                shap_values={}, # No SHAP for rule-based
                top_features=[{"feature": "policy_violation", "value": 1.0, "description": "Blocked Execution"}]
            )
            await anomaly.create()
            
            # Create MITRE mapping
            await models.MitreMapping(
                anomaly_id=anomaly.id,
                technique_id="T1204.002",
                technique_name="User Execution: Malicious File",
                tactic="Execution",
                description="User attempted to execute a blocked file extension (.bat/.cmd/.vbs)",
                confidence=1.0
            ).create()
            
            # Create Mitigation Strategy
            await models.MitigationStrategy(
                anomaly_id=anomaly.id,
                strategy_name="Isolate and Educate",
                description="The agent has already blocked the process. Recommend security awareness training for the employee.",
                action_type="automated_blocking",
                status="active"
            ).create()
            
            return

        # Extract recent features
        features = await extract_features_from_recent_events(employee_id, hours_back=24)
        feature_array = features_to_array(features)
        
        # Load detector and predict
        detector = AnomalyDetector()
        
        # Need to check if model is trained
        if detector.isolation_forest is None:
            # Try loading model if not in memory
            if not detector.load_model():
                return
                
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
                    employee_name
                )
                
                # Create anomaly record
                anomaly = models.Anomaly(
                    employee_id=employee_id,
                    anomaly_score=prediction['anomaly_score'],
                    risk_level=prediction['risk_level'],
                    risk_score=prediction['risk_score'],
                    trigger_event_id=db_event.id,
                    description=description,
                    anomaly_type=anomaly_type,
                    shap_values=explanation['shap_values'],
                    top_features=explanation['top_features']
                )
                await anomaly.create()
                
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
                    await db_mapping.create()
                
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
                    await db_strategy.create()
                
    except Exception as e:
        print(f"Error in anomaly detection: {e}")
        # Don't fail the event creation if anomaly detection fails
