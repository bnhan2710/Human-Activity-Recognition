import requests
import json

print("="*60)
print("   QUICK DIAGNOSIS - HAR SYSTEM")
print("="*60)

# 1. Check backend
print("\n[1] Checking backend...")
try:
    response = requests.get('http://localhost:8000/health', timeout=3)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Backend is running")
        print(f"   Status: {data.get('status')}")
        print(f"   Model: {data.get('model')}")
        print(f"   Firebase: {data.get('firebase')}")
        print(f"   Buffer size: {data.get('buffer_size')}")
    else:
        print(f"❌ Backend returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ Backend is NOT running!")
    print("\n   Start backend with:")
    print("   cd C:\\PBL4\\AIBackend")
    print("   venv\\Scripts\\activate")
    print("   uvicorn main:app --reload")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# 2. Check Firebase
print("\n[2] Checking Firebase data...")
try:
    import firebase_admin
    from firebase_admin import credentials, db
    
    # Initialize if not already
    try:
        cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://your-project.firebaseio.com'
        })
    except:
        pass  # Already initialized
    
    ref = db.reference('sensor_data')
    data = ref.get()
    
    if data:
        sample_count = len([k for k in data.keys() if 'sample' in str(k) or str(k).isdigit()])
        print(f"✅ Firebase has data")
        print(f"   Total samples: {sample_count}")
        
        # Show first sample
        if 'sample_0' in data:
            s = data['sample_0']
        elif 0 in data:
            s = data[0]
        elif '0' in data:
            s = data['0']
        else:
            s = list(data.values())[0]
        
        print(f"   First sample:")
        print(f"     ax={s.get('ax_g', 0):.5f}, ay={s.get('ay_g', 0):.5f}, az={s.get('az_g', 0):.5f}")
    else:
        print("❌ No data in Firebase!")
        print("\n   Upload test data:")
        print("   python upload_test_data.py")
        exit(1)
        
except FileNotFoundError:
    print("❌ serviceAccountKey.json not found!")
    exit(1)
except Exception as e:
    print(f"⚠️ Cannot check Firebase: {e}")

# 3. Test prediction
print("\n[3] Testing prediction with 40 samples...")
try:
    # Get 40 samples
    samples = []
    for i in range(40):
        key = f'sample_{i}'
        if key in data:
            s = data[key]
        elif i in data:
            s = data[i]
        elif str(i) in data:
            s = data[str(i)]
        else:
            continue
        
        samples.append({
            'ax_g': float(s.get('ax_g', 0)),
            'ay_g': float(s.get('ay_g', 0)),
            'az_g': float(s.get('az_g', 0)),
            'gx_dps': float(s.get('gx_dps', 0)),
            'gy_dps': float(s.get('gy_dps', 0)),
            'gz_dps': float(s.get('gz_dps', 0)),
            'amag_g': float(s.get('amag_g', 0)),
            'pitch_kf': float(s.get('pitch_kf', 0)),
            'roll_kf': float(s.get('roll_kf', 0)),
            'timestamp': int(s.get('time_ms', 0))
        })
    
    if len(samples) < 40:
        print(f"⚠️ Only {len(samples)} samples available (need 40)")
    
    print(f"   Sending {len(samples)} samples to backend...")
    response = requests.post(
        'http://localhost:8000/predict',
        json=samples,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n{'='*60}")
        print(f"🎯 PREDICTION SUCCESS!")
        print(f"{'='*60}")
        print(f"   Activity: {result['activity']}")
        print(f"   Confidence: {result['confidence']:.2%}")
        print(f"\n   All probabilities:")
        for act, prob in sorted(result['probabilities'].items(), key=lambda x: x[1], reverse=True):
            bar = '█' * int(prob * 50)
            print(f"     {act:12s} [{prob:6.2%}] {bar}")
        print(f"{'='*60}")
    else:
        print(f"❌ Prediction failed: {response.status_code}")
        print(f"   Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error during prediction: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("   DIAGNOSIS COMPLETE")
print("="*60)
