"""
SHAP-based explainability for anomaly detection
Provides interpretable explanations for why an employee was flagged as anomalous
"""
import shap
import numpy as np
from typing import Dict, List, Tuple
from ml.feature_engineering import get_feature_names


class ExplainabilityEngine:
    """
    Provides SHAP-based explanations for anomaly predictions
    """
    
    def __init__(self, model, background_data: np.ndarray = None):
        """
        Initialize explainability engine
        
        Args:
            model: Trained Isolation Forest model
            background_data: Background dataset for SHAP (optional)
        """
        self.model = model
        self.background_data = background_data
        self.explainer = None
        
        if model is not None:
            self._initialize_explainer()
    
    def _initialize_explainer(self):
        """Initialize SHAP explainer"""
        try:
            # Use TreeExplainer for Isolation Forest
            self.explainer = shap.TreeExplainer(self.model)
        except Exception as e:
            print(f"Warning: Could not initialize SHAP explainer: {e}")
            self.explainer = None
    
    def explain(self, features: np.ndarray) -> Dict:
        """
        Generate SHAP explanation for a prediction
        
        Args:
            features: Feature vector (1, n_features)
            
        Returns:
            Dictionary with SHAP values and top features
        """
        if self.explainer is None:
            return self._fallback_explanation(features)
        
        try:
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(features)
            
            # Get feature names
            feature_names = get_feature_names()
            
            # Create dictionary of feature -> SHAP value
            shap_dict = {}
            for i, name in enumerate(feature_names):
                shap_dict[name] = float(shap_values[0][i])
            
            # Get top contributing features (by absolute value)
            top_features = self._get_top_features(shap_dict, features[0])
            
            return {
                'shap_values': shap_dict,
                'top_features': top_features
            }
        except Exception as e:
            print(f"Error calculating SHAP values: {e}")
            return self._fallback_explanation(features)
    
    def _get_top_features(self, shap_values: Dict[str, float], feature_values: np.ndarray, top_n: int = 5) -> List[Dict]:
        """
        Get top contributing features sorted by absolute SHAP value
        
        Args:
            shap_values: Dictionary of feature -> SHAP value
            feature_values: Actual feature values
            top_n: Number of top features to return
            
        Returns:
            List of dictionaries with feature info
        """
        feature_names = get_feature_names()
        
        # Sort by absolute SHAP value
        sorted_features = sorted(
            shap_values.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:top_n]
        
        top_features = []
        for feature_name, shap_value in sorted_features:
            # Get feature index
            feature_idx = feature_names.index(feature_name)
            feature_value = float(feature_values[feature_idx])
            
            # Determine impact direction
            impact = 'increases' if shap_value > 0 else 'decreases'
            
            top_features.append({
                'feature': feature_name,
                'feature_display': self._format_feature_name(feature_name),
                'value': feature_value,
                'shap_value': shap_value,
                'impact': impact,
                'description': self._get_feature_description(feature_name, feature_value, shap_value)
            })
        
        return top_features
    
    def _format_feature_name(self, feature_name: str) -> str:
        """Convert feature name to human-readable format"""
        name_map = {
            'avg_login_hour': 'Average Login Hour',
            'login_hour_std': 'Login Time Variability',
            'unique_locations_count': 'Unique Locations',
            'avg_location_distance': 'Location Deviation',
            'unique_ports_count': 'Unique Ports',
            'avg_port_number': 'Average Port Number',
            'file_access_rate': 'File Access Rate',
            'sensitive_file_access_rate': 'Sensitive File Access',
            'privilege_escalation_rate': 'Privilege Escalation Rate',
            'firewall_change_rate': 'Firewall Changes',
            'network_activity_volume': 'Network Activity',
            'failed_login_rate': 'Failed Login Rate',
            'weekday_activity_ratio': 'Weekday Activity Ratio',
            'night_activity_ratio': 'Night Activity Ratio'
        }
        return name_map.get(feature_name, feature_name.replace('_', ' ').title())
    
    def _get_feature_description(self, feature_name: str, value: float, shap_value: float) -> str:
        """Generate human-readable description of feature contribution"""
        impact = 'increases' if shap_value > 0 else 'decreases'
        
        descriptions = {
            'avg_login_hour': f'Login at {value:.1f}:00 {impact} anomaly risk',
            'login_hour_std': f'Login time variability of {value:.2f} hours {impact} risk',
            'unique_locations_count': f'{int(value)} unique locations {impact} risk',
            'avg_location_distance': f'{value:.2%} location deviation {impact} risk',
            'unique_ports_count': f'{int(value)} unique ports accessed {impact} risk',
            'avg_port_number': f'Average port {int(value)} {impact} risk',
            'file_access_rate': f'{value:.1f} files/day {impact} risk',
            'sensitive_file_access_rate': f'{value:.2f} sensitive files/day {impact} risk',
            'privilege_escalation_rate': f'{value:.2f} privilege escalations/day {impact} risk',
            'firewall_change_rate': f'{value:.2f} firewall changes/week {impact} risk',
            'network_activity_volume': f'{value:.1f} network events/day {impact} risk',
            'failed_login_rate': f'{value:.2f} failed logins/day {impact} risk',
            'weekday_activity_ratio': f'{value:.1%} weekday activity {impact} risk',
            'night_activity_ratio': f'{value:.1%} night activity {impact} risk'
        }
        
        return descriptions.get(feature_name, f'{feature_name}: {value:.2f} {impact} risk')
    
    def _fallback_explanation(self, features: np.ndarray) -> Dict:
        """
        Fallback explanation when SHAP is not available
        Uses simple heuristics based on feature values
        """
        feature_names = get_feature_names()
        feature_values = features[0]
        
        # Simple heuristic: features far from "normal" contribute more
        normal_values = {
            'avg_login_hour': 9.0,
            'login_hour_std': 2.0,
            'unique_locations_count': 1,
            'avg_location_distance': 0.0,
            'unique_ports_count': 3,
            'avg_port_number': 443.0,
            'file_access_rate': 5.0,
            'sensitive_file_access_rate': 0.1,
            'privilege_escalation_rate': 0.5,
            'firewall_change_rate': 0.0,
            'network_activity_volume': 10.0,
            'failed_login_rate': 0.0,
            'weekday_activity_ratio': 0.8,
            'night_activity_ratio': 0.05
        }
        
        shap_dict = {}
        deviations = []
        
        for i, name in enumerate(feature_names):
            value = feature_values[i]
            normal = normal_values.get(name, 0.0)
            
            # Calculate deviation (normalized)
            if normal != 0:
                deviation = abs(value - normal) / abs(normal)
            else:
                deviation = abs(value)
            
            # Pseudo-SHAP value based on deviation
            pseudo_shap = deviation * (1 if value > normal else -1)
            shap_dict[name] = float(pseudo_shap)
            
            deviations.append((name, abs(pseudo_shap), value, pseudo_shap))
        
        # Sort by deviation
        deviations.sort(key=lambda x: x[1], reverse=True)
        
        top_features = []
        for name, _, value, pseudo_shap in deviations[:5]:
            impact = 'increases' if pseudo_shap > 0 else 'decreases'
            top_features.append({
                'feature': name,
                'feature_display': self._format_feature_name(name),
                'value': float(value),
                'shap_value': float(pseudo_shap),
                'impact': impact,
                'description': self._get_feature_description(name, value, pseudo_shap)
            })
        
        return {
            'shap_values': shap_dict,
            'top_features': top_features
        }
