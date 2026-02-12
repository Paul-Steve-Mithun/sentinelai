"""
Demo data generator for insider threat detection system
Generates realistic behavioral data with normal and anomalous patterns
"""
import random
import sys
import os
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
import models

# Create tables
Base.metadata.create_all(bind=engine)


def generate_employees(db, count=20):
    """Generate sample employees"""
    departments = ['Engineering', 'Sales', 'HR', 'Finance', 'Operations', 'IT Security']
    roles = ['Developer', 'Manager', 'Analyst', 'Administrator', 'Director']
    locations = ['New York', 'San Francisco', 'London', 'Tokyo', 'Mumbai']
    
    employees = []
    for i in range(count):
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
    print(f"✓ Created {count} employees")
    return employees


def generate_normal_events(db, employee, days=30):
    """Generate normal behavioral events for an employee"""
    events = []
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Normal login pattern: 8-10 AM on weekdays
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        
        # Skip weekends for most employees
        if current_date.weekday() >= 5 and random.random() > 0.1:
            continue
        
        # Morning login
        login_hour = random.randint(8, 10)
        login_time = current_date.replace(hour=login_hour, minute=random.randint(0, 59))
        
        events.append(models.BehavioralEvent(
            employee_id=employee.id,
            event_type='login',
            timestamp=login_time,
            location=employee.baseline_location,
            ip_address=f"192.168.1.{random.randint(10, 250)}",
            success=True
        ))
        
        # Normal file access (5-15 files per day)
        for _ in range(random.randint(5, 15)):
            file_time = login_time + timedelta(hours=random.randint(0, 8))
            events.append(models.BehavioralEvent(
                employee_id=employee.id,
                event_type='file_access',
                timestamp=file_time,
                file_path=f"/home/user/documents/file{random.randint(1, 100)}.txt",
                action=random.choice(['read', 'write']),
                success=True
            ))
        
        # Normal network activity (standard ports)
        for _ in range(random.randint(10, 20)):
            net_time = login_time + timedelta(hours=random.randint(0, 8))
            events.append(models.BehavioralEvent(
                employee_id=employee.id,
                event_type='network',
                timestamp=net_time,
                port=random.choice([80, 443, 22, 3306]),
                success=True
            ))
        
        # Occasional privilege escalation (normal for some roles)
        if random.random() < 0.3:
            sudo_time = login_time + timedelta(hours=random.randint(1, 6))
            events.append(models.BehavioralEvent(
                employee_id=employee.id,
                event_type='privilege_escalation',
                timestamp=sudo_time,
                action='sudo',
                success=True
            ))
    
    for event in events:
        db.add(event)
    
    return len(events)


def generate_anomalous_events(db, employee, anomaly_type='unusual_login'):
    """Generate anomalous events for testing"""
    events = []
    base_time = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 7))
    
    if anomaly_type == 'unusual_login':
        # Login at 3 AM
        night_login = base_time.replace(hour=3, minute=random.randint(0, 59))
        events.append(models.BehavioralEvent(
            employee_id=employee.id,
            event_type='login',
            timestamp=night_login,
            location=employee.baseline_location,
            ip_address=f"192.168.1.{random.randint(10, 250)}",
            success=True
        ))
    
    elif anomaly_type == 'unusual_location':
        # Login from different location
        unusual_locations = ['Beijing', 'Moscow', 'Unknown Location']
        events.append(models.BehavioralEvent(
            employee_id=employee.id,
            event_type='login',
            timestamp=base_time,
            location=random.choice(unusual_locations),
            ip_address=f"10.0.0.{random.randint(1, 255)}",
            success=True
        ))
    
    elif anomaly_type == 'unusual_port':
        # Access unusual ports
        unusual_ports = [4444, 8888, 9999, 31337, 6667]
        for port in random.sample(unusual_ports, 3):
            events.append(models.BehavioralEvent(
                employee_id=employee.id,
                event_type='network',
                timestamp=base_time + timedelta(minutes=random.randint(0, 60)),
                port=port,
                success=True
            ))
    
    elif anomaly_type == 'sensitive_files':
        # Access sensitive files
        sensitive_paths = [
            '/etc/shadow',
            '/root/.ssh/id_rsa',
            '/var/log/auth.log',
            '/home/admin/passwords.txt',
            '/etc/secrets/api_keys.conf'
        ]
        for path in random.sample(sensitive_paths, 3):
            events.append(models.BehavioralEvent(
                employee_id=employee.id,
                event_type='file_access',
                timestamp=base_time + timedelta(minutes=random.randint(0, 60)),
                file_path=path,
                action='read',
                success=True
            ))
    
    elif anomaly_type == 'privilege_escalation':
        # Excessive privilege escalation
        for _ in range(15):
            events.append(models.BehavioralEvent(
                employee_id=employee.id,
                event_type='privilege_escalation',
                timestamp=base_time + timedelta(minutes=random.randint(0, 120)),
                action='sudo',
                success=True
            ))
    
    elif anomaly_type == 'firewall_change':
        # Firewall modifications
        for _ in range(5):
            events.append(models.BehavioralEvent(
                employee_id=employee.id,
                event_type='firewall',
                timestamp=base_time + timedelta(minutes=random.randint(0, 60)),
                action='modify_rule',
                success=True
            ))
    
    elif anomaly_type == 'failed_logins':
        # Multiple failed login attempts
        for _ in range(10):
            events.append(models.BehavioralEvent(
                employee_id=employee.id,
                event_type='login',
                timestamp=base_time + timedelta(minutes=random.randint(0, 30)),
                location=employee.baseline_location,
                ip_address=f"192.168.1.{random.randint(10, 250)}",
                success=False
            ))
    
    for event in events:
        db.add(event)
    
    return len(events)


def main():
    """Main data generation function"""
    db = SessionLocal()
    
    try:
        print("🚀 Starting data generation...")
        
        # Clear existing data
        print("Clearing existing data...")
        db.query(models.MitigationStrategy).delete()
        db.query(models.MitreMapping).delete()
        db.query(models.Anomaly).delete()
        db.query(models.BehavioralFingerprint).delete()
        db.query(models.BehavioralEvent).delete()
        db.query(models.Employee).delete()
        db.commit()
        
        # Generate employees
        employees = generate_employees(db, count=20)
        
        # Generate normal events for all employees
        print("Generating normal behavioral events...")
        total_events = 0
        for employee in employees:
            count = generate_normal_events(db, employee, days=30)
            total_events += count
        
        db.commit()
        print(f"✓ Created {total_events} normal events")
        
        # Generate anomalous events for some employees
        print("Generating anomalous events...")
        anomaly_types = [
            'unusual_login',
            'unusual_location',
            'unusual_port',
            'sensitive_files',
            'privilege_escalation',
            'firewall_change',
            'failed_logins'
        ]
        
        anomalous_employees = random.sample(employees, 7)
        anomaly_count = 0
        for employee, anomaly_type in zip(anomalous_employees, anomaly_types):
            count = generate_anomalous_events(db, employee, anomaly_type)
            anomaly_count += count
        
        db.commit()
        print(f"✓ Created {anomaly_count} anomalous events for {len(anomalous_employees)} employees")
        
        print("\n✅ Data generation complete!")
        print(f"   - Employees: {len(employees)}")
        print(f"   - Normal events: {total_events}")
        print(f"   - Anomalous events: {anomaly_count}")
        print(f"\n💡 Next steps:")
        print(f"   1. Train the ML model: POST http://localhost:8000/api/ml/train")
        print(f"   2. View dashboard: http://localhost:5173")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
