import firebase_admin
from firebase_admin import credentials, db
import requests
import time
import json

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://imu-detection-app-default-rtdb.asia-southeast1.firebasedatabase.app/'
})


# FastAPI endpoint
API_URL = 'http://localhost:8000/sensor_data'

def test_send_data():
    """
    Test gửi dữ liệu từ Realtime DB vào FastAPI
    Gửi từng sample một, khi đủ 40 samples thì predict
    """
    print("🔄 Fetching data from Firebase Realtime Database...")
    
    # Lấy dữ liệu từ root, sau đó vào sensor_data
    root_ref = db.reference('/')
    root_data = root_ref.get()
    
    if not root_data or 'sensor_data' not in root_data:
        print("❌ No sensor_data found in Realtime Database")
        return
    
    sensor_data_node = root_data['sensor_data']
    print("✅ Found 'sensor_data' node")
    
    # Get all timestamps sorted (descending - newest first)
    timestamps = sorted(sensor_data_node.keys(), key=lambda x: int(x) if x.isdigit() else 0, reverse=True)
    print(f"   Found {len(timestamps)} timestamps")
    print(f"   Newest timestamps: {timestamps[:5]}...")
    
    # Collect 40 most recent samples
    all_samples = []
    
    for timestamp in timestamps:
        timestamp_data = sensor_data_node[timestamp]
        
        # Get all sample keys from this timestamp (sorted descending)
        sample_keys = sorted([k for k in timestamp_data.keys() if 'sample' in str(k).lower()], reverse=True)
        
        if len(all_samples) < 40:
            print(f"   Timestamp {timestamp}: {len(sample_keys)} samples")
        
        for sample_key in sample_keys:
            if len(all_samples) >= 40:
                break
            
            try:
                sample = timestamp_data[sample_key]
                
                # Check if sample is dict with sensor data
                if not isinstance(sample, dict):
                    continue
                
                # Check required fields
                required_fields = ['ax_g', 'ay_g', 'az_g', 'gx_dps', 'gy_dps', 'gz_dps']
                if not all(field in sample for field in required_fields):
                    continue
                
                # Format data
                sensor_data = {
                    'ax_g': float(sample.get('ax_g', 0)),
                    'ay_g': float(sample.get('ay_g', 0)),
                    'az_g': float(sample.get('az_g', 0)),
                    'gx_dps': float(sample.get('gx_dps', 0)),
                    'gy_dps': float(sample.get('gy_dps', 0)),
                    'gz_dps': float(sample.get('gz_dps', 0)),
                    'amag_g': float(sample.get('amag_g', 0)),
                    'pitch_kf': float(sample.get('pitch_kf', 0)),
                    'roll_kf': float(sample.get('roll_kf', 0)),
                    'timestamp': int(sample.get('time_ms', 0))
                }
                all_samples.append(sensor_data)
                
                if len(all_samples) <= 3:
                    print(f"  Sample {len(all_samples)}: ax={sensor_data['ax_g']:.5f}, "
                          f"ay={sensor_data['ay_g']:.5f}, az={sensor_data['az_g']:.5f}")
            
            except Exception as e:
                continue
        
        if len(all_samples) >= 40:
            break
    
    print(f"\n✅ Collected {len(all_samples)} samples from {len(timestamps)} timestamps")
    
    if len(all_samples) < 40:
        print(f"⚠️ Warning: Only {len(all_samples)} samples available, need 40 for prediction")
        print(f"   Will send all available samples")
    
    # Lấy 40 samples đầu tiên (hoặc tất cả nếu < 40)
    samples = []
    
    # Sử dụng sample_keys đã tìm được
    for i, key in enumerate(sorted(sample_keys)[:40]):
        try:
            sample = data[key]
            
            # Check if sample is dict with sensor data
            if not isinstance(sample, dict):
                print(f"⚠️ Sample {key} is not a dict, skipping...")
                continue
            
            # Check required fields
            required_fields = ['ax_g', 'ay_g', 'az_g', 'gx_dps', 'gy_dps', 'gz_dps']
            if not all(field in sample for field in required_fields):
                print(f"⚠️ Sample {key} missing required fields, skipping...")
                continue
            
            # Format data theo API schema
            sensor_data = {
                'ax_g': float(sample.get('ax_g', 0)),
                'ay_g': float(sample.get('ay_g', 0)),
                'az_g': float(sample.get('az_g', 0)),
                'gx_dps': float(sample.get('gx_dps', 0)),
                'gy_dps': float(sample.get('gy_dps', 0)),
                'gz_dps': float(sample.get('gz_dps', 0)),
                'amag_g': float(sample.get('amag_g', 0)),
                'pitch_kf': float(sample.get('pitch_kf', 0)),
                'roll_kf': float(sample.get('roll_kf', 0)),
                'timestamp': int(sample.get('time_ms', 0))
            }
            samples.append(sensor_data)
            
            if len(samples) <= 3:  # Print first 3 samples
                print(f"  Sample {key}: ax={sensor_data['ax_g']:.5f}, "
                      f"ay={sensor_data['ay_g']:.5f}, az={sensor_data['az_g']:.5f}")
        
        except Exception as e:
            print(f"⚠️ Error processing sample {key}: {e}")
            continue
    
    if len(all_samples) < 40:
        print(f"⚠️ Warning: Only {len(all_samples)} samples available, need 40 for prediction")
        print(f"   Prediction may not be accurate")
    
    samples = all_samples[:40]  # Use collected samples
    
    print(f"\n🚀 Sending {len(samples)} samples to API (fast mode)...")
    
    # Gửi từng sample một với delay ngắn hơn
    for i, sample in enumerate(samples):
        try:
            response = requests.post(API_URL, json=sample, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'prediction' in result:
                    pred = result['prediction']
                    print(f"\n{'='*60}")
                    print(f"🎯 PREDICTION RESULT (After {i+1} samples)")
                    print(f"{'='*60}")
                    print(f"   Activity: {pred['activity']}")
                    print(f"   Confidence: {pred['confidence']:.2%}")
                    print(f"\n   Probabilities:")
                    for activity, prob in sorted(pred['probabilities'].items(), 
                                                 key=lambda x: x[1], reverse=True):
                        bar = '█' * int(prob * 50)
                        print(f"     {activity:12s} [{prob:6.2%}] {bar}")
                else:
                    need = result.get('need', 40 - (i + 1))
                    print(f"  [{i+1:2d}/40] Buffering... (need {need} more samples)", end='\r')
            else:
                print(f"\n❌ Error: {response.status_code} - {response.text}")
            
            # Delay ngắn để không quá tải server (10ms)
            time.sleep(0.01)
            
        except requests.exceptions.Timeout:
            print(f"\n⚠️ Timeout sending sample {i}")
        except Exception as e:
            print(f"\n❌ Error sending sample {i}: {e}")
    
    print("\n" + "="*60)
    print("✅ Test completed!")
    print("="*60)

def test_manual_prediction():
    """
    Test manual prediction với 40 samples
    Gửi tất cả 40 samples cùng lúc vào endpoint /predict
    """
    print("🔄 Testing manual prediction endpoint...")
    print("   Collecting samples from multiple timestamps...")
    
    # Lấy dữ liệu
    root_ref = db.reference('/')
    root_data = root_ref.get()
    
    if not root_data or 'sensor_data' not in root_data:
        print("❌ No sensor_data found")
        return
    
    sensor_data_node = root_data['sensor_data']
    timestamps = sorted(sensor_data_node.keys(), key=lambda x: int(x) if x.isdigit() else 0)
    
    print(f"✅ Found {len(timestamps)} timestamps")
    
    # Collect 40 samples from multiple timestamps
    samples = []
    for timestamp in timestamps:
        timestamp_data = sensor_data_node[timestamp]
        sample_keys = sorted([k for k in timestamp_data.keys() if 'sample' in str(k).lower()])
        
        for sample_key in sample_keys:
            if len(samples) >= 40:
                break
            
            try:
                sample = timestamp_data[sample_key]
                if not isinstance(sample, dict):
                    continue
                
                samples.append({
                    'ax_g': float(sample.get('ax_g', 0)),
                    'ay_g': float(sample.get('ay_g', 0)),
                    'az_g': float(sample.get('az_g', 0)),
                    'gx_dps': float(sample.get('gx_dps', 0)),
                    'gy_dps': float(sample.get('gy_dps', 0)),
                    'gz_dps': float(sample.get('gz_dps', 0)),
                    'amag_g': float(sample.get('amag_g', 0)),
                    'pitch_kf': float(sample.get('pitch_kf', 0)),
                    'roll_kf': float(sample.get('roll_kf', 0)),
                    'timestamp': int(sample.get('time_ms', 0))
                })
            except:
                continue
        
        if len(samples) >= 40:
            break
    
    print(f"✅ Collected {len(samples)} samples")
    
    if len(samples) < 40:
        print(f"⚠️ Only {len(samples)} samples, need 40 for best accuracy")
    
    print(f"\n🚀 Sending to /predict endpoint...")
    
    try:
        response = requests.post(
            'http://localhost:8000/predict',
            json=samples,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n{'='*60}")
            print(f"🎯 PREDICTION RESULT")
            print(f"{'='*60}")
            print(f"   Activity: {result['activity']}")
            print(f"   Confidence: {result['confidence']:.2%}")
            print(f"\n   Probabilities (sorted by confidence):")
            for activity, prob in sorted(result['probabilities'].items(), 
                                         key=lambda x: x[1], reverse=True):
                bar = '█' * int(prob * 50)
                print(f"     {activity:12s} [{prob:6.2%}] {bar}")
            print(f"{'='*60}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.Timeout:
        print("❌ Request timeout - backend may be processing")
    except Exception as e:
        print(f"❌ Error: {e}")

def print_sample_data():
    """
    In ra dữ liệu mẫu từ Realtime DB
    """
    print("📊 Sample data from Realtime Database:")
    print("=" * 60)
    
    ref = db.reference('sensor_data')
    data = ref.get()
    
    if not data:
        print("❌ No data found")
        return
    
    # In 5 samples đầu
    for i in range(min(5, len(data))):
        sample_key = f'sample_{i}'
        if sample_key in data:
            sample = data[sample_key]
            print(f"\nSample {i}:")
            print(f"  Time: {sample.get('time_ms', 0)} ms")
            print(f"  Accel (g):    ax={sample.get('ax_g', 0):7.4f}  "
                  f"ay={sample.get('ay_g', 0):7.4f}  az={sample.get('az_g', 0):7.4f}")
            print(f"  Gyro (dps):   gx={sample.get('gx_dps', 0):7.4f}  "
                  f"gy={sample.get('gy_dps', 0):7.4f}  gz={sample.get('gz_dps', 0):7.4f}")
            print(f"  Magnitude:    {sample.get('amag_g', 0):.4f} g")
            print(f"  Orientation:  pitch={sample.get('pitch_kf', 0):7.4f}°  "
                  f"roll={sample.get('roll_kf', 0):7.4f}°")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    print("=" * 60)
    print("  PBL4 HAR - Realtime Database Test")
    print("=" * 60)
    print()
    
    # 1. In dữ liệu mẫu
    print_sample_data()
    
    print("\n\nChoose test mode:")
    print("1. Send data sample by sample (realtime simulation)")
    print("2. Send 40 samples at once (manual prediction)")
    print("3. Both")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        test_send_data()
    elif choice == '2':
        test_manual_prediction()
    elif choice == '3':
        test_send_data()
        print("\n" + "=" * 60)
        test_manual_prediction()
    else:
        print("Invalid choice")
