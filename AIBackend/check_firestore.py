import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

print("=" * 60)
print("  CHECK FIRESTORE DATA")
print("=" * 60)

# Initialize Firebase
try:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
except:
    pass

db = firestore.client()

print("\n[1] Checking activity_predictions collection...")
try:
    docs = db.collection('activity_predictions').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(5).stream()
    
    predictions = list(docs)
    
    if predictions:
        print(f"✅ Found {len(predictions)} predictions\n")
        
        for i, doc in enumerate(predictions):
            data = doc.to_dict()
            timestamp = data.get('timestamp')
            if timestamp:
                time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(timestamp, 'strftime') else str(timestamp)
            else:
                time_str = 'N/A'
            
            print(f"  [{i+1}] {data.get('activity', 'N/A')}")
            print(f"      Confidence: {data.get('confidence', 0):.2%}")
            print(f"      User: {data.get('user_id', 'N/A')}")
            print(f"      Time: {time_str}")
            print()
    else:
        print("❌ No predictions found!")
        print("\n   Possible reasons:")
        print("   1. Backend hasn't predicted yet")
        print("   2. Predictions not being saved to Firestore")
        print("   3. Wrong collection name")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n[2] Checking activity_sessions collection...")
try:
    docs = db.collection('activity_sessions').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(5).stream()
    
    sessions = list(docs)
    
    if sessions:
        print(f"✅ Found {len(sessions)} sessions\n")
        
        for i, doc in enumerate(sessions):
            data = doc.to_dict()
            print(f"  [{i+1}] {data.get('activity', 'N/A')}")
            print(f"      Duration: {data.get('duration', 0):.1f}s")
            print(f"      User: {data.get('user_id', 'N/A')}")
            print()
    else:
        print("⚠️ No sessions found (this is normal if activities haven't changed)")
        
except Exception as e:
    print(f"⚠️ Sessions collection may not exist yet")

print("\n[3] Testing write to Firestore...")
try:
    # Test write
    test_ref = db.collection('activity_predictions').document()
    test_ref.set({
        'user_id': 'user1',
        'activity': 'TEST',
        'confidence': 1.0,
        'probabilities': {'TEST': 1.0},
        'timestamp': firestore.SERVER_TIMESTAMP,
        'created_at': datetime.now().isoformat()
    })
    
    print("✅ Write successful!")
    print("   Created test document in Firestore")
    
    # Clean up
    test_ref.delete()
    print("✅ Test document deleted")
    
except Exception as e:
    print(f"❌ Write failed: {e}")

print("\n" + "=" * 60)
print("  DIAGNOSIS COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. If no predictions found:")
print("   → Run: python test_realtime_db.py")
print("   → Choose option 2 to predict")
print()
print("2. If Flutter still shows 'waiting':")
print("   → Check Firebase Console")
print("   → Verify collection name is 'activity_predictions'")
print("   → Check Firestore rules allow read")
print()
