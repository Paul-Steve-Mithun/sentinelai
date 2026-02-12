import asyncio
import random
from datetime import datetime, timedelta, timezone
from database import init_db
from models import Employee, Anomaly, MitreMapping, MitigationStrategy

async def generate_data():
    print("Starting data generation...")
    await init_db()
    
    # 1. Ensure we have some employees
    employees = await Employee.find_all().to_list()
    if len(employees) < 5:
        print("Creating dummy employees...")
        departments = ["Engineering", "Sales", "HR", "Finance", "Marketing"]
        roles = ["Developer", "Manager", "Analyst", "Director", "Specialist"]
        
        for i in range(5):
            emp = Employee(
                employee_id=f"DUMMY_{i+100}",
                name=f"Dummy Employee {i+1}",
                email=f"dummy{i+1}@company.com",
                department=random.choice(departments),
                role=random.choice(roles),
                baseline_location="New York, US",
                is_isolated=False
            )
            await emp.create()
            employees.append(emp)
    
    print(f"Working with {len(employees)} employees")
    
    # 2. Generate Anomalies
    risk_levels = [
        {"level": "low", "score_range": (0, 39), "types": ["policy_violation", "minor_access"]},
        {"level": "medium", "score_range": (40, 59), "types": ["unusual_login", "suspicious_download"]},
        {"level": "high", "score_range": (60, 79), "types": ["privilege_escalation", "mass_deletion"]},
        {"level": "critical", "score_range": (80, 100), "types": ["data_exfiltration", "malware_activity"]}
    ]
    
    # Generate ~50 anomalies over 30 days
    anomalies_created = 0
    now = datetime.now(timezone.utc)
    
    for _ in range(50):
        emp = random.choice(employees)
        
        # Weighted random choice for risk level (fewer criticals, more low/medium)
        risk_config = random.choices(
            risk_levels, 
            weights=[40, 30, 20, 10], # 40% low, 30% medium, 20% high, 10% critical
            k=1
        )[0]
        
        score = random.randint(*risk_config["score_range"])
        anom_type = random.choice(risk_config["types"])
        
        # Random time in last 30 days
        days_ago = random.randint(0, 30)
        detected_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))
        
        # Status: Older ones resolved, newer ones open
        status = "resolved" if days_ago > 7 else "open"
        
        anomaly = Anomaly(
            employee_id=emp.id,
            anomaly_score=-1.0, # Dummy raw score
            risk_level=risk_config["level"],
            risk_score=score,
            description=f"Generated {risk_config['level']} risk anomaly: {anom_type}",
            anomaly_type=anom_type,
            status=status,
            detected_at=detected_at,
            top_features=[{"feature": "dummy_feature", "value": 0.0, "description": "Simulated value"}]
        )
        await anomaly.create()
        anomalies_created += 1
        
        # Add a MITRE mapping for realism
        await MitreMapping(
            anomaly_id=anomaly.id,
            technique_id="T1078",
            technique_name="Valid Accounts",
            tactic="Defense Evasion",
            description="Simulated usage of valid accounts",
            confidence=0.8
        ).create()
        
    print(f"✅ Successfully generated {anomalies_created} anomalies.")

if __name__ == "__main__":
    asyncio.run(generate_data())
