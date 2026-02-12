"""
Database initialization endpoint - No shell access needed!
Just visit /api/init in your browser to populate the database
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models
import random
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/init", tags=["initialization"])

@router.get("/")
def initialize_database(db: Session = Depends(get_db)):
    """
    Initialize database with demo data
    Access via browser: https://your-url.onrender.com/api/init
    """
    try:
        # Check if already initialized
        existing_count = db.query(models.Employee).count()
        if existing_count > 0:
            return {
                "status": "already_initialized",
                "message": f"Database already has {existing_count} employees. Clear data first if you want to reinitialize.",
                "employees": existing_count
            }
        
        # Generate 20 employees
        departments = ['Engineering', 'Sales', 'HR', 'Finance', 'Operations']
        roles = ['Developer', 'Manager', 'Analyst', 'Administrator']
        locations = ['New York', 'San Francisco', 'London', 'Tokyo', 'Mumbai']
        
        employees = []
        for i in range(20):
            employee = models.Employee(
                employee_id=f"EMP{1000 + i}",
                name=f"Employee {i+1}",
                email=f"employee{i+1}@company.com",
                department=random.choice(departments),
                role=random.choice(roles),
                baseline_location=random.choice(locations)
            )
            db.add(employee)
            employees.append(employee)
        
        db.commit()
        
        # Generate events for each employee
        total_events = 0
        for employee in employees:
            # Refresh to get ID
            db.refresh(employee)
            
            # Generate 30 days of normal events
            start_date = datetime.utcnow() - timedelta(days=30)
            for day in range(30):
                current_date = start_date + timedelta(days=day)
                
                # Skip weekends
                if current_date.weekday() >= 5:
                    continue
                
                # Morning login
                login_time = current_date.replace(hour=random.randint(8, 10), minute=random.randint(0, 59))
                db.add(models.BehavioralEvent(
                    employee_id=employee.id,
                    event_type='login',
                    timestamp=login_time,
                    location=employee.baseline_location,
                    ip_address=f"192.168.1.{random.randint(10, 250)}",
                    success=True
                ))
                total_events += 1
                
                # File access events
                for _ in range(random.randint(5, 10)):
                    db.add(models.BehavioralEvent(
                        employee_id=employee.id,
                        event_type='file_access',
                        timestamp=login_time + timedelta(hours=random.randint(0, 8)),
                        file_path=f"/home/user/documents/file{random.randint(1, 100)}.txt",
                        action=random.choice(['read', 'write']),
                        success=True
                    ))
                    total_events += 1
                
                # Network events
                for _ in range(random.randint(5, 10)):
                    db.add(models.BehavioralEvent(
                        employee_id=employee.id,
                        event_type='network',
                        timestamp=login_time + timedelta(hours=random.randint(0, 8)),
                        port=random.choice([80, 443, 22, 3306]),
                        success=True
                    ))
                    total_events += 1
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Database initialized successfully!",
            "employees_created": len(employees),
            "events_created": total_events,
            "next_steps": [
                "Train the model: POST /api/ml/train",
                "View dashboard: Open your frontend",
                "Check employees: GET /api/employees"
            ]
        }
        
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Initialization failed: {str(e)}"
        }

