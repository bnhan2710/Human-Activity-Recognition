"""
Test Firebase /start endpoint directly
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_firebase_start():
    print("="*80)
    print("Testing /firebase/start endpoint")
    print("="*80)
    
    payload = {
        "database_url": "https://imu-detection-app-default-rtdb.asia-southeast1.firebasedatabase.app/",
        "service_account_path": "serviceAccountKey.json",
        "realtime_db_path": "/sensor_data",
        "firestore_collection": "activity_predictions",
        "user_id": "user1"
    }
    
    print(f"POST {API_URL}/firebase/start")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(f"{API_URL}/firebase/start", json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print()
            print("✅ Firebase stream started successfully!")
        else:
            print()
            print("❌ Failed to start Firebase stream")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("   Make sure the server is running: python main.py")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("="*80)

if __name__ == "__main__":
    test_firebase_start()
