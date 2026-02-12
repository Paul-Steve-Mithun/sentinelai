import asyncio
import aiohttp
from database import init_db
from models import Anomaly, Employee, MitreMapping
from datetime import datetime, timezone

async def verify():
    # 1. Setup Data
    await init_db()
    
    # Create dummy employee if needed
    emp_id = "VERIFY_TEST_EMP"
    emp = await Employee.find_one(Employee.employee_id == emp_id)
    if not emp:
        emp = Employee(
            employee_id=emp_id,
            name="Verify Test",
            email="verify@test.com",
            department="Test",
            role="Test"
        )
        await emp.create()
        
    # Create dummy anomaly
    anomaly = Anomaly(
        employee_id=emp.id,
        anomaly_score=0.9,
        risk_level="critical",
        risk_score=90,
        description="Test Anomaly",
        anomaly_type="test_type",
        status="open",
        detected_at=datetime.now(timezone.utc)
    )
    await anomaly.create()
    print(f"Created test anomaly: {anomaly.id}")
    
    # Create dummy mitigation strategy
    from models import MitigationStrategy
    strategy = MitigationStrategy(
        anomaly_id=anomaly.id,
        priority=1,
        category="Test Category",
        action="Test Action",
        description="Test Description"
    )
    await strategy.create()
    print("Created test mitigation strategy")
    
    # 2. Test API
    url = f"http://localhost:8000/api/anomalies/{anomaly.id}/mitigation"
    print(f"Testing URL: {url}")
    
    try:
        import requests
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Verification SUCCESS: Mitigation endpoint returned 200 OK")
        else:
            print(f"❌ Verification FAILED: {response.status_code}")
                    
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        print("Note: Ensure the backend server is running on localhost:8000")

    # Cleanup
    await anomaly.delete()
    # await mapping.delete() # removing mapping
    await strategy.delete()
    # keeping employee is fine

if __name__ == "__main__":
    asyncio.run(verify())
