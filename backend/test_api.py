"""
Test script for Human Activity Recognition Backend
Demonstrates how to use the API
"""

import requests
import json
import time
import numpy as np

# Configuration
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*80)
    print("TEST 1: Health Check")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def test_single_prediction():
    """Test single sample prediction"""
    print("\n" + "="*80)
    print("TEST 2: Single Sample Prediction")
    print("="*80)
    
    # Simulate walking sensor data
    sensor_data = {
        "ax_g": 0.05,
        "ay_g": 0.98,
        "az_g": 0.15,
        "gx_dps": 1.2,
        "gy_dps": -0.5,
        "gz_dps": 0.3,
        "amag_g": 1.01,
        "pitch_kf": 5.2,
        "roll_kf": 2.8,
        "timestamp": int(time.time() * 1000)
    }
    
    # Send multiple samples to fill buffer
    print("\nFilling buffer with 40 samples...")
    for i in range(40):
        # Add some noise to make it realistic
        data = sensor_data.copy()
        data['ax_g'] += np.random.normal(0, 0.02)
        data['ay_g'] += np.random.normal(0, 0.02)
        data['az_g'] += np.random.normal(0, 0.02)
        data['timestamp'] = int(time.time() * 1000) + i * 50  # 20Hz
        
        response = requests.post(f"{BASE_URL}/predict/single", json=data)
        
        if response.status_code == 202:
            print(f"  Sample {i+1}/40: Buffering... {response.json()['detail']}")
        elif response.status_code == 200:
            print(f"\n✅ Prediction successful!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
        
        time.sleep(0.05)  # 20Hz sampling rate
    
    return False


def test_batch_prediction():
    """Test batch prediction"""
    print("\n" + "="*80)
    print("TEST 3: Batch Prediction")
    print("="*80)
    
    # Generate synthetic walking data
    print("\nGenerating 50 samples of walking data...")
    
    samples = []
    base_time = int(time.time() * 1000)
    
    for i in range(50):
        # Simulate walking pattern
        t = i * 0.05  # 20Hz
        
        sample = {
            "ax_g": 0.05 + 0.3 * np.sin(2 * np.pi * 1.5 * t) + np.random.normal(0, 0.02),
            "ay_g": 0.98 + 0.1 * np.cos(2 * np.pi * 1.5 * t) + np.random.normal(0, 0.02),
            "az_g": 0.15 + 0.2 * np.sin(2 * np.pi * 1.5 * t) + np.random.normal(0, 0.02),
            "gx_dps": 1.2 + 5.0 * np.sin(2 * np.pi * 1.5 * t) + np.random.normal(0, 0.5),
            "gy_dps": -0.5 + 3.0 * np.cos(2 * np.pi * 1.5 * t) + np.random.normal(0, 0.5),
            "gz_dps": 0.3 + 2.0 * np.sin(2 * np.pi * 1.5 * t) + np.random.normal(0, 0.5),
            "amag_g": 1.0 + 0.1 * np.abs(np.sin(2 * np.pi * 1.5 * t)),
            "pitch_kf": 5.2 + 10.0 * np.sin(2 * np.pi * 1.5 * t),
            "roll_kf": 2.8 + 8.0 * np.cos(2 * np.pi * 1.5 * t),
            "timestamp": base_time + i * 50
        }
        samples.append(sample)
    
    batch_data = {
        "data": samples,
        "device_id": "ESP32_TEST"
    }
    
    print(f"Sending batch of {len(samples)} samples...")
    response = requests.post(f"{BASE_URL}/predict/batch", json=batch_data)
    
    if response.status_code == 200:
        print(f"\n✅ Batch prediction successful!")
        result = response.json()
        print(f"\nPrediction Results:")
        print(f"  Activity: {result['activity']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Samples Used: {result['samples_used']}")
        print(f"\nProbabilities:")
        for activity, prob in result['probabilities'].items():
            print(f"  {activity:12s}: {prob:.2%}")
        return True
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return False


def test_buffer_status():
    """Test buffer status endpoint"""
    print("\n" + "="*80)
    print("TEST 4: Buffer Status")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/buffer/status")
    
    if response.status_code == 200:
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        return False


def test_clear_buffer():
    """Test clear buffer endpoint"""
    print("\n" + "="*80)
    print("TEST 5: Clear Buffer")
    print("="*80)
    
    response = requests.post(f"{BASE_URL}/buffer/clear")
    
    if response.status_code == 200:
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        return False


def test_different_activities():
    """Test predictions for different activity patterns"""
    print("\n" + "="*80)
    print("TEST 6: Different Activity Patterns")
    print("="*80)
    
    activities = {
        "SITTING": {
            "ax_g": 0.01,
            "ay_g": 0.99,
            "az_g": 0.05,
            "gx_dps": 0.1,
            "gy_dps": 0.1,
            "gz_dps": 0.1,
            "amag_g": 1.0,
            "pitch_kf": 1.0,
            "roll_kf": 1.0
        },
        "WALKING": {
            "ax_g": 0.05,
            "ay_g": 0.98,
            "az_g": 0.15,
            "gx_dps": 1.2,
            "gy_dps": -0.5,
            "gz_dps": 0.3,
            "amag_g": 1.01,
            "pitch_kf": 5.2,
            "roll_kf": 2.8
        },
        "RUNNING": {
            "ax_g": 0.15,
            "ay_g": 0.95,
            "az_g": 0.25,
            "gx_dps": 5.2,
            "gy_dps": -2.5,
            "gz_dps": 1.3,
            "amag_g": 1.05,
            "pitch_kf": 15.2,
            "roll_kf": 8.8
        }
    }
    
    results = {}
    
    for activity_name, base_pattern in activities.items():
        print(f"\n--- Testing {activity_name} pattern ---")
        
        # Generate 50 samples with this pattern
        samples = []
        base_time = int(time.time() * 1000)
        
        for i in range(50):
            t = i * 0.05
            
            sample = base_pattern.copy()
            
            # Add periodic motion
            if activity_name in ["WALKING", "RUNNING"]:
                freq = 1.5 if activity_name == "WALKING" else 2.5
                sample['ax_g'] += 0.3 * np.sin(2 * np.pi * freq * t)
                sample['gx_dps'] += 5.0 * np.sin(2 * np.pi * freq * t)
                sample['pitch_kf'] += 10.0 * np.sin(2 * np.pi * freq * t)
            
            # Add noise
            for key in ['ax_g', 'ay_g', 'az_g']:
                sample[key] += np.random.normal(0, 0.02)
            for key in ['gx_dps', 'gy_dps', 'gz_dps']:
                sample[key] += np.random.normal(0, 0.5)
            
            sample['timestamp'] = base_time + i * 50
            samples.append(sample)
        
        # Predict
        batch_data = {
            "data": samples,
            "device_id": f"TEST_{activity_name}"
        }
        
        response = requests.post(f"{BASE_URL}/predict/batch", json=batch_data)
        
        if response.status_code == 200:
            result = response.json()
            results[activity_name] = result
            
            print(f"  Predicted: {result['activity']} (confidence: {result['confidence']:.2%})")
            print(f"  Top 3 probabilities:")
            
            sorted_probs = sorted(result['probabilities'].items(), 
                                key=lambda x: x[1], reverse=True)[:3]
            for act, prob in sorted_probs:
                print(f"    {act:12s}: {prob:.2%}")
        else:
            print(f" Error: {response.status_code}")
    
    return len(results) > 0


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 HUMAN ACTIVITY RECOGNITION BACKEND TESTS")
    print("="*80)
    print(f"\nBase URL: {BASE_URL}")
    print("\nMake sure the server is running: python main.py")
    
    input("\nPress Enter to start tests...")
    
    # Check if server is running
    try:
        requests.get(BASE_URL)
    except requests.exceptions.ConnectionError:
        print("\n Error: Cannot connect to server. Make sure it's running!")
        print("   Run: python main.py")
        return
    
    tests = [
        ("Health Check", test_health),
        ("Buffer Status", test_buffer_status),
        ("Clear Buffer", test_clear_buffer),
        ("Batch Prediction", test_batch_prediction),
        ("Different Activities", test_different_activities),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n Test '{test_name}' failed with error: {e}")
            results[test_name] = False
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = " PASS" if result else "FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n All tests passed!")
    else:
        print("\n Some tests failed. Check the output above.")


if __name__ == "__main__":
    run_all_tests()
