from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.background import BackgroundTasks
import tensorflow as tf
import os
import sys

print("🔄 Loading AI model...")

model = None
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.path.join(BASE_DIR, "AI", "final_model_test_BINH_PHONG.h5")

    if not os.path.exists(MODEL_PATH):
        print(f"⚠️ Model not found at: {MODEL_PATH}")
        print("   Running without model")
    else:
        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        print("✅ Model loaded successfully")
        print("   Input:", model.input_shape)
        print("   Output:", model.output_shape)

except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None

# ==================== PREPROCESSOR ====================
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import tensorflow as tf
from typing import List, Dict
import firebase_admin
from firebase_admin import credentials, db, firestore
from datetime import datetime
import threading
import time
import sys
import os

# Add AI src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'AI', 'src'))
from preprocessing import Preprocessor

app = FastAPI(title="PBL4 HAR API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== FIREBASE SETUP ====================
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://imu-detection-app-default-rtdb.asia-southeast1.firebasedatabase.app/'  # Thay bằng URL của bạn
    })
    realtime_db = db.reference()
    firestore_db = firestore.client()
    FIREBASE_ENABLED = True
    print("✅ Firebase initialized successfully")
except Exception as e:
    print(f"⚠️ Firebase not initialized: {e}")
    print("   Running in TEST MODE without Firebase")
    realtime_db = None
    firestore_db = None
    FIREBASE_ENABLED = False

# ==================== LOAD MODEL ====================


# ==================== PREPROCESSOR ====================
preprocessor = Preprocessor()

# Activity labels
ACTIVITIES = ['WALKING', 'UPSTAIRS', 'DOWNSTAIRS', 'SITTING', 'STANDING', 'RUNNING']

# ==================== DATA MODELS ====================
class SensorData(BaseModel):
    ax_g: float
    ay_g: float
    az_g: float
    gx_dps: float
    gy_dps: float
    gz_dps: float
    amag_g: float
    pitch_kf: float
    roll_kf: float
    timestamp: int

class PredictionResult(BaseModel):
    activity: str
    confidence: float
    timestamp: str
    sensor_data: Dict

# ==================== BUFFER FOR SLIDING WINDOW ====================
class DataBuffer:
    def __init__(self, window_size=40):
        self.window_size = window_size
        self.buffer = []
        self.last_prediction = None
        self.lock = threading.Lock()
        
    def add_data(self, data: Dict):
        with self.lock:
            self.buffer.append(data)
            if len(self.buffer) > self.window_size:
                self.buffer.pop(0)
    
    def get_window(self):
        with self.lock:
            if len(self.buffer) >= self.window_size:
                return self.buffer[-self.window_size:]
            return None
    
    def clear(self):
        with self.lock:
            self.buffer.clear()

data_buffer = DataBuffer(window_size=40)

# ==================== PREPROCESSING ====================
def preprocess_window(window_data: List[Dict]) -> np.ndarray:
    """
    Tiền xử lý window data thành format model mong đợi
    """
    # Extract features từ window
    features = []
    for data in window_data:
        feature_vector = [
            data['ax_g'], data['ay_g'], data['az_g'],
            data['gx_dps'], data['gy_dps'], data['gz_dps'],
            data['amag_g'], data['pitch_kf'], data['roll_kf']
        ]
        features.append(feature_vector)
    
    # Convert to numpy array
    X = np.array(features)  # Shape: (40, 9)
    
    # Tính đạo hàm pitch và roll
    d_pitch = np.diff(X[:, 7], prepend=X[0, 7])
    d_roll = np.diff(X[:, 8], prepend=X[0, 8])
    
    # Thêm derivatives
    X_with_deriv = np.concatenate([
        X,
        d_pitch.reshape(-1, 1),
        d_roll.reshape(-1, 1)
    ], axis=1)  # Shape: (40, 11)
    
    # Reshape for model input: (1, 40, 11)
    X_batch = X_with_deriv.reshape(1, 40, 11)
    
    return X_batch

