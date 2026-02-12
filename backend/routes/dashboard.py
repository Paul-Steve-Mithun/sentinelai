"""
Dashboard statistics and analytics routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List
import models
import schemas
from database import get_db

router = APIRouter()


@router.get("/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get overall dashboard statistics"""
    # Total employees
    total_employees = db.query(func.count(models.Employee.id)).scalar()
    
    # Active threats (open anomalies)
    active_threats = db.query(func.count(models.Anomaly.id)).filter(
        models.Anomaly.status == 'open'
    ).scalar()
    
    # Total anomalies
    total_anomalies = db.query(func.count(models.Anomaly.id)).scalar()
    
    # Average risk score
    avg_risk = db.query(func.avg(models.Anomaly.risk_score)).filter(
        models.Anomaly.status == 'open'
    ).scalar() or 0
    
    # Count by risk level
    critical_threats = db.query(func.count(models.Anomaly.id)).filter(
        models.Anomaly.risk_level == 'critical',
        models.Anomaly.status == 'open'
    ).scalar()
    
    high_threats = db.query(func.count(models.Anomaly.id)).filter(
        models.Anomaly.risk_level == 'high',
        models.Anomaly.status == 'open'
    ).scalar()
    
    medium_threats = db.query(func.count(models.Anomaly.id)).filter(
        models.Anomaly.risk_level == 'medium',
        models.Anomaly.status == 'open'
    ).scalar()
    
    low_threats = db.query(func.count(models.Anomaly.id)).filter(
        models.Anomaly.risk_level == 'low',
        models.Anomaly.status == 'open'
    ).scalar()
    
    return {
        'total_employees': total_employees,
        'active_threats': active_threats,
        'total_anomalies': total_anomalies,
        'avg_risk_score': float(avg_risk),
        'critical_threats': critical_threats,
        'high_threats': high_threats,
        'medium_threats': medium_threats,
        'low_threats': low_threats
    }


@router.get("/risk-distribution", response_model=schemas.RiskDistribution)
def get_risk_distribution(db: Session = Depends(get_db)):
    """Get distribution of anomalies by risk level"""
    low = db.query(func.count(models.Anomaly.id)).filter(
        models.Anomaly.risk_level == 'low'
    ).scalar()
    
    medium = db.query(func.count(models.Anomaly.id)).filter(
        models.Anomaly.risk_level == 'medium'
    ).scalar()
    
    high = db.query(func.count(models.Anomaly.id)).filter(
        models.Anomaly.risk_level == 'high'
    ).scalar()
    
    critical = db.query(func.count(models.Anomaly.id)).filter(
        models.Anomaly.risk_level == 'critical'
    ).scalar()
    
    return {
        'low': low,
        'medium': medium,
        'high': high,
        'critical': critical
    }


@router.get("/top-threats", response_model=List[schemas.TopThreat])
def get_top_threats(limit: int = 10, db: Session = Depends(get_db)):
    """Get top employees by risk score"""
    # Subquery to get latest anomaly per employee
    subquery = db.query(
        models.Anomaly.employee_id,
        func.max(models.Anomaly.risk_score).label('max_risk'),
        func.count(models.Anomaly.id).label('anomaly_count'),
        func.max(models.Anomaly.detected_at).label('latest_anomaly')
    ).filter(
        models.Anomaly.status == 'open'
    ).group_by(
        models.Anomaly.employee_id
    ).subquery()
    
    # Join with employees
    results = db.query(
        models.Employee,
        subquery.c.max_risk,
        subquery.c.anomaly_count,
        subquery.c.latest_anomaly
    ).join(
        subquery,
        models.Employee.id == subquery.c.employee_id
    ).order_by(
        desc(subquery.c.max_risk)
    ).limit(limit).all()
    
    top_threats = []
    for employee, max_risk, anomaly_count, latest_anomaly in results:
        top_threats.append({
            'employee_id': employee.id,
            'employee_name': employee.name,
            'risk_score': int(max_risk),
            'anomaly_count': anomaly_count,
            'latest_anomaly': latest_anomaly
        })
    
    return top_threats


@router.get("/timeline", response_model=List[schemas.TimelinePoint])
def get_anomaly_timeline(days: int = 30, db: Session = Depends(get_db)):
    """Get anomaly timeline for the past N days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all anomalies in the time range
    anomalies = db.query(models.Anomaly).filter(
        models.Anomaly.detected_at >= cutoff_date
    ).all()
    
    # Group by date
    timeline_data = {}
    for anomaly in anomalies:
        date_str = anomaly.detected_at.strftime('%Y-%m-%d')
        
        if date_str not in timeline_data:
            timeline_data[date_str] = {
                'date': date_str,
                'count': 0,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            }
        
        timeline_data[date_str]['count'] += 1
        timeline_data[date_str][anomaly.risk_level] += 1
    
    # Convert to list and sort by date
    timeline = list(timeline_data.values())
    timeline.sort(key=lambda x: x['date'])
    
    return timeline
