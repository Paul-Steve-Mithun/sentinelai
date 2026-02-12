"""
Database models for insider threat detection system
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True)
    department = Column(String)
    role = Column(String)
    baseline_location = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    events = relationship("BehavioralEvent", back_populates="employee")
    fingerprints = relationship("BehavioralFingerprint", back_populates="employee")
    anomalies = relationship("Anomaly", back_populates="employee")


class BehavioralEvent(Base):
    __tablename__ = "behavioral_events"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    event_type = Column(String, index=True)  # login, file_access, network, firewall, privilege_escalation
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Event details
    location = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    port = Column(Integer, nullable=True)
    file_path = Column(String, nullable=True)
    action = Column(String, nullable=True)  # read, write, delete, execute
    success = Column(Boolean, default=True)
    
    # Additional metadata
    event_metadata = Column(JSON, nullable=True)
    
    # Relationships
    employee = relationship("Employee", back_populates="events")


class BehavioralFingerprint(Base):
    __tablename__ = "behavioral_fingerprints"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    computed_at = Column(DateTime, default=datetime.utcnow)
    
    # Behavioral features (baseline)
    avg_login_hour = Column(Float)
    login_hour_std = Column(Float)
    unique_locations_count = Column(Integer)
    avg_location_distance = Column(Float)
    unique_ports_count = Column(Integer)
    avg_port_number = Column(Float)
    file_access_rate = Column(Float)  # files per day
    sensitive_file_access_rate = Column(Float)
    privilege_escalation_rate = Column(Float)  # sudo attempts per day
    firewall_change_rate = Column(Float)  # changes per week
    network_activity_volume = Column(Float)  # MB per day
    failed_login_rate = Column(Float)
    
    # Time-based patterns
    weekday_activity_ratio = Column(Float)  # weekday vs weekend
    night_activity_ratio = Column(Float)  # night (10pm-6am) vs day
    
    # Relationships
    employee = relationship("Employee", back_populates="fingerprints")


class Anomaly(Base):
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Anomaly details
    anomaly_score = Column(Float)  # -1 to 1 (Isolation Forest score)
    risk_level = Column(String)  # low, medium, high, critical
    risk_score = Column(Integer)  # 0-100
    
    # Event that triggered anomaly
    trigger_event_id = Column(Integer, ForeignKey("behavioral_events.id"), nullable=True)
    
    # Anomaly description
    description = Column(Text)
    anomaly_type = Column(String)  # unusual_login, unusual_location, unusual_port, etc.
    
    # SHAP explanation
    shap_values = Column(JSON)  # Feature contributions
    top_features = Column(JSON)  # Top contributing features
    
    # Status
    status = Column(String, default="open")  # open, investigating, resolved, false_positive
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    employee = relationship("Employee", back_populates="anomalies")
    mitre_mappings = relationship("MitreMapping", back_populates="anomaly")
    mitigation_strategies = relationship("MitigationStrategy", back_populates="anomaly")


class MitreMapping(Base):
    __tablename__ = "mitre_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    anomaly_id = Column(Integer, ForeignKey("anomalies.id"))
    
    # MITRE ATT&CK details
    technique_id = Column(String)  # e.g., T1078
    technique_name = Column(String)
    tactic = Column(String)  # e.g., Initial Access, Privilege Escalation
    description = Column(Text)
    confidence = Column(Float)  # 0-1
    
    # Relationships
    anomaly = relationship("Anomaly", back_populates="mitre_mappings")


class MitigationStrategy(Base):
    __tablename__ = "mitigation_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    anomaly_id = Column(Integer, ForeignKey("anomalies.id"))
    
    # Strategy details
    priority = Column(Integer)  # 1 (highest) to 5 (lowest)
    category = Column(String)  # immediate, short_term, long_term
    action = Column(Text)
    description = Column(Text)
    
    # Status
    implemented = Column(Boolean, default=False)
    implemented_at = Column(DateTime, nullable=True)
    implemented_by = Column(String, nullable=True)
    
    # Relationships
    anomaly = relationship("Anomaly", back_populates="mitigation_strategies")
