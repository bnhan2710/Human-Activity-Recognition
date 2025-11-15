import firebase_admin
from firebase_admin import credentials, db
import time
import random
import math

# Initialize Firebase
try:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred, {
       'databaseURL': 'https://imu-detection-app-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })
except:
    pass

def generate_activity_samples(activity, num_samples=10, start_time=0):
    """Generate realistic samples for different activities"""
    samples = {}
    
    for i in range(num_samples):
        t = i / num_samples * 2 * math.pi
        
        if activity == 'WALKING':
            sample = {
                'ax_g': 0.3 * math.sin(t) + random.uniform(-0.05, 0.05),
                'ay_g': 0.2 * math.cos(t) + random.uniform(-0.05, 0.05),
                'az_g': 1.0 + 0.1 * math.sin(2*t) + random.uniform(-0.05, 0.05),
                'gx_dps': 10 * math.sin(t) + random.uniform(-2, 2),
                'gy_dps': 5 * math.cos(t) + random.uniform(-2, 2),
                'gz_dps': 3 * math.sin(t) + random.uniform(-1, 1),
                'amag_g': random.uniform(0.9, 1.1),
                'pitch_kf': 5 * math.sin(t),
                'roll_kf': 3 * math.cos(t),
                'time_ms': start_time + i * 50
            }
        elif activity == 'RUNNING':
            sample = {
                'ax_g': 0.6 * math.sin(t*2) + random.uniform(-0.1, 0.1),
                'ay_g': 0.4 * math.cos(t*2) + random.uniform(-0.1, 0.1),
                'az_g': 1.0 + 0.3 * math.sin(3*t) + random.uniform(-0.1, 0.1),
                'gx_dps': 20 * math.sin(t*2) + random.uniform(-5, 5),
                'gy_dps': 15 * math.cos(t*2) + random.uniform(-5, 5),
                'gz_dps': 10 * math.sin(t*2) + random.uniform(-3, 3),
                'amag_g': random.uniform(1.1, 1.5),
                'pitch_kf': 10 * math.sin(t*2),
                'roll_kf': 7 * math.cos(t*2),
                'time_ms': start_time + i * 50
            }
        elif activity == 'STANDING':
            sample = {
                'ax_g': random.uniform(-0.03, 0.03),
                'ay_g': random.uniform(-0.03, 0.03),
                'az_g': random.uniform(0.97, 1.03),
                'gx_dps': random.uniform(-0.5, 0.5),
                'gy_dps': random.uniform(-0.5, 0.5),
                'gz_dps': random.uniform(-0.5, 0.5),
                'amag_g': random.uniform(0.97, 1.03),
                'pitch_kf': random.uniform(-2, 2),
                'roll_kf': random.uniform(-2, 2),
                'time_ms': start_time + i * 50
            }
        else:  # SITTING
            sample = {
                'ax_g': random.uniform(-0.02, 0.02),
                'ay_g': random.uniform(-0.02, 0.02),
                'az_g': random.uniform(0.98, 1.02),
                'gx_dps': random.uniform(-0.3, 0.3),
                'gy_dps': random.uniform(-0.3, 0.3),
                'gz_dps': random.uniform(-0.3, 0.3),
                'amag_g': random.uniform(0.98, 1.02),
                'pitch_kf': random.uniform(-1, 1),
                'roll_kf': random.uniform(-1, 1),
                'time_ms': start_time + i * 50
            }
        
        samples[f'sample_{i}'] = sample
    
    return samples

def stream_data_continuous():
    """Stream data continuously to simulate realtime sensor"""
    print("🔄 Streaming data continuously to Firebase...")
    print("   Press Ctrl+C to stop\n")
    
    ref = db.reference('sensor_data')
    
    activities = ['WALKING', 'RUNNING', 'STANDING', 'SITTING']
    current_time = int(time.time() * 1000)
    
    activity_durations = {
        'WALKING': 15,    # 15 seconds
        'RUNNING': 10,    # 10 seconds
        'STANDING': 20,   # 20 seconds
        'SITTING': 25     # 25 seconds
    }
    
    try:
        cycle = 0
        while True:
            # Cycle through activities
            for activity in activities:
                duration = activity_durations[activity]
                num_batches = duration // 2  # Each batch = 10 samples = 0.5s @ 20Hz = 2s interval
                
                print(f"\n{'='*60}")
                print(f"🎯 Activity: {activity} (duration: {duration}s)")
                print(f"{'='*60}")
                
                for batch in range(num_batches):
                    # Generate 10 samples
                    timestamp = current_time
                    samples = generate_activity_samples(activity, 10, timestamp)
                    
                    # Upload to Firebase
                    ref.child(str(timestamp)).set(samples)
                    
                    print(f"  [{batch+1}/{num_batches}] Uploaded timestamp {timestamp} with 10 samples ({activity})")
                    
                    current_time += 2000  # 2 second interval
                    time.sleep(2)  # Wait 2 seconds
                
                print(f"✅ Completed {activity} cycle")
            
            cycle += 1
            print(f"\n🔁 Completed cycle {cycle}. Repeating...\n")
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Stopped streaming")
        print(f"📊 Total cycles: {cycle}")

def stream_single_activity():
    """Stream one activity continuously"""
    print("Choose activity to stream:")
    print("1. WALKING")
    print("2. RUNNING")
    print("3. STANDING")
    print("4. SITTING")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    activities = {
        '1': 'WALKING',
        '2': 'RUNNING',
        '3': 'STANDING',
        '4': 'SITTING'
    }
    
    activity = activities.get(choice, 'WALKING')
    
    print(f"\n🔄 Streaming {activity} data continuously...")
    print("   Press Ctrl+C to stop\n")
    
    ref = db.reference('sensor_data')
    current_time = int(time.time() * 1000)
    
    try:
        batch = 0
        while True:
            timestamp = current_time
            samples = generate_activity_samples(activity, 10, timestamp)
            
            ref.child(str(timestamp)).set(samples)
            
            batch += 1
            print(f"  [{batch}] Uploaded timestamp {timestamp} ({activity})")
            
            current_time += 2000
            time.sleep(2)
    
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Stopped streaming")
        print(f"📊 Total batches: {batch}")

if __name__ == '__main__':
    print("=" * 60)
    print("  CONTINUOUS DATA STREAMING")
    print("=" * 60)
    print()
    print("Choose mode:")
    print("1. Stream all activities (cycle)")
    print("2. Stream single activity")
    
    mode = input("\nEnter choice (1/2): ").strip()
    
    if mode == '1':
        stream_data_continuous()
    elif mode == '2':
        stream_single_activity()
    else:
        print("Invalid choice")
