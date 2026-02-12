"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


from beanie import PydanticObjectId

# Employee Schemas
class EmployeeBase(BaseModel):
    employee_id: str
    name: str
    email: str
    department: str
    role: str
    baseline_location: Optional[str] = None
    is_isolated: bool = False


class EmployeeCreate(EmployeeBase):
    pass


class Employee(EmployeeBase):
    id: Optional[PydanticObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


# Behavioral Event Schemas
class BehavioralEventBase(BaseModel):
    event_type: str
    timestamp: Optional[datetime] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    file_path: Optional[str] = None
    action: Optional[str] = None
    success: Optional[bool] = True
    metadata: Optional[Dict[str, Any]] = None
    cpu_usage: Optional[float] = 0.0
    memory_usage: Optional[float] = 0.0


class BehavioralEventCreate(BehavioralEventBase):
    employee_id: str


class BehavioralEvent(BehavioralEventBase):
    id: Optional[PydanticObjectId] = Field(alias="_id", default=None)
    employee_id: str
    
    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


# Behavioral Fingerprint Schemas
class BehavioralFingerprintBase(BaseModel):
    avg_login_hour: float
    login_hour_std: float
    unique_locations_count: int
    avg_location_distance: float
    unique_ports_count: int
    avg_port_number: float
    file_access_rate: float
    sensitive_file_access_rate: float
    privilege_escalation_rate: float
    firewall_change_rate: float
    network_activity_volume: float
    failed_login_rate: float
    weekday_activity_ratio: float
    night_activity_ratio: float


class BehavioralFingerprint(BehavioralFingerprintBase):
    id: Optional[PydanticObjectId] = Field(alias="_id", default=None)
    employee_id: Union[str, PydanticObjectId]
    computed_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


# Anomaly Schemas
class AnomalyBase(BaseModel):
    anomaly_score: float
    risk_level: str
    risk_score: int
    description: str
    anomaly_type: str


class Anomaly(AnomalyBase):
    id: Optional[PydanticObjectId] = Field(alias="_id", default=None)
    employee_id: Union[str, PydanticObjectId]
    detected_at: datetime
    shap_values: Optional[Dict[str, float]] = None
    top_features: Optional[List[Dict[str, Any]]] = None
    status: str
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    @field_validator('employee_id')
    @classmethod
    def serialize_employee_id(cls, v):
        return str(v)
    
    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class AnomalyWithEmployee(Anomaly):
    employee: Employee


class AnomalyResolve(BaseModel):
    resolved_by: str
    resolution_notes: str
    status: str  # resolved, false_positive


# MITRE Mapping Schemas
class MitreMappingBase(BaseModel):
    technique_id: str
    technique_name: str
    tactic: str
    description: str
    confidence: float


class MitreMapping(MitreMappingBase):
    id: Optional[PydanticObjectId] = Field(alias="_id", default=None)
    anomaly_id: Union[str, PydanticObjectId]
    
    @field_validator('anomaly_id')
    @classmethod
    def serialize_anomaly_id(cls, v):
        return str(v)
    
    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


# Mitigation Strategy Schemas
class MitigationStrategyBase(BaseModel):
    priority: int
    category: str
    action: str
    description: str


class MitigationStrategy(MitigationStrategyBase):
    id: Optional[PydanticObjectId] = Field(alias="_id", default=None)
    anomaly_id: Union[str, PydanticObjectId]
    implemented: bool
    implemented_at: Optional[datetime] = None
    implemented_by: Optional[str] = None
    
    @field_validator('anomaly_id')
    @classmethod
    def serialize_anomaly_id(cls, v):
        return str(v)
    
    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PydanticObjectId: str}


class MitigationImplement(BaseModel):
    implemented_by: str


# Dashboard Schemas
class DashboardStats(BaseModel):
    total_employees: int
    active_threats: int
    total_anomalies: int
    avg_risk_score: float
    critical_threats: int
    high_threats: int
    medium_threats: int
    low_threats: int


class RiskDistribution(BaseModel):
    low: int
    medium: int
    high: int
    critical: int


class TopThreat(BaseModel):
    employee_id: str
    employee_name: str
    risk_score: int
    anomaly_count: int
    latest_anomaly: datetime


class TimelinePoint(BaseModel):
    date: str
    count: int
    critical: int
    high: int
    medium: int
    low: int


# ML Schemas
class ModelInfo(BaseModel):
    model_type: str
    trained_at: Optional[datetime] = None
    n_samples: int
    n_features: int
    accuracy: Optional[float] = None


class PredictionRequest(BaseModel):
    employee_id: str
    features: Dict[str, float]


class PredictionResponse(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    risk_level: str
    risk_score: int
    shap_values: Dict[str, float]
    top_features: List[Dict[str, Any]]
