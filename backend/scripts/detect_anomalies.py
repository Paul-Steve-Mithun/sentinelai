"""
Script to trigger anomaly detection on all existing events
"""
import sys
import os
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
import models
from ml.feature_engineering import calculate_behavioral_fingerprint
from ml.anomaly_detector import AnomalyDetector
from ml.explainability import ExplainabilityEngine
from ml.mitre_mapper import MitreMapper
from ml.mitigation_engine import MitigationEngine
from datetime import datetime, timedelta, timezone

def detect_anomalies():
    """Run anomaly detection on all employees"""
    db = SessionLocal()
    
    try:
        print("🔍 Starting anomaly detection...")
        
        # Initialize ML components
        detector = AnomalyDetector()
        explainer = ExplainabilityEngine(detector)
        mitre_mapper = MitreMapper()
        mitigation_engine = MitigationEngine()
        
        # Load the trained model
        try:
            detector.load_model()
            print("✓ Model loaded successfully")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("Please train the model first: POST http://localhost:8000/api/ml/train")
            return
        
        # Get all employees
        employees = db.query(models.Employee).all()
        print(f"✓ Found {len(employees)} employees")
        
        total_anomalies = 0
        
        for employee in employees:
            print(f"\nProcessing {employee.name} (ID: {employee.id})...")
            
            # Get recent events (last 24 hours)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_events = db.query(models.BehavioralEvent).filter(
                models.BehavioralEvent.employee_id == employee.id,
                models.BehavioralEvent.timestamp >= cutoff
            ).all()
            
            if not recent_events:
                print(f"  No recent events for {employee.name}")
                continue
            
            print(f"  Found {len(recent_events)} recent events")
            
            # Calculate behavioral features
            features = calculate_behavioral_fingerprint(db, employee.id, days_back=30)
            if not features:
                print(f"  Insufficient data for {employee.name}")
                continue
            
            # Convert features dict to array
            from ml.feature_engineering import get_feature_names
            feature_names = get_feature_names()
            feature_array = np.array([[features.get(name, 0.0) for name in feature_names]])
            
            # Predict anomaly
            result = detector.predict_single(feature_array)
            
            if result['is_anomaly']:
                print(f"  🚨 ANOMALY DETECTED! Risk: {result['risk_level']} ({result['risk_score']})")
                
                # Get SHAP explanation
                explanation = explainer.explain(feature_array)
                
                # Determine anomaly type based on top features
                top_feature = explanation['top_features'][0]['feature'] if explanation['top_features'] else 'unknown'
                anomaly_type_map = {
                    'avg_login_hour': 'unusual_login',
                    'login_hour_std': 'unusual_login',
                    'avg_location_distance': 'unusual_location',
                    'unique_ports_count': 'unusual_port',
                    'sensitive_file_access_rate': 'sensitive_files',
                    'privilege_escalation_rate': 'privilege_escalation',
                    'firewall_change_rate': 'firewall_change',
                    'failed_login_rate': 'failed_logins'
                }
                anomaly_type = anomaly_type_map.get(top_feature, 'behavioral_anomaly')
                
                # Create anomaly description
                description = f"Anomalous behavior detected for {employee.name}. "
                if explanation['top_features']:
                    top_contrib = explanation['top_features'][0]
                    description += top_contrib['description']
                
                # Save anomaly to database
                anomaly = models.Anomaly(
                    employee_id=employee.id,
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
                total_anomalies += 1
                print(f"  ✓ Anomaly saved with {len(mappings)} MITRE mappings and {len(strategies)} mitigations")
            else:
                print(f"  ✓ Normal behavior")
        
        print(f"\n✅ Anomaly detection complete!")
        print(f"   Total anomalies detected: {total_anomalies}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    detect_anomalies()
