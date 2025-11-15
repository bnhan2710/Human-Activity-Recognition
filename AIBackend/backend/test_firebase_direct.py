"""
Test Firebase Realtime Database connection directly
"""
import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv

load_dotenv()

def test_firebase():
    print("="*80)
    print("Testing Firebase Realtime Database Connection")
    print("="*80)
    
    # Get config from .env
    database_url = os.getenv("FIREBASE_DATABASE_URL")
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    
    print(f"Database URL: {database_url}")
    print(f"Service Account: {service_account_path}")
    print()
    
    # Check if service account file exists
    if not os.path.exists(service_account_path):
        print(f"❌ Service account file not found: {service_account_path}")
        return
    
    print(f"✅ Service account file exists")
    print()
    
    try:
        # Initialize Firebase
        print("Initializing Firebase Admin SDK...")
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
        print("✅ Firebase initialized")
        print()
        
        # Test read from /sensor_data
        print("Testing read from /sensor_data...")
        ref = db.reference('/sensor_data')
        
        try:
            data = ref.get()
            print(f"✅ Successfully read from Firebase!")
            print(f"   Data exists: {data is not None}")
            if data:
                print(f"   Data type: {type(data)}")
                if isinstance(data, dict):
                    print(f"   Number of keys: {len(data)}")
                    print(f"   First few keys: {list(data.keys())[:5]}")
            else:
                print(f"   ⚠️  No data at /sensor_data (database is empty)")
        except Exception as read_err:
            print(f"❌ Failed to read from Firebase:")
            print(f"   Error: {read_err}")
            print(f"   Error type: {type(read_err).__name__}")
            
            # Check Firebase rules
            print()
            print("Possible causes:")
            print("  1. Firebase Realtime Database rules are too restrictive")
            print("  2. Service account doesn't have read permission")
            print("  3. Database URL is incorrect")
            print()
            print("To fix:")
            print("  1. Go to Firebase Console > Realtime Database > Rules")
            print("  2. Temporarily set rules to:")
            print('     {')
            print('       "rules": {')
            print('         ".read": true,')
            print('         ".write": true')
            print('       }')
            print('     }')
            print("  3. Or add service account to Firebase project with admin access")
            
        print()
        
        # Test write
        print("Testing write to /test_connection...")
        test_ref = db.reference('/test_connection')
        try:
            test_ref.set({
                'timestamp': firebase_admin.db.ServerValue.TIMESTAMP,
                'message': 'Connection test successful'
            })
            print("✅ Successfully wrote to Firebase!")
        except Exception as write_err:
            print(f"❌ Failed to write to Firebase:")
            print(f"   Error: {write_err}")
        
        print()
        print("="*80)
        
    except Exception as e:
        print(f"❌ Failed to initialize Firebase:")
        print(f"   Error: {e}")
        print(f"   Error type: {type(e).__name__}")
        
    finally:
        # Cleanup
        if firebase_admin._apps:
            firebase_admin.delete_app(firebase_admin.get_app())
            print("🧹 Firebase app deleted")

if __name__ == "__main__":
    test_firebase()
