"""
Script to check if there's data in Firestore activity_predictions collection
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from firebase_admin import credentials, firestore, initialize_app

# Load environment variables
load_dotenv()

# Initialize Firebase
service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccountKey.json")
cred = credentials.Certificate(service_account_path)
initialize_app(cred)

# Get Firestore client
db = firestore.client()

print("=" * 80)
print("🔍 CHECKING FIRESTORE DATA")
print("=" * 80)

# Query activity_predictions collection
collection_ref = db.collection('activity_predictions')

# Get all documents
docs = collection_ref.limit(10).stream()

doc_list = list(docs)

if not doc_list:
    print("❌ NO DATA FOUND in 'activity_predictions' collection")
    print("\n📋 Possible reasons:")
    print("   1. Backend is not running")
    print("   2. Firebase stream is not started")
    print("   3. No sensor data received from ESP32")
    print("   4. Predictions not being saved to Firestore")
    print("\n💡 Solution:")
    print("   1. Start backend: python main.py")
    print("   2. Start stream: python start_stream.py")
    print("   3. Check ESP32 is sending data")
else:
    print(f"✅ FOUND {len(doc_list)} DOCUMENTS\n")
    
    for i, doc in enumerate(doc_list, 1):
        data = doc.to_dict()
        print(f"📄 Document {i} (ID: {doc.id}):")
        print(f"   Activity: {data.get('activity', 'N/A')}")
        print(f"   Confidence: {data.get('confidence', 0):.2%}")
        print(f"   User ID: {data.get('user_id', 'N/A')}")
        print(f"   Created at: {data.get('created_at', 'N/A')}")
        
        # Check for new time fields
        if 'start_time' in data:
            print(f"   ✅ Start time: {data['start_time']}")
        else:
            print(f"   ⚠️  Start time: NOT FOUND")
            
        if 'end_time' in data:
            print(f"   ✅ End time: {data['end_time']}")
        else:
            print(f"   ⚠️  End time: NOT FOUND")
            
        if 'duration_seconds' in data:
            print(f"   ✅ Duration: {data['duration_seconds']}s")
        else:
            print(f"   ⚠️  Duration: NOT FOUND")
        
        print()

print("=" * 80)

# Query for today's data
print("\n📅 CHECKING TODAY'S DATA:")
today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
print(f"   Date: {today_start.strftime('%Y-%m-%d')}")

# Count documents for user1
user_docs = collection_ref.where('user_id', '==', 'user1').stream()
user_count = len(list(user_docs))
print(f"   Documents for user_id='user1': {user_count}")

if user_count == 0:
    print("\n❌ NO DATA for user_id='user1' found!")
    print("   Flutter app is looking for user_id='user1'")
    print("   Check if backend is saving with correct user_id")
else:
    print(f"\n✅ Found {user_count} predictions for user_id='user1'")

print("=" * 80)
