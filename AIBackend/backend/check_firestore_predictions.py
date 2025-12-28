"""
Check Firestore predictions to verify data is being saved
"""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

def check_firestore():
    print("="*80)
    print("🔍 Checking Firestore Predictions")
    print("="*80)
    print()
    
    try:
        # Initialize Firebase
        cred = credentials.Certificate('serviceAccountKey.json')
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        
        # Get latest predictions
        print("📊 Fetching latest predictions from Firestore...")
        docs = (db.collection('activity_predictions')
               .where('user_id', '==', 'user1')
               .order_by('created_at', direction=firestore.Query.DESCENDING)
               .limit(5)
               .stream())
        
        predictions = []
        for doc in docs:
            data = doc.to_dict()
            predictions.append({
                'id': doc.id,
                'activity': data.get('activity'),
                'confidence': data.get('confidence'),
                'created_at': data.get('created_at'),
                'timestamp': data.get('timestamp')
            })
        
        if predictions:
            print(f"✅ Found {len(predictions)} predictions:")
            print()
            for i, pred in enumerate(predictions, 1):
                print(f"{i}. Activity: {pred['activity']}")
                print(f"   Confidence: {pred['confidence']:.2%}")
                print(f"   Created: {pred['created_at']}")
                print(f"   Doc ID: {pred['id']}")
                print()
        else:
            print("⚠️  No predictions found in Firestore!")
            print()
            print("Possible issues:")
            print("  1. Backend hasn't made any predictions yet")
            print("  2. Firebase stream hasn't been started")
            print("  3. No sensor data in Firebase Realtime DB")
            print()
            print("To fix:")
            print("  1. Make sure backend is running: uvicorn main:app --reload")
            print("  2. Start Firebase stream: python start_stream.py")
            print("  3. Check if sensor data exists in Realtime DB")
        
        print("="*80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if firebase_admin._apps:
            firebase_admin.delete_app(firebase_admin.get_app())

if __name__ == "__main__":
    check_firestore()
