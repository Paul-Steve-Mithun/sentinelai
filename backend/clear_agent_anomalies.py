import asyncio
import os
from database import init_db
from models import Anomaly, Employee
from beanie import PydanticObjectId

async def clear_anomalies():
    # Initialize database
    await init_db()
    
    employee_id_str = "698e325fb524ae2ca3c43efb"
    
    print(f"Clearing anomalies for Employee ObjectId: {employee_id_str}")
    
    try:
        if PydanticObjectId.is_valid(employee_id_str):
            employee = await Employee.get(PydanticObjectId(employee_id_str))
            
            if employee:
                print(f"Employee found: {employee.name}")
                
                # Update all open anomalies to resolved or delete them?
                # For a fresh start, let's delete them or mark as resolved.
                # Deleting is cleaner for "fresh start".
                
                delete_result = await Anomaly.find(
                    Anomaly.employee_id == employee.id
                ).delete()
                
                print(f"Deleted {delete_result.deleted_count} anomalies.")
                
            else:
                print("Employee not found")
        else:
            print("Invalid ID")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(clear_anomalies())
