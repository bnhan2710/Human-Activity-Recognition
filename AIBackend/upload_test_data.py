import firebase_admin
from firebase_admin import credentials, db
import json

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://your-project.firebaseio.com'  # Thay bằng URL của bạn
})

# Dữ liệu mẫu từ bạn
sample_data = {
    'sample_0': {
        'amag_g': 0.99543,
        'ax_g': 0.00275,
        'ay_g': 0.00067,
        'az_g': 0.99542,
        'gx_dps': 0.0916,
        'gy_dps': -0.03053,
        'gz_dps': 0,
        'pitch_kf': -0.00581,
        'roll_kf': 0.01715,
        'time_ms': 9589
    }
}

# Tạo 40 samples (giả lập STANDING activity)
def generate_standing_samples(num_samples=40):
    """
    Generate 40 samples giống STANDING activity
    (ax, ay nhỏ, az ~ 1g, gyro ~ 0)
    """
    import random
    
    samples = {}
    for i in range(num_samples):
        # STANDING: az ~ 1g, ax, ay nhỏ, gyro ~ 0
        samples[f'sample_{i}'] = {
            'ax_g': random.uniform(-0.05, 0.05),
            'ay_g': random.uniform(-0.05, 0.05),
            'az_g': random.uniform(0.95, 1.05),
            'gx_dps': random.uniform(-0.1, 0.1),
            'gy_dps': random.uniform(-0.1, 0.1),
            'gz_dps': random.uniform(-0.1, 0.1),
            'amag_g': random.uniform(0.95, 1.05),
            'pitch_kf': random.uniform(-1, 1),
            'roll_kf': random.uniform(-1, 1),
            'time_ms': 9589 + i * 50  # 20Hz = 50ms interval
        }
    
    return samples

def generate_walking_samples(num_samples=40):
    """
    Generate 40 samples giống WALKING activity
    (ax, ay có biến đổi tuần hoàn)
    """
    import random
    import math
    
    samples = {}
    for i in range(num_samples):
        # WALKING: có pattern tuần hoàn
        t = i / 40.0 * 2 * math.pi
        samples[f'sample_{i}'] = {
            'ax_g': 0.3 * math.sin(t) + random.uniform(-0.05, 0.05),
            'ay_g': 0.2 * math.cos(t) + random.uniform(-0.05, 0.05),
            'az_g': 1.0 + 0.1 * math.sin(2*t) + random.uniform(-0.05, 0.05),
            'gx_dps': 10 * math.sin(t) + random.uniform(-1, 1),
            'gy_dps': 5 * math.cos(t) + random.uniform(-1, 1),
            'gz_dps': 3 * math.sin(t) + random.uniform(-1, 1),
            'amag_g': random.uniform(0.9, 1.1),
            'pitch_kf': 5 * math.sin(t),
            'roll_kf': 3 * math.cos(t),
            'time_ms': 9589 + i * 50
        }
    
    return samples

def upload_to_firebase(activity='standing'):
    """
    Upload test data to Firebase Realtime DB
    """
    print(f"🔄 Generating {activity.upper()} samples...")
    
    if activity.lower() == 'walking':
        samples = generate_walking_samples(40)
    else:
        samples = generate_standing_samples(40)
    
    print(f"✅ Generated {len(samples)} samples")
    
    # Upload to Firebase
    ref = db.reference('sensor_data')
    
    print(f"📤 Uploading to Firebase Realtime Database...")
    ref.set(samples)
    
    print(f"✅ Upload complete!")
    print(f"\nView at: https://console.firebase.google.com/project/YOUR_PROJECT/database")
    
    # Print first sample
    first_sample = samples['sample_0']
    print(f"\nFirst sample preview:")
    print(json.dumps(first_sample, indent=2))

if __name__ == '__main__':
    print("=" * 60)
    print("  Upload Test Data to Firebase Realtime DB")
    print("=" * 60)
    print()
    print("Choose activity type:")
    print("1. STANDING (stable, no movement)")
    print("2. WALKING (periodic movement)")
    
    choice = input("\nEnter choice (1/2): ").strip()
    
    if choice == '1':
        upload_to_firebase('standing')
    elif choice == '2':
        upload_to_firebase('walking')
    else:
        print("Invalid choice")
