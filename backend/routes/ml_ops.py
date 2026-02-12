"""
ML operations routes
Model training, prediction, and metadata
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
import numpy as np
import models
import schemas
from database import get_db
from ml.anomaly_detector import AnomalyDetector, create_training_data
from ml.feature_engineering import calculate_behavioral_fingerprint, features_to_array
from ml.explainability import ExplainabilityEngine

router = APIRouter()


@router.post("/train")
@router.get("/train")
def train_model(db: Session = Depends(get_db)):
    """Train or retrain the anomaly detection model"""
    # Get all employees
    employees = db.query(models.Employee).all()
    
    if len(employees) < 10:
        raise HTTPException(
            status_code=400,
            detail="Need at least 10 employees with behavioral data to train model"
        )
    
    # Calculate fingerprints for all employees
    fingerprints = []
    for employee in employees:
        features = calculate_behavioral_fingerprint(db, employee.id, days_back=30)
        if features:
            fingerprints.append(features)
            
            # Save fingerprint to database
            db_fingerprint = models.BehavioralFingerprint(
                employee_id=employee.id,
                **features
            )
            db.add(db_fingerprint)
    
    db.commit()
    
    if len(fingerprints) < 10:
        raise HTTPException(
            status_code=400,
            detail="Not enough behavioral data to train model"
        )
    
    # Create training data
    X = create_training_data(fingerprints)
    
    # Train model
    detector = AnomalyDetector()
    detector.train(X, contamination=0.1, n_clusters=5)
    
    return {
        "message": "Model trained successfully",
        "n_samples": len(fingerprints),
        "n_features": X.shape[1],
        "model_info": detector.get_model_info()
    }


@router.get("/model-info", response_model=schemas.ModelInfo)
def get_model_info():
    """Get information about the current model"""
    detector = AnomalyDetector()
    
    if detector.isolation_forest is None:
        raise HTTPException(status_code=404, detail="Model not trained yet")
    
    info = detector.get_model_info()
    
    return {
        'model_type': info['model_type'],
        'trained_at': info['trained_at'],
        'n_samples': info['n_samples'],
        'n_features': info['n_features'],
        'accuracy': None  # Could calculate if we have labeled data
    }


@router.post("/predict", response_model=schemas.PredictionResponse)
def predict_anomaly(
    request: schemas.PredictionRequest,
    db: Session = Depends(get_db)
):
    """Manual prediction endpoint"""
    # Verify employee exists
    employee = db.query(models.Employee).filter(
        models.Employee.id == request.employee_id
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Load detector
    detector = AnomalyDetector()
    if detector.isolation_forest is None:
        raise HTTPException(status_code=400, detail="Model not trained yet")
    
    # Convert features to array
    from ml.feature_engineering import get_feature_names
    feature_names = get_feature_names()
    feature_array = np.array([
        request.features.get(name, 0.0) for name in feature_names
    ]).reshape(1, -1)
    
    # Predict
    prediction = detector.predict_single(feature_array)
    
    # Get explanation
    explainer = ExplainabilityEngine(detector.isolation_forest)
    explanation = explainer.explain(feature_array)
    
    return {
        'is_anomaly': prediction['is_anomaly'],
        'anomaly_score': prediction['anomaly_score'],
        'risk_level': prediction['risk_level'],
        'risk_score': prediction['risk_score'],
        'shap_values': explanation['shap_values'],
        'top_features': explanation['top_features']
    }
