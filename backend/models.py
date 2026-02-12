"""
Database models for insider threat detection system (MongoDB/Beanie)
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from beanie import Document, Link, PydanticObjectId
from pydantic import Field, EmailStr

class Employee(Document):
    """Employee document"""
    employee_id: str = Field(..., description="Unique employee ID string")
    name: str
    email: str = Field(..., description="Unique email")
    department: str
    role: str
    baseline_location: Optional[str] = None
    is_isolated: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "employees"
        indexes = [
            "employee_id",
            "email",
            "name"
        ]

class BehavioralEvent(Document):
    """Behavioral event document"""
    employee_id: PydanticObjectId = Field(..., description="Reference to Employee ID")
    event_type: str  # login, file_access, network, firewall, privilege_escalation
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Event details
    location: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    file_path: Optional[str] = None
    action: Optional[str] = None # read, write, delete, execute
    success: bool = True
    
    # Additional metadata
    event_metadata: Optional[Dict[str, Any]] = None
    
    # System Metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    
    class Settings:
        name = "behavioral_events"
        indexes = [
            "employee_id",
            "event_type",
            "timestamp"
        ]

class BehavioralFingerprint(Document):
    """Behavioral fingerprint document (baseline)"""
    employee_id: PydanticObjectId = Field(..., description="Reference to Employee ID")
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Behavioral features (baseline)
    avg_login_hour: float
    login_hour_std: float
    unique_locations_count: int
    avg_location_distance: float
    unique_ports_count: int
    avg_port_number: float
    file_access_rate: float  # files per day
    sensitive_file_access_rate: float
    privilege_escalation_rate: float  # sudo attempts per day
    firewall_change_rate: float  # changes per week
    network_activity_volume: float  # MB per day
    failed_login_rate: float
    
    # Time-based patterns
    weekday_activity_ratio: float  # weekday vs weekend
    night_activity_ratio: float  # night (10pm-6am) vs day
    
    class Settings:
        name = "behavioral_fingerprints"
        indexes = [
            "employee_id",
            "computed_at"
        ]

class Anomaly(Document):
    """Anomaly document"""
    employee_id: PydanticObjectId = Field(..., description="Reference to Employee ID")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Anomaly details
    anomaly_score: float  # -1 to 1 (Isolation Forest score)
    risk_level: str  # low, medium, high, critical
    risk_score: int  # 0-100
    
    # Event that triggered anomaly
    trigger_event_id: Optional[PydanticObjectId] = None
    
    # Anomaly description
    description: str
    anomaly_type: str  # unusual_login, unusual_location, unusual_port, etc.
    
    # SHAP explanation
    shap_values: Optional[Dict[str, float]] = None # Feature contributions
    top_features: Optional[List[Dict[str, Any]]] = None # Top contributing features
    
    # Status
    status: str = "open"  # open, investigating, resolved, false_positive
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    class Settings:
        name = "anomalies"
        indexes = [
            "employee_id",
            "detected_at",
            "risk_level",
            "status"
        ]

class MitreMapping(Document):
    """MITRE ATT&CK mapping document"""
    anomaly_id: PydanticObjectId = Field(..., description="Reference to Anomaly ID")
    
    # MITRE ATT&CK details
    technique_id: str  # e.g., T1078
    technique_name: str
    tactic: str  # e.g., Initial Access, Privilege Escalation
    description: str
    confidence: float  # 0-1
    
    class Settings:
        name = "mitre_mappings"
        indexes = [
            "anomaly_id",
            "technique_id"
        ]

class MitigationStrategy(Document):
    """Mitigation strategy document"""
    anomaly_id: PydanticObjectId = Field(..., description="Reference to Anomaly ID")
    
    # Strategy details
    priority: int  # 1 (highest) to 5 (lowest)
    category: str  # immediate, short_term, long_term
    action: str
    description: str
    
    # Status
    implemented: bool = False
    implemented_at: Optional[datetime] = None
    implemented_by: Optional[str] = None
    
    class Settings:
        name = "mitigation_strategies"
        indexes = [
            "anomaly_id",
            "priority"
        ]
