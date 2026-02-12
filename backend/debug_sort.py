import asyncio
import os
from database import init_db
from models import MitreMapping, Anomaly, Employee
from beanie import PydanticObjectId

async def test_sort():
    await init_db()
    
    print("Testing sort syntax...")
    try:
        # Create dummy entry if none exists (just to be safe, though empty list is fine for sort check)
        # We just want to see if the query construction fails
        
        query = MitreMapping.find_all()
        print("Constructing sort query with -models.MitreMapping.confidence...")
        try:
            # The suspicious syntax
            results = await query.sort(-MitreMapping.confidence).to_list()
            print("Sort with unary minus worked!")
        except Exception as e:
            print(f"Sort with unary minus FAILED: {e}")
            
        print("\nConstructing sort query with string '-confidence'...")
        try:
            results = await query.sort("-confidence").to_list()
            print("Sort with string worked!")
        except Exception as e:
            print(f"Sort with string FAILED: {e}")

    except Exception as e:
        print(f"General Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_sort())
