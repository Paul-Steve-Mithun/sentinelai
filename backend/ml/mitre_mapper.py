"""
MITRE ATT&CK Framework mapper
Maps detected anomalies to MITRE ATT&CK tactics and techniques
"""
from typing import List, Dict, Tuple
import re


class MitreMapper:
    """
    Maps behavioral anomalies to MITRE ATT&CK framework
    """
    
    def __init__(self):
        # Define MITRE ATT&CK technique mappings
        self.technique_database = {
            'T1078': {
                'name': 'Valid Accounts',
                'tactic': 'Initial Access / Persistence',
                'description': 'Adversaries may obtain and abuse credentials of existing accounts',
                'indicators': ['unusual_login', 'failed_login', 'night_activity', 'location_variance']
            },
            'T1021': {
                'name': 'Remote Services',
                'tactic': 'Lateral Movement',
                'description': 'Adversaries may use valid accounts to log into a service',
                'indicators': ['unusual_port', 'network_activity', 'unique_ports']
            },
            'T1068': {
                'name': 'Exploitation for Privilege Escalation',
                'tactic': 'Privilege Escalation',
                'description': 'Adversaries may exploit software vulnerabilities to elevate privileges',
                'indicators': ['privilege_escalation', 'unusual_sudo']
            },
            'T1048': {
                'name': 'Exfiltration Over Alternative Protocol',
                'tactic': 'Exfiltration',
                'description': 'Adversaries may steal data by exfiltrating it over a different protocol',
                'indicators': ['unusual_port', 'network_activity', 'large_transfer']
            },
            'T1562': {
                'name': 'Impair Defenses',
                'tactic': 'Defense Evasion',
                'description': 'Adversaries may maliciously modify components to impair defenses',
                'indicators': ['firewall_change', 'security_config']
            },
            'T1530': {
                'name': 'Data from Cloud Storage',
                'tactic': 'Collection',
                'description': 'Adversaries may access data from cloud storage',
                'indicators': ['sensitive_file_access', 'unusual_file_access', 'bulk_download']
            },
            'T1110': {
                'name': 'Brute Force',
                'tactic': 'Credential Access',
                'description': 'Adversaries may use brute force techniques to gain access',
                'indicators': ['failed_login', 'multiple_login_attempts']
            },
            'T1098': {
                'name': 'Account Manipulation',
                'tactic': 'Persistence',
                'description': 'Adversaries may manipulate accounts to maintain access',
                'indicators': ['privilege_escalation', 'account_modification']
            }
        }
    
    def map_anomaly(self, anomaly_type: str, top_features: List[Dict], risk_score: int) -> List[Dict]:
        """
        Map an anomaly to MITRE ATT&CK techniques
        
        Args:
            anomaly_type: Type of anomaly detected
            top_features: Top contributing features from SHAP
            risk_score: Risk score of the anomaly
            
        Returns:
            List of MITRE technique mappings with confidence scores
        """
        mappings = []
        
        # Extract feature names from top features
        feature_names = [f['feature'] for f in top_features]
        
        # Check each technique for matches
        for technique_id, technique_info in self.technique_database.items():
            confidence = self._calculate_confidence(
                anomaly_type,
                feature_names,
                technique_info['indicators'],
                risk_score
            )
            
            if confidence > 0.3:  # Threshold for inclusion
                mappings.append({
                    'technique_id': technique_id,
                    'technique_name': technique_info['name'],
                    'tactic': technique_info['tactic'],
                    'description': technique_info['description'],
                    'confidence': confidence
                })
        
        # Sort by confidence
        mappings.sort(key=lambda x: x['confidence'], reverse=True)
        
        return mappings
    
    def _calculate_confidence(
        self,
        anomaly_type: str,
        feature_names: List[str],
        indicators: List[str],
        risk_score: int
    ) -> float:
        """
        Calculate confidence score for a technique mapping
        
        Args:
            anomaly_type: Type of anomaly
            feature_names: List of contributing feature names
            indicators: List of indicators for this technique
            risk_score: Risk score (0-100)
            
        Returns:
            Confidence score (0-1)
        """
        confidence = 0.0
        
        # Check anomaly type match
        for indicator in indicators:
            if indicator in anomaly_type:
                confidence += 0.4
                break
        
        # Check feature matches
        feature_matches = 0
        for feature in feature_names:
            for indicator in indicators:
                if indicator in feature or feature in indicator:
                    feature_matches += 1
                    break
        
        if len(indicators) > 0:
            feature_confidence = (feature_matches / len(indicators)) * 0.4
            confidence += feature_confidence
        
        # Risk score contribution
        risk_confidence = (risk_score / 100) * 0.2
        confidence += risk_confidence
        
        return min(confidence, 1.0)
    
    def get_technique_details(self, technique_id: str) -> Dict:
        """Get detailed information about a specific technique"""
        return self.technique_database.get(technique_id, {})
    
    def get_all_techniques(self) -> Dict:
        """Get all techniques in the database"""
        return self.technique_database


