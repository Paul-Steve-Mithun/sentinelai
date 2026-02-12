"""
Feature engineering for behavioral fingerprinting
Extracts behavioral features from raw events to create employee baselines
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from sqlalchemy.orm import Session
import models


def calculate_behavioral_fingerprint(db: Session, employee_id: int, days_back: int = 30) -> Dict[str, float]:
    """
    Calculate behavioral fingerprint for an employee based on historical events
    
    Args:
        db: Database session
        employee_id: Employee ID
        days_back: Number of days to look back for baseline calculation
        
    Returns:
        Dictionary of behavioral features
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
    
    # Get employee and their events
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee:
        return None
    
    events = db.query(models.BehavioralEvent).filter(
        models.BehavioralEvent.employee_id == employee_id,
        models.BehavioralEvent.timestamp >= cutoff_date
    ).all()
    
    if not events:
        # Return default fingerprint for new employees
        return get_default_fingerprint()
    
    # Convert to DataFrame for easier analysis
    events_df = pd.DataFrame([{
        'event_type': e.event_type,
        'timestamp': e.timestamp,
        'location': e.location,
        'ip_address': e.ip_address,
        'port': e.port,
        'file_path': e.file_path,
        'action': e.action,
        'success': e.success
    } for e in events])
    
    # Extract features
    features = {}
    
    # 1. Login time patterns
    login_events = events_df[events_df['event_type'] == 'login']
    if len(login_events) > 0:
        login_hours = login_events['timestamp'].dt.hour
        features['avg_login_hour'] = float(login_hours.mean())
        features['login_hour_std'] = float(login_hours.std()) if len(login_hours) > 1 else 0.0
    else:
        features['avg_login_hour'] = 9.0  # Default 9 AM
        features['login_hour_std'] = 2.0
    
    # 2. Location patterns
    unique_locations = events_df['location'].dropna().nunique()
    features['unique_locations_count'] = unique_locations
    
    # Calculate average distance from baseline location
    if employee.baseline_location:
        # Simplified: count how often location differs from baseline
        location_events = events_df[events_df['location'].notna()]
        if len(location_events) > 0:
            different_locations = (location_events['location'] != employee.baseline_location).sum()
            features['avg_location_distance'] = float(different_locations / len(location_events))
        else:
            features['avg_location_distance'] = 0.0
    else:
        features['avg_location_distance'] = 0.0
    
    # 3. Port usage patterns
    port_events = events_df[events_df['port'].notna()]
    if len(port_events) > 0:
        features['unique_ports_count'] = int(port_events['port'].nunique())
        features['avg_port_number'] = float(port_events['port'].mean())
    else:
        features['unique_ports_count'] = 0
        features['avg_port_number'] = 0.0
    
    # 4. File access patterns
    file_events = events_df[events_df['event_type'] == 'file_access']
    features['file_access_rate'] = len(file_events) / max(days_back, 1)
    
    # Sensitive file access (files in /etc, /root, or containing 'secret', 'password', etc.)
    if len(file_events) > 0:
        sensitive_keywords = ['secret', 'password', 'credential', 'key', '/etc/', '/root/', 'config']
        sensitive_files = file_events[
            file_events['file_path'].str.contains('|'.join(sensitive_keywords), case=False, na=False)
        ]
        features['sensitive_file_access_rate'] = len(sensitive_files) / max(days_back, 1)
    else:
        features['sensitive_file_access_rate'] = 0.0
    
    # 5. Privilege escalation patterns
    priv_events = events_df[events_df['event_type'] == 'privilege_escalation']
    features['privilege_escalation_rate'] = len(priv_events) / max(days_back, 1)
    
    # 6. Firewall changes
    firewall_events = events_df[events_df['event_type'] == 'firewall']
    features['firewall_change_rate'] = len(firewall_events) / max(days_back / 7, 1)  # per week
    
    # 7. Network activity volume (simplified: count of network events)
    network_events = events_df[events_df['event_type'] == 'network']
    features['network_activity_volume'] = len(network_events) / max(days_back, 1)
    
    # 8. Failed login rate
    failed_logins = login_events[login_events['success'] == False] if len(login_events) > 0 else pd.DataFrame()
    features['failed_login_rate'] = len(failed_logins) / max(days_back, 1)
    
    # 9. Time-based patterns
    if len(events_df) > 0:
        events_df['day_of_week'] = events_df['timestamp'].dt.dayofweek
        events_df['hour'] = events_df['timestamp'].dt.hour
        
        # Weekday vs weekend activity
        weekday_events = events_df[events_df['day_of_week'] < 5]
        weekend_events = events_df[events_df['day_of_week'] >= 5]
        total_events = len(events_df)
        features['weekday_activity_ratio'] = len(weekday_events) / total_events if total_events > 0 else 0.7
        
        # Night vs day activity (night: 22:00 - 06:00)
        night_events = events_df[(events_df['hour'] >= 22) | (events_df['hour'] < 6)]
        features['night_activity_ratio'] = len(night_events) / total_events if total_events > 0 else 0.0
    else:
        features['weekday_activity_ratio'] = 0.7
        features['night_activity_ratio'] = 0.0
    
    return features


