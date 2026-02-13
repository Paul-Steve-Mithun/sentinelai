import requests
import json

BACKEND_URL = "http://3.106.209.92:8000"
EMPLOYEE_ID = "698e45bb6f10e8f6978cd3e9"

def clear_isolation():
    try:
        # Endpoint to update employee status (assuming we have one or can update the employee directly)
        # Based on typical REST patterns or previous routes knowledge
        
        # Method 1: Try to clear anomalies if that's the cause
        print("Attempting to clear anomalies...")
        url = f"{BACKEND_URL}/api/anomalies/clear/{EMPLOYEE_ID}" 
        # Note: I might need to check available routes if this doesn't exist, but 'clear_agent_anomalies.py' in file list suggests similar logic
        
        # Let's try to update the employee status directly if there is an endpoint
        # First, let's see available routes by listing route files if this fails, but let's try a direct update first if possible.
        # Actually, looking at the file list, there is a `clear_agent_anomalies.py` script in the backend folder. 
        # I should probably just use that logic or ask the user to run it if they have access, 
        # but since I am remote to the backend (it's on AWS), I have to use the API.
        
        # Let's try to hit the resolution endpoint
        payload = {
            "resolution_notes": "False positive - clearing for demo",
            "resolution_type": "false_positive"
        }
        
        # We need to find the anomaly IDs to resolve first.
        # Get active threats
        anomalies_url = f"{BACKEND_URL}/api/anomalies/employee/{EMPLOYEE_ID}"
        resp = requests.get(anomalies_url)
        if resp.status_code == 200:
            anomalies = resp.json()
            print(f"Found {len(anomalies)} anomalies.")
            
            for anomaly in anomalies:
                if anomaly.get('severity') in ['critical', 'high']:
                    a_id = anomaly.get('_id') or anomaly.get('id')
                    print(f"Resolving anomaly {a_id}...")
                    
                    resolve_url = f"{BACKEND_URL}/api/anomalies/{a_id}/resolve"
                    res = requests.post(resolve_url, json=payload)
                    print(f"Resolution status: {res.status_code}")
        
        # Check status again
        status_url = f"{BACKEND_URL}/api/agent/{EMPLOYEE_ID}/status"
        final_resp = requests.get(status_url)
        print("\nFinal Status:")
        print(json.dumps(final_resp.json(), indent=2))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clear_isolation()