def determine_anomaly_type(top_features: List[Dict]) -> str:
    """
    Determine the primary anomaly type based on top contributing features
    
    Args:
        top_features: List of top contributing features
        
    Returns:
        Anomaly type string
    """
    if not top_features:
        return 'unknown'
    
    # Get the top feature
    top_feature = top_features[0]['feature']
    
    # Map features to anomaly types
    type_mapping = {
        'avg_login_hour': 'unusual_login_time',
        'login_hour_std': 'unusual_login_pattern',
        'unique_locations_count': 'unusual_location',
        'avg_location_distance': 'location_variance',
        'unique_ports_count': 'unusual_port_usage',
        'avg_port_number': 'unusual_port',
        'file_access_rate': 'unusual_file_access',
        'sensitive_file_access_rate': 'sensitive_file_access',
        'privilege_escalation_rate': 'privilege_escalation',
        'firewall_change_rate': 'firewall_change',
        'network_activity_volume': 'network_activity',
        'failed_login_rate': 'failed_login',
        'weekday_activity_ratio': 'unusual_schedule',
        'night_activity_ratio': 'night_activity'
    }
    
    return type_mapping.get(top_feature, 'behavioral_anomaly')


def generate_anomaly_description(anomaly_type: str, top_features: List[Dict], employee_name: str) -> str:
    """
    Generate human-readable description of the anomaly
    
    Args:
        anomaly_type: Type of anomaly
        top_features: Top contributing features
        employee_name: Name of the employee
        
    Returns:
        Description string
    """
    if not top_features:
        return f"Unusual behavioral pattern detected for {employee_name}"
    
    top_feature = top_features[0]
    feature_name = top_feature['feature_display']
    value = top_feature['value']
    
    descriptions = {
        'unusual_login_time': f"{employee_name} logged in at an unusual time ({value:.1f}:00)",
        'unusual_login_pattern': f"{employee_name} shows irregular login patterns (std: {value:.2f})",
        'unusual_location': f"{employee_name} accessed from {int(value)} different locations",
        'location_variance': f"{employee_name} accessed from unusual location ({value:.1%} deviation)",
        'unusual_port_usage': f"{employee_name} accessed {int(value)} unusual ports",
        'unusual_port': f"{employee_name} used unusual port {int(value)}",
        'unusual_file_access': f"{employee_name} accessed {value:.1f} files/day (unusual volume)",
        'sensitive_file_access': f"{employee_name} accessed {value:.2f} sensitive files/day",
        'privilege_escalation': f"{employee_name} performed {value:.2f} privilege escalations/day",
        'firewall_change': f"{employee_name} made {value:.2f} firewall changes/week",
        'network_activity': f"{employee_name} generated {value:.1f} network events/day",
        'failed_login': f"{employee_name} had {value:.2f} failed logins/day",
        'unusual_schedule': f"{employee_name} shows unusual work schedule ({value:.1%} weekday activity)",
        'night_activity': f"{employee_name} shows {value:.1%} night activity (unusual)"
    }
    
    return descriptions.get(anomaly_type, f"Unusual {feature_name} detected for {employee_name}")
