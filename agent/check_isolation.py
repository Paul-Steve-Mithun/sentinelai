import requests
import json

BACKEND_URL = "http://3.106.209.92:8000"
EMPLOYEE_ID = "698e45bb6f10e8f6978cd3e9"

def check_status():
    try:
        url = f"{BACKEND_URL}/api/agent/{EMPLOYEE_ID}/status"
        print(f"Checking status at: {url}")
        
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response Data:")
            print(json.dumps(data, indent=2))
            
            if data.get('isolated'):
                print("\n⚠️  AGENT IS MARKED AS ISOLATED!")
            else:
                print("\n✅ Agent is NOT isolated.")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    check_status()
