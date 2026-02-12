import requests
import time
import random
import uuid
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000/api"

def register_agent():
    print("🤖 Registering malicious agent...")
    system_info = {
        'hostname': f"DESKTOP-DEMO-{random.randint(1000,9999)}",
        'username': "demo_user",
        'os': "Windows",
        'os_version': "10.0.19045",
        'ip_address': "192.168.1.105"
    }
    try:
        response = requests.post(f"{BASE_URL}/agent/register", json=system_info)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Registered Agent ID: {data['employee_id']}")
            return data['employee_id']
    except Exception as e:
        print(f"❌ Registration failed: {e}")
    return None

def send_events(employee_id, count=10, type="normal"):
    print(f"📡 Sending {count} {type} events...")
    events = []
    
    for i in range(count):
        if type == "normal":
            cpu = random.uniform(5.0, 15.0)
            ram = random.uniform(30.0, 40.0)
            event_type = "file_access"
        elif type == "attack":
            # Simulate Crypto Miner
            cpu = random.uniform(85.0, 99.0)
            ram = random.uniform(70.0, 90.0)
            event_type = "process_start"
        
        event = {
            "employee_id": employee_id,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": "Office_Network",
            "ip_address": "192.168.1.105",
            "port": 443,
            "file_path": "C:\\Users\\demo\\AppData\\Local\\Temp\\miner.exe" if type == "attack" else "C:\\Users\\demo\\Documents\\report.docx",
            "action": "execute" if type == "attack" else "read",
            "success": True,
            "cpu_usage": cpu,
            "memory_usage": ram
        }
        events.append(event)
    
    try:
        # Use bulk endpoint which now triggers anomalies
        response = requests.post(f"{BASE_URL}/events/bulk", json=events)
        if response.status_code == 200:
            print(f"✅ Sent {len(events)} events.")
        else:
            print(f"❌ Failed to send events: {response.text}")
    except Exception as e:
        print(f"❌ Error sending events: {e}")

def trigger_training():
    print("🧠 Triggering model training...")
    try:
        # Check health first
        health = requests.get(f"{BASE_URL}/health/system").json()
        if health['ml_model']['status'] == 'active':
            print("✅ Model is already active.")
            return True
            
        response = requests.post(f"{BASE_URL}/ml/train")
        if response.status_code == 200:
            print("✅ Model trained successfully!")
            return True
        else:
            print(f"⚠️ Model training skipped/failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Training error: {e}")
        return False

def main():
    print("🚀 SENTINEL AI - HACKATHON DEMO SIMULATION 🚀")
    print("===============================================")
    
    # 1. Register
    emp_id = register_agent()
    if not emp_id:
        return

    # 2. Establish Baseline (Normal Behavior)
    # We need enough data for the model to learn "normal"
    print("\n[Phase 1] Establishing Baseline...")
    for _ in range(3):
        send_events(emp_id, count=5, type="normal")
        time.sleep(1)
        
    # 3. Train Model (if needed)
    print("\n[Phase 2] Training Model...")
    trigger_training()
    time.sleep(2)
    
    # 4. Launch Attack
    print("\n[Phase 3] ⚔️ LAUNCHING CRYPTO-MINING ATTACK ⚔️")
    input("Press Enter to simulate attack...")
    send_events(emp_id, count=5, type="attack")
    
    print("\n✅ Attack simulation complete.")
    print("👉 Check the Dashboard for 'High CPU Usage' alerts and MITRE T1496 mapping.")

if __name__ == "__main__":
    main()