# ==================== PREDICTION ====================
def predict_activity(window_data: List[Dict]) -> Dict:
    """
    Dự đoán activity từ window data
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Preprocess
    X = preprocess_window(window_data)
    
    # Predict
    predictions = model.predict(X, verbose=0)
    predicted_class = np.argmax(predictions[0])
    confidence = float(predictions[0][predicted_class])
    
    activity = ACTIVITIES[predicted_class]
    
    return {
        'activity': activity,
        'confidence': confidence,
        'probabilities': {
            ACTIVITIES[i]: float(predictions[0][i]) 
            for i in range(len(ACTIVITIES))
        }
    }

# ==================== SAVE TO FIRESTORE ====================
def save_prediction_to_firestore(prediction: Dict, user_id: str = "user1"):
    """
    Lưu kết quả dự đoán vào Firestore
    """
    if not FIREBASE_ENABLED or firestore_db is None:
        print(f"⚠️ Firebase disabled, skipping save: {prediction['activity']} ({prediction['confidence']:.2%})")
        return
    
    try:
        doc_ref = firestore_db.collection('activity_predictions').document()
        doc_ref.set({
            'user_id': user_id,
            'activity': prediction['activity'],
            'confidence': prediction['confidence'],
            'probabilities': prediction['probabilities'],
            'timestamp': firestore.SERVER_TIMESTAMP,
            'created_at': datetime.now().isoformat()
        })
        print(f"✅ Saved to Firestore: {prediction['activity']} ({prediction['confidence']:.2%})")
    except Exception as e:
        print(f"❌ Error saving to Firestore: {e}")

# ==================== FIREBASE REALTIME DB LISTENER ====================
def listen_to_realtime_db():
    """
    Lắng nghe dữ liệu mới từ Firebase Realtime Database
    """
    if not FIREBASE_ENABLED or realtime_db is None:
        print("⚠️ Firebase disabled, Realtime DB listener not started")
        return
    
    print("👂 Starting Firebase Realtime Database listener...")
    
    def on_data_change(event):
        if event.data is None:
            return
        
        try:
            # Parse sensor data
            data = event.data
            
            # Validate data
            required_keys = ['ax_g', 'ay_g', 'az_g', 'gx_dps', 'gy_dps', 'gz_dps', 
                           'amag_g', 'pitch_kf', 'roll_kf']
            
            if not all(key in data for key in required_keys):
                return
            
            # Add to buffer
            data_buffer.add_data(data)
            
            # Get window
            window = data_buffer.get_window()
            
            if window is not None:
                # Predict
                prediction = predict_activity(window)
                
                # Save to Firestore
                save_prediction_to_firestore(prediction)
                
                # Update buffer last prediction
                data_buffer.last_prediction = prediction
                
                print(f"🎯 Prediction: {prediction['activity']} ({prediction['confidence']:.2%})")
        
        except Exception as e:
            print(f"❌ Error processing data: {e}")
    
    # Listen to sensor_data node
    sensor_ref = realtime_db.child('sensor_data')
    sensor_ref.listen(on_data_change)

# ==================== API ENDPOINTS ====================

@app.on_event("startup")
async def startup_event():
    """
    Start background listener when API starts
    """
    threading.Thread(target=listen_to_realtime_db, daemon=True).start()

@app.get("/")
async def root():
    return {
        "message": "PBL4 HAR API",
        "status": "running",
        "model_loaded": model is not None
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model": "loaded" if model is not None else "not loaded",
        "firebase": "enabled" if FIREBASE_ENABLED else "disabled",
        "buffer_size": len(data_buffer.buffer),
        "last_prediction": data_buffer.last_prediction
    }

@app.post("/predict")
async def manual_predict(sensor_data: List[SensorData], background_tasks: BackgroundTasks):
    """
    Manual prediction endpoint (for testing)
    """
    if len(sensor_data) < 40:
        raise HTTPException(
            status_code=400, 
            detail=f"Need at least 40 samples, got {len(sensor_data)}"
        )
    
    # Convert to dict
    window_data = [data.dict() for data in sensor_data[-40:]]
    
    # Predict
    prediction = predict_activity(window_data)
    
    # Save to Firestore in background
    if FIREBASE_ENABLED:
        background_tasks.add_task(save_prediction_to_firestore, prediction)
    
    return prediction

@app.post("/sensor_data")
async def receive_sensor_data(data: SensorData, background_tasks: BackgroundTasks):
    """
    Receive sensor data from ESP32 (alternative to Realtime DB)
    """
    # Add to buffer
    data_buffer.add_data(data.dict())
    
    # Get window
    window = data_buffer.get_window()
    
    if window is not None:
        # Predict in background
        prediction = predict_activity(window)
        background_tasks.add_task(save_prediction_to_firestore, prediction)
        
        return {
            "status": "processed",
            "prediction": prediction
        }
    else:
        return {
            "status": "buffering",
            "buffer_size": len(data_buffer.buffer),
            "need": 40 - len(data_buffer.buffer)
        }

@app.get("/predictions/recent")
async def get_recent_predictions(limit: int = 10):
    """
    Get recent predictions from Firestore
    """
    if not FIREBASE_ENABLED or firestore_db is None:
        raise HTTPException(status_code=503, detail="Firebase not configured")
    
    try:
        docs = firestore_db.collection('activity_predictions')\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .stream()
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            results.append(data)
        
        return {"predictions": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistics/{user_id}")
async def get_user_statistics(user_id: str, days: int = 7):
    """
    Get activity statistics for user
    """
    if not FIREBASE_ENABLED or firestore_db is None:
        raise HTTPException(status_code=503, detail="Firebase not configured")
    
    try:
        # Get predictions from last N days
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        
        docs = firestore_db.collection('activity_predictions')\
            .where('user_id', '==', user_id)\
            .where('timestamp', '>=', start_date)\
            .stream()
        
        activity_counts = {}
        total = 0
        
        for doc in docs:
            data = doc.to_dict()
            activity = data.get('activity')
            if activity:
                activity_counts[activity] = activity_counts.get(activity, 0) + 1
                total += 1
        
        # Calculate percentages
        statistics = {
            activity: {
                'count': count,
                'percentage': (count / total * 100) if total > 0 else 0
            }
            for activity, count in activity_counts.items()
        }
        
        return {
            'user_id': user_id,
            'days': days,
            'total_predictions': total,
            'statistics': statistics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/buffer/clear")
async def clear_buffer():
    """
    Clear data buffer
    """
    data_buffer.clear()
    return {"status": "buffer cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
