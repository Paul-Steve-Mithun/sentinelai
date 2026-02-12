import requests
import time

url = "http://localhost:8000/api/ml/train"

print("⏳ Triggering model training...")
try:
    response = requests.post(url)
    if response.status_code == 200:
        print("✅ Model trained successfully!")
        print(response.json())
    else:
        print(f"❌ Training failed: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Error: {e}")