def get_default_fingerprint() -> Dict[str, float]:
    """Return default fingerprint for employees with no history"""
    return {
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


def extract_features_from_recent_events(db: Session, employee_id: int, hours_back: int = 24) -> Dict[str, float]:
    """
    Extract features from recent events for real-time anomaly detection
    Similar to fingerprint but for shorter time window
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    
    events = db.query(models.BehavioralEvent).filter(
        models.BehavioralEvent.employee_id == employee_id,
        models.BehavioralEvent.timestamp >= cutoff_time
    ).all()
    
    if not events:
        return get_default_fingerprint()
    
    # Use same logic as fingerprint calculation but with shorter window
    events_df = pd.DataFrame([{
        'event_type': e.event_type,
        'timestamp': e.timestamp,
        'location': e.location,
        'ip_address': e.ip_address,
        'port': e.port,
        'file_path': e.file_path,
        'action': e.action,
        'success': e.success
    } for e in events])
    
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    
    features = {}
    
    # Calculate same features but normalize by hours instead of days
    login_events = events_df[events_df['event_type'] == 'login']
    if len(login_events) > 0:
        login_hours = login_events['timestamp'].dt.hour
        features['avg_login_hour'] = float(login_hours.mean())
        features['login_hour_std'] = float(login_hours.std()) if len(login_hours) > 1 else 0.0
    else:
        features['avg_login_hour'] = 9.0
        features['login_hour_std'] = 2.0
    
    features['unique_locations_count'] = events_df['location'].dropna().nunique()
    
    if employee and employee.baseline_location:
        location_events = events_df[events_df['location'].notna()]
        if len(location_events) > 0:
            different_locations = (location_events['location'] != employee.baseline_location).sum()
            features['avg_location_distance'] = float(different_locations / len(location_events))
        else:
            features['avg_location_distance'] = 0.0
    else:
        features['avg_location_distance'] = 0.0
    
    port_events = events_df[events_df['port'].notna()]
    if len(port_events) > 0:
        features['unique_ports_count'] = int(port_events['port'].nunique())
        features['avg_port_number'] = float(port_events['port'].mean())
    else:
        features['unique_ports_count'] = 0
        features['avg_port_number'] = 0.0
    
    file_events = events_df[events_df['event_type'] == 'file_access']
    features['file_access_rate'] = len(file_events) / max(hours_back / 24, 1)
    
    if len(file_events) > 0:
        sensitive_keywords = ['secret', 'password', 'credential', 'key', '/etc/', '/root/', 'config']
        sensitive_files = file_events[
            file_events['file_path'].str.contains('|'.join(sensitive_keywords), case=False, na=False)
        ]
        features['sensitive_file_access_rate'] = len(sensitive_files) / max(hours_back / 24, 1)
    else:
        features['sensitive_file_access_rate'] = 0.0
    
    priv_events = events_df[events_df['event_type'] == 'privilege_escalation']
    features['privilege_escalation_rate'] = len(priv_events) / max(hours_back / 24, 1)
    
    firewall_events = events_df[events_df['event_type'] == 'firewall']
    features['firewall_change_rate'] = len(firewall_events) / max(hours_back / (24 * 7), 1)
    
    network_events = events_df[events_df['event_type'] == 'network']
    features['network_activity_volume'] = len(network_events) / max(hours_back / 24, 1)
    
    failed_logins = login_events[login_events['success'] == False] if len(login_events) > 0 else pd.DataFrame()
    features['failed_login_rate'] = len(failed_logins) / max(hours_back / 24, 1)
    
    if len(events_df) > 0:
        events_df['day_of_week'] = events_df['timestamp'].dt.dayofweek
        events_df['hour'] = events_df['timestamp'].dt.hour
        
        weekday_events = events_df[events_df['day_of_week'] < 5]
        total_events = len(events_df)
        features['weekday_activity_ratio'] = len(weekday_events) / total_events if total_events > 0 else 0.7
        
        night_events = events_df[(events_df['hour'] >= 22) | (events_df['hour'] < 6)]
        features['night_activity_ratio'] = len(night_events) / total_events if total_events > 0 else 0.0
    else:
        features['weekday_activity_ratio'] = 0.7
        features['night_activity_ratio'] = 0.0
    
    return features


def get_feature_names() -> List[str]:
    """Return list of feature names in consistent order"""
    return [
        'avg_login_hour',
        'login_hour_std',
        'unique_locations_count',
        'avg_location_distance',
        'unique_ports_count',
        'avg_port_number',
        'file_access_rate',
        'sensitive_file_access_rate',
        'privilege_escalation_rate',
        'firewall_change_rate',
        'network_activity_volume',
        'failed_login_rate',
        'weekday_activity_ratio',
        'night_activity_ratio'
    ]


def features_to_array(features: Dict[str, float]) -> np.ndarray:
    """Convert feature dictionary to numpy array in consistent order"""
    feature_names = get_feature_names()
    return np.array([features.get(name, 0.0) for name in feature_names]).reshape(1, -1)
