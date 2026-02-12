"""
ML operations routes
Model training, prediction, and metadata
"""
from fastapi import APIRouter, HTTPException
import numpy as np
import models
import schemas
from ml.anomaly_detector import AnomalyDetector, create_training_data
from ml.feature_engineering import calculate_behavioral_fingerprint, features_to_array
from ml.explainability import ExplainabilityEngine
from beanie import PydanticObjectId

router = APIRouter()


@router.post("/train")
@router.get("/train")
async def train_model():
    """Train or retrain the anomaly detection model"""
    # Get all employees
    employees = await models.Employee.find_all().to_list()
    
    if len(employees) < 1:
        raise HTTPException(
            status_code=400,
            detail="Need at least 1 employee with behavioral data to train model"
        )
    
    # Calculate fingerprints for all employees
    fingerprints = []
    for employee in employees:
        features = await calculate_behavioral_fingerprint(str(employee.id), days_back=30)
        if features:
            fingerprints.append(features)
            
            # Save fingerprint to database
            db_fingerprint = models.BehavioralFingerprint(
                employee_id=employee.id,
                **features
            )
            await db_fingerprint.create()
    
    if len(fingerprints) < 1:
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
async def get_model_info():
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
async def predict_anomaly(request: schemas.PredictionRequest):
    """Manual prediction endpoint"""
    # Verify employee exists
    if PydanticObjectId.is_valid(request.employee_id):
        employee = await models.Employee.get(request.employee_id)
    else:
        employee = await models.Employee.find_one(models.Employee.employee_id == request.employee_id)

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
