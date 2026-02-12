"""
Anomaly detection using Isolation Forest and K-Means clustering
"""
import pickle
import os
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from datetime import datetime
from typing import Tuple, Dict, Optional
import pandas as pd


class AnomalyDetector:
    """
    Hybrid anomaly detection using Isolation Forest and K-Means
    """
    
    def __init__(self, model_path: str = "./models/"):
        self.model_path = model_path
        self.isolation_forest = None
        self.kmeans = None
        self.scaler = StandardScaler()
        self.trained_at = None
        self.n_samples = 0
        self.n_features = 0
        
        # Create models directory if it doesn't exist
        os.makedirs(model_path, exist_ok=True)
        
        # Try to load existing model
        self.load_model()
    
    def train(self, X: np.ndarray, contamination: float = 0.1, n_clusters: int = 5):
        """
        Train anomaly detection models
        
        Args:
            X: Training data (n_samples, n_features)
            contamination: Expected proportion of outliers
            n_clusters: Number of clusters for K-Means
        """
        self.n_samples, self.n_features = X.shape
        
        # Standardize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.isolation_forest.fit(X_scaled)
        
        # Train K-Means for behavioral clustering
        self.kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10
        )
        self.kmeans.fit(X_scaled)
        
        self.trained_at = datetime.utcnow()
        
        # Save model
        self.save_model()
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Predict anomalies
        
        Args:
            X: Input data (n_samples, n_features)
            
        Returns:
            predictions: -1 for anomaly, 1 for normal
            scores: Anomaly scores (lower = more anomalous)
            clusters: Cluster assignments
        """
        if self.isolation_forest is None:
            raise ValueError("Model not trained. Call train() first.")
        
        X_scaled = self.scaler.transform(X)
        
        # Isolation Forest predictions
        predictions = self.isolation_forest.predict(X_scaled)
        scores = self.isolation_forest.score_samples(X_scaled)
        
        # K-Means cluster assignment
        clusters = self.kmeans.predict(X_scaled)
        
        return predictions, scores, clusters
    
    def predict_single(self, features: np.ndarray) -> Dict:
        """
        Predict anomaly for a single sample with detailed output
        
        Args:
            features: Feature vector (1, n_features)
            
        Returns:
            Dictionary with prediction details
        """
        predictions, scores, clusters = self.predict(features)
        
        is_anomaly = predictions[0] == -1
        anomaly_score = float(scores[0])
        cluster = int(clusters[0])
        
        # Calculate risk score (0-100)
        # Isolation Forest scores typically range from -0.5 to 0.5
        # More negative = more anomalous
        risk_score = self._calculate_risk_score(anomaly_score)
        risk_level = self._get_risk_level(risk_score)
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': anomaly_score,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'cluster': cluster
        }
    
    def _calculate_risk_score(self, anomaly_score: float) -> int:
        """
        Convert anomaly score to risk score (0-100)
        
        Isolation Forest scores typically range from -0.5 (very anomalous) to 0.5 (very normal)
        """
        # Normalize to 0-100 scale
        # -0.5 -> 100, 0.5 -> 0
        normalized = (0.5 - anomaly_score) * 100
        risk_score = int(np.clip(normalized, 0, 100))
        return risk_score
    
    def _get_risk_level(self, risk_score: int) -> str:
        """
        Convert risk score to risk level category
        """
        if risk_score >= 80:
            return 'critical'
        elif risk_score >= 60:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        else:
            return 'low'
    
    def save_model(self):
        """Save trained models to disk"""
        if self.isolation_forest is None:
            return
        
        model_data = {
            'isolation_forest': self.isolation_forest,
            'kmeans': self.kmeans,
            'scaler': self.scaler,
            'trained_at': self.trained_at,
            'n_samples': self.n_samples,
            'n_features': self.n_features
        }
        
        model_file = os.path.join(self.model_path, 'anomaly_detector.pkl')
        with open(model_file, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self) -> bool:
        """
        Load trained models from disk
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        model_file = os.path.join(self.model_path, 'anomaly_detector.pkl')
        
        if not os.path.exists(model_file):
            return False
        
        try:
            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)
            
            self.isolation_forest = model_data['isolation_forest']
            self.kmeans = model_data['kmeans']
            self.scaler = model_data['scaler']
            self.trained_at = model_data['trained_at']
            self.n_samples = model_data['n_samples']
            self.n_features = model_data['n_features']
            
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """Get model metadata"""
        return {
            'model_type': 'Isolation Forest + K-Means',
            'trained_at': self.trained_at,
            'n_samples': self.n_samples,
            'n_features': self.n_features,
            'is_trained': self.isolation_forest is not None
        }


def create_training_data(fingerprints: list) -> np.ndarray:
    """
    Convert list of fingerprint dictionaries to training matrix
    
    Args:
        fingerprints: List of fingerprint dictionaries
        
    Returns:
        Training matrix (n_samples, n_features)
    """
    from ml.feature_engineering import get_feature_names
    
    feature_names = get_feature_names()
    X = []
    
    for fp in fingerprints:
        features = [fp.get(name, 0.0) for name in feature_names]
        X.append(features)
    
    return np.array(X)
