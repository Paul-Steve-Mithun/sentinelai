"""
Dashboard statistics and analytics routes
"""
from fastapi import APIRouter
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import models
import schemas
from beanie import PydanticObjectId
from beanie.operators import In

router = APIRouter()


@router.get("/stats", response_model=schemas.DashboardStats)
async def get_dashboard_stats():
    """Get overall dashboard statistics"""
    # Total employees
    total_employees = await models.Employee.find_all().count()
    
    # Active threats (open anomalies)
    active_threats = await models.Anomaly.find(
        models.Anomaly.status == 'open'
    ).count()
    
    # Total anomalies
    total_anomalies = await models.Anomaly.find_all().count()
    
    # Average risk score
    # Beanie avg() returns float or None
    avg_risk = await models.Anomaly.find(
        models.Anomaly.status == 'open'
    ).avg(models.Anomaly.risk_score) or 0
    
    # Count by risk level
    critical_threats = await models.Anomaly.find(
        models.Anomaly.risk_level == 'critical',
        models.Anomaly.status == 'open'
    ).count()
    
    high_threats = await models.Anomaly.find(
        models.Anomaly.risk_level == 'high',
        models.Anomaly.status == 'open'
    ).count()
    
    medium_threats = await models.Anomaly.find(
        models.Anomaly.risk_level == 'medium',
        models.Anomaly.status == 'open'
    ).count()
    
    low_threats = await models.Anomaly.find(
        models.Anomaly.risk_level == 'low',
        models.Anomaly.status == 'open'
    ).count()
    
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
async def get_risk_distribution():
    """Get distribution of anomalies by risk level"""
    low = await models.Anomaly.find(
        models.Anomaly.risk_level == 'low'
    ).count()
    
    medium = await models.Anomaly.find(
        models.Anomaly.risk_level == 'medium'
    ).count()
    
    high = await models.Anomaly.find(
        models.Anomaly.risk_level == 'high'
    ).count()
    
    critical = await models.Anomaly.find(
        models.Anomaly.risk_level == 'critical'
    ).count()
    
    return {
        'low': low,
        'medium': medium,
        'high': high,
        'critical': critical
    }


@router.get("/top-threats", response_model=List[schemas.TopThreat])
async def get_top_threats(limit: int = 10):
    """Get top employees by risk score"""
    # Aggregation to get latest anomaly per employee
    pipeline = [
        {'$match': {'status': 'open'}},
        {'$group': {
            '_id': '$employee_id',
            'max_risk': {'$max': '$risk_score'},
            'anomaly_count': {'$sum': 1},
            'latest_anomaly': {'$max': '$detected_at'}
        }},
        {'$sort': {'max_risk': -1}},
        {'$limit': limit}
    ]
    
    results = await models.Anomaly.aggregate(pipeline).to_list()
    
    top_threats = []
    
    if not results:
        return top_threats
        
    # Fetch employees
    emp_ids = [res['_id'] for res in results if res['_id']]
    # Ensure IDs are in correct format for query (PydanticObjectId)
    # Beanie stores them as ObjectId usually if defined as such
    
    employees = await models.Employee.find(In(models.Employee.id, emp_ids)).to_list()
    emp_map = {e.id: e for e in employees}
    
    for res in results:
        emp_id = res['_id']
        employee = emp_map.get(emp_id)
        
        if employee:
            top_threats.append({
                'employee_id': str(employee.id),
                'employee_name': employee.name,
                'risk_score': int(res['max_risk']),
                'anomaly_count': int(res['anomaly_count']),
                'latest_anomaly': res['latest_anomaly']
            })
    
    return top_threats


@router.get("/timeline", response_model=List[schemas.TimelinePoint])
async def get_anomaly_timeline(days: int = 30):
    """Get anomaly timeline for the past N days"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get all anomalies in the time range
    anomalies = await models.Anomaly.find(
        models.Anomaly.detected_at >= cutoff_date
    ).to_list()
    
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
