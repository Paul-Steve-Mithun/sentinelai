import asyncio
import os
from database import init_db
from models import Anomaly, Employee
from beanie import PydanticObjectId

async def check_anomalies():
    # Initialize database
    await init_db()
    
    employee_id_str = "698e325fb524ae2ca3c43efb"
    
    try:
        if PydanticObjectId.is_valid(employee_id_str):
            employee = await Employee.get(PydanticObjectId(employee_id_str))
            
            if employee:
                print(f"Employee: {employee.name}")
                anomalies = await Anomaly.find(
                    Anomaly.employee_id == employee.id
                ).sort("-detected_at").to_list()
                
                print(f"Total Anomalies: {len(anomalies)}")
                
                for anomaly in anomalies[:5]: # Show top 5
                    print(f"Time: {anomaly.detected_at}")
                    print(f"Risk: {anomaly.risk_level}")
                    print(f"Status: {anomaly.status}")
                    print(f"Desc: {anomaly.description}")
                    print("-" * 20)
            else:
                print("Employee not found")
        else:
            print("Invalid ID")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_anomalies())
