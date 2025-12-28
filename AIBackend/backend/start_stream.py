"""
Start Firebase Stream for Real-time Activity Prediction
"""
import requests
import json

def start_firebase_stream():
    print("="*80)
    print("🚀 Starting Firebase Stream for Activity Prediction")
    print("="*80)
    print()
    
    # API endpoint
    url = "http://127.0.0.1:8000/firebase/start"
    
    # Request payload
    payload = {
        "database_url": "https://imu-detection-app-default-rtdb.asia-southeast1.firebasedatabase.app",
        "service_account_path": "serviceAccountKey.json",
        "realtime_db_path": "/sensor_data",
        "firestore_collection": "activity_predictions",
        "user_id": "user1"
    }
    
    print("📡 Sending request to start Firebase listener...")
    print(f"   URL: {url}")
    print(f"   Realtime DB Path: {payload['realtime_db_path']}")
    print(f"   Firestore Collection: {payload['firestore_collection']}")
    print()
    
    try:
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Firebase stream started successfully!")
            print()
            print("Response:")
            print(json.dumps(result, indent=2))
            print()
            print("="*80)
            print("🎯 Backend is now listening to Firebase Realtime Database!")
            print("   - Waiting for sensor data from ESP32...")
            print("   - Predictions will be saved to Firestore automatically")
            print("   - Check the terminal running uvicorn for prediction logs")
            print("="*80)
        else:
            print("❌ Failed to start Firebase stream")
            print()
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print("   Make sure the backend server is running:")
        print("   cd c:\\PBL4\\AIBackend\\backend")
        print("   uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    start_firebase_stream()
