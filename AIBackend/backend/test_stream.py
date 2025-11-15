"""
Test Script for Firebase Realtime Stream
Tests the complete flow: Realtime DB -> Prediction -> Firestore
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_separator():
    print("\n" + "="*80 + "\n")

def test_health_check():
    """Test if API is running"""
    print("🏥 Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def start_stream():
    """Start Firebase stream"""
    print("🚀 Starting Firebase Stream...")
    url = f"{BASE_URL}/firebase/start"
    payload = {
        "database_url": "https://imu-detection-app-default-rtdb.asia-southeast1.firebasedatabase.app",
        "service_account_path": "serviceAccountKey.json",
        "realtime_db_path": "/sensor_data",
        "firestore_collection": "activity_predictions",
        "user_id": "user1"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_stream_status():
    """Check current stream status"""
    print("📊 Checking Stream Status...")
    url = f"{BASE_URL}/stream/status"
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
    return result

def check_buffer_status():
    """Check buffer status"""
    print("🔢 Checking Buffer Status...")
    url = f"{BASE_URL}/buffer/status"
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
    return result

def get_recent_predictions(user_id="user1", limit=5):
    """Get recent predictions from Firestore"""
    print(f"📖 Getting Recent Predictions (user_id={user_id}, limit={limit})...")
    url = f"{BASE_URL}/firestore/predictions?user_id={user_id}&limit={limit}"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        
        if result.get('status') == 'success':
            print(f"\n✅ Found {result['count']} predictions:")
            for i, pred in enumerate(result['predictions'], 1):
                print(f"\n--- Prediction {i} ---")
                print(f"  ID: {pred.get('id', 'N/A')}")
                print(f"  Activity: {pred.get('activity', 'N/A')}")
                print(f"  Confidence: {pred.get('confidence', 0)*100:.2f}%")
                print(f"  Created: {pred.get('created_at', 'N/A')}")
        else:
            print(json.dumps(result, indent=2))
        
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_prediction_by_id(doc_id):
    """Get specific prediction by ID"""
    print(f"🔍 Getting Prediction {doc_id}...")
    url = f"{BASE_URL}/firestore/predictions/{doc_id}"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def stop_stream():
    """Stop Firebase stream"""
    print("🛑 Stopping Firebase Stream...")
    url = f"{BASE_URL}/firebase/stop"
    
    try:
        response = requests.post(url)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def clear_buffer():
    """Clear data buffer"""
    print("🧹 Clearing Buffer...")
    url = f"{BASE_URL}/buffer/clear"
    response = requests.post(url)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
    return response.status_code == 200

def monitor_stream(duration=30, interval=5):
    """Monitor stream for a specified duration"""
    print(f"👀 Monitoring Stream for {duration} seconds...")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        elapsed = int(time.time() - start_time)
        print(f"\n--- {elapsed}s elapsed ---")
        
        status = check_stream_status()
        
        if status.get('predictions_made', 0) > 0:
            print(f"✅ Predictions made: {status['predictions_made']}")
        
        time.sleep(interval)
    
    print(f"\n✅ Monitoring complete!")

def run_full_test(monitor_duration=30):
    """Run complete test flow"""
    print("\n🎯 Starting Full Stream Test")
    print(f"Time: {datetime.now().isoformat()}")
    print_separator()
    
    # 1. Health check
    if not test_health_check():
        print("❌ API is not healthy. Exiting...")
        return
    print_separator()
    
    # 2. Start stream
    if not start_stream():
        print("❌ Failed to start stream. Exiting...")
        return
    print_separator()
    
    # 3. Wait a bit
    print(f"⏳ Waiting 5 seconds for stream to stabilize...")
    time.sleep(5)
    print_separator()
    
    # 4. Monitor stream
    monitor_stream(duration=monitor_duration, interval=5)
    print_separator()
    
    # 5. Check final status
    print("📊 Final Status Check:")
    check_stream_status()
    print_separator()
    
    # 6. Get predictions
    predictions = get_recent_predictions(limit=10)
    print_separator()
    
    # 7. If we have predictions, show first one in detail
    if predictions and predictions.get('count', 0) > 0:
        first_pred_id = predictions['predictions'][0].get('id')
        if first_pred_id:
            get_prediction_by_id(first_pred_id)
            print_separator()
    
    # 8. Stop stream
    stop_stream()
    print_separator()
    
    print("✅ Full test complete!")

def run_quick_test():
    """Run quick test (10 seconds)"""
    run_full_test(monitor_duration=10)

def main():
    """Main menu"""
    print("\n" + "="*80)
    print("  🔥 Firebase Realtime Stream Test")
    print("="*80)
    print("\nOptions:")
    print("  1. Full Test (30 seconds monitoring)")
    print("  2. Quick Test (10 seconds monitoring)")
    print("  3. Start Stream Only")
    print("  4. Check Status")
    print("  5. Get Recent Predictions")
    print("  6. Stop Stream")
    print("  7. Clear Buffer")
    print("  8. Monitor Stream (custom duration)")
    print("  0. Exit")
    
    choice = input("\nEnter choice: ").strip()
    
    if choice == "1":
        run_full_test(monitor_duration=30)
    elif choice == "2":
        run_quick_test()
    elif choice == "3":
        start_stream()
    elif choice == "4":
        check_stream_status()
        print_separator()
        check_buffer_status()
    elif choice == "5":
        limit = input("Number of predictions to retrieve (default 5): ").strip()
        limit = int(limit) if limit.isdigit() else 5
        get_recent_predictions(limit=limit)
    elif choice == "6":
        stop_stream()
    elif choice == "7":
        clear_buffer()
    elif choice == "8":
        duration = input("Monitor duration (seconds, default 30): ").strip()
        duration = int(duration) if duration.isdigit() else 30
        start_stream()
        time.sleep(2)
        monitor_stream(duration=duration)
        stop_stream()
    elif choice == "0":
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        print("🛑 Stopping stream...")
        stop_stream()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
