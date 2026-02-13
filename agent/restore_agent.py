import requests
import json

BACKEND_URL = "http://3.106.209.92:8000"
EMPLOYEE_ID = "698e45bb6f10e8f6978cd3e9"

def restore_agent():
    try:
        url = f"{BACKEND_URL}/api/agent/{EMPLOYEE_ID}/restore"
        print(f"Restoring agent at: {url}")
        
        # POST request to restore
        response = requests.post(url)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Agent restored successfully!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    restore_agent()
