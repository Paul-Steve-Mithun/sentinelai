import asyncio
import aiohttp
from database import init_db
from models import Employee, Anomaly
from datetime import datetime, timezone
import requests

async def verify():
    print("Starting Verification...")
    # 1. Setup Data
    await init_db()
    
    # Create or get employee
    emp_id = "ISOLATION_TEST_EMP"
    emp = await Employee.find_one(Employee.employee_id == emp_id)
    if not emp:
        emp = Employee(
            employee_id=emp_id,
            name="Isolation Test",
            email="isolation@test.com",
            department="Test",
            role="Test",
            is_isolated=False
        )
        await emp.create()
        print(f"Created test employee: {emp.id}")
    else:
        # Reset isolation
        emp.is_isolated = False
        await emp.save()
        print(f"Using existing test employee: {emp.id}")

    # Create dummy critical anomaly
    anomaly = Anomaly(
        employee_id=emp.id,
        anomaly_score=-0.4, # High anomaly score
        risk_level="critical",
        risk_score=90,
        description="Test Anomaly for Isolation",
        anomaly_type="test_type",
        status="open",
        detected_at=datetime.now(timezone.utc)
    )
    await anomaly.create()
    print("Created test critical anomaly")
    
    base_url = "http://localhost:8000/api/agent"
    
    try:
        # 2. Verify Auto-Isolation is DISABLED
        # Previous logic would return isolated=True because of critical anomaly
        status_url = f"{base_url}/{emp.id}/status"
        print(f"Checking Status: {status_url}")
        resp = requests.get(status_url)
        data = resp.json()
        print(f"Status Response: {data}")
        
        if data.get("isolated") == False:
            print("✅ PASS: Agent is NOT auto-isolated despite critical anomaly")
        else:
            print("❌ FAIL: Agent IS auto-isolated")
            
        # 3. Verify Manual Isolation
        isolate_url = f"{base_url}/{emp.id}/isolate"
        print(f"Sending Isolate Command: {isolate_url}")
        requests.post(isolate_url)
        
        # Check status again
        resp = requests.get(status_url)
        data = resp.json()
        if data.get("isolated") == True:
             print("✅ PASS: Agent is MANUALLY isolated")
        else:
             print("❌ FAIL: Manual isolation failed")
             
        # 4. Verify Restore
        restore_url = f"{base_url}/{emp.id}/restore"
        print(f"Sending Restore Command: {restore_url}")
        requests.post(restore_url)
        
        # Check status again
        resp = requests.get(status_url)
        data = resp.json()
        if data.get("isolated") == False:
             print("✅ PASS: Agent is RESTORED")
        else:
             print("❌ FAIL: Restore failed")

    except Exception as e:
        print(f"❌ Verification Error: {e}")

    # Cleanup
    await anomaly.delete()
    # keeping employee for future use or manual deletion

if __name__ == "__main__":
    asyncio.run(verify())
