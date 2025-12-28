"""
Quick script to check saved predictions in Firestore
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def get_all_predictions():
    """Get all saved predictions"""
    print("\n" + "="*80)
    print("📊 Checking Saved Predictions in Firestore")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/firestore/predictions?user_id=user1&limit=20")
        data = response.json()
        
        if data.get('status') == 'success':
            count = data['count']
            print(f"\n✅ Found {count} predictions in Firestore:")
            print("="*80)
            
            for i, pred in enumerate(data.get('predictions', []), 1):
                print(f"\n[{i}] Prediction ID: {pred.get('id', 'N/A')}")
                print(f"    Activity: {pred.get('activity', 'N/A')}")
                print(f"    Confidence: {pred.get('confidence', 0)*100:.2f}%")
                print(f"    Created: {pred.get('created_at', 'N/A')}")
                
                # Show all probabilities
                probs = pred.get('probabilities', {})
                if probs:
                    print(f"    Probabilities:")
                    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
                    for act, prob in sorted_probs:
                        bar = "█" * int(prob * 50)  # Visual bar
                        print(f"      {act:12s}: {prob*100:6.2f}% {bar}")
            
            print("\n" + "="*80)
            print(f"✅ Total: {count} predictions successfully saved!")
            print("="*80)
            
            # Summary statistics
            if count > 0:
                activities = [p.get('activity') for p in data['predictions']]
                activity_counts = {}
                for act in activities:
                    activity_counts[act] = activity_counts.get(act, 0) + 1
                
                print("\n📈 Activity Distribution:")
                for act, count in sorted(activity_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {act:12s}: {count:2d} times")
        else:
            print("❌ Failed to get predictions:")
            print(json.dumps(data, indent=2))
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_all_predictions()
