from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import numpy as np
import pandas as pd
from datetime import datetime
import logging
import uvicorn
import os
from dotenv import load_dotenv

from predictor import ActivityPredictor
from firebase_handler import FirebaseHandler
from data_buffer import DataBuffer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Human Activity Recognition API",
    description="Real-time activity prediction from ESP32 sensor data via Firebase",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
predictor: Optional[ActivityPredictor] = None
firebase_handler: Optional[FirebaseHandler] = None
data_buffer: DataBuffer = DataBuffer(window_size=40, overlap=0.5)
stream_active: bool = False  # Track if streaming is active
prediction_count: int = 0  # Track number of predictions made

# ==================== Pydantic Models ====================

class SensorData(BaseModel):
    """Single sensor reading from ESP32"""
    ax_g: float = Field(..., description="Accelerometer X (g)")
    ay_g: float = Field(..., description="Accelerometer Y (g)")
    az_g: float = Field(..., description="Accelerometer Z (g)")
    gx_dps: float = Field(..., description="Gyroscope X (deg/s)")
    gy_dps: float = Field(..., description="Gyroscope Y (deg/s)")
    gz_dps: float = Field(..., description="Gyroscope Z (deg/s)")
    amag_g: float = Field(..., description="Accelerometer magnitude (g)")
    pitch_kf: float = Field(..., description="Kalman filtered pitch (deg)")
    roll_kf: float = Field(..., description="Kalman filtered roll (deg)")
    timestamp: Optional[int] = Field(None, description="Timestamp in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "ax_g": 0.05,
                "ay_g": 0.98,
                "az_g": 0.15,
                "gx_dps": 1.2,
                "gy_dps": -0.5,
                "gz_dps": 0.3,
                "amag_g": 1.01,
                "pitch_kf": 5.2,
                "roll_kf": 2.8,
                "timestamp": 1699876543210
            }
        }


class BatchSensorData(BaseModel):
    """Batch of sensor readings"""
    data: List[SensorData]
    device_id: Optional[str] = Field(None, description="ESP32 device identifier")


class PredictionResponse(BaseModel):
    """Prediction result"""
    activity: str
    confidence: float
    probabilities: Dict[str, float]
    timestamp: str
    samples_used: int
    device_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    firebase_connected: bool
    timestamp: str
    model_info: Optional[Dict] = None


class FirebaseConfig(BaseModel):
    """Firebase configuration"""
    database_url: str
    service_account_path: Optional[str] = None
    credentials_dict: Optional[Dict] = None
    realtime_db_path: Optional[str] = Field(default="/sensor_data", description="Path to listen in Realtime DB")
    firestore_collection: Optional[str] = Field(default="activity_predictions", description="Firestore collection name")
    user_id: Optional[str] = Field(default="user1", description="User ID for predictions")


# ==================== Startup & Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Initialize model and Firebase connection on startup"""
    global predictor, firebase_handler
    
    logger.info("🚀 Starting Human Activity Recognition API...")
    
    # Load predictor WITH model artifacts (scalers + metadata)
    try:
        predictor = ActivityPredictor(
            model_path="../AI/final_model_test_BINH_PHONG.h5",
            artifacts_path="../AI/model_artifacts"  # Use full artifacts package!
        )
        logger.info("✅ Activity Predictor loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load predictor: {e}")
        predictor = None
    
    # Initialize Firebase connection from .env config
    try:
        database_url = os.getenv("FIREBASE_DATABASE_URL")
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        
        if database_url and service_account_path:
            logger.info("📡 Initializing Firebase from .env config...")
            logger.info(f"   Database URL: {database_url}")
            logger.info(f"   Service Account: {service_account_path}")
            
            firebase_handler = FirebaseHandler(
                database_url=database_url,
                service_account_path=service_account_path,
                use_firestore=True
            )
            logger.info("✅ Firebase initialized successfully")
        else:
            logger.warning("⚠️ Firebase config not found in .env - Firebase will be initialized on first request")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase: {e}")
        firebase_handler = None
    
    logger.info("✅ API is ready to accept requests")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global firebase_handler
    
    logger.info("🛑 Shutting down API...")
    
    if firebase_handler:
        firebase_handler.disconnect()
        logger.info(" Firebase disconnected")
    
    logger.info(" Goodbye!")


# ==================== API Endpoints ====================

@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "message": "Human Activity Recognition API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "predict_single": "/predict/single",
            "predict_batch": "/predict/batch",
            "firebase_start": "/firebase/start",
            "firebase_stop": "/firebase/stop"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint"""
    firebase_connected = firebase_handler is not None and firebase_handler.is_connected()
    
    model_info = None
    if predictor:
        model_info = {
            "activities": predictor.activity_names,
            "window_size": predictor.window_size,
            "n_features": predictor.n_features
        }
    
    return HealthResponse(
        status="healthy" if predictor else "degraded",
        model_loaded=predictor is not None,
        firebase_connected=firebase_connected,
        timestamp=datetime.now().isoformat(),
        model_info=model_info
    )


@app.post("/predict/single", response_model=PredictionResponse, tags=["Prediction"])
async def predict_single(sensor_data: SensorData):
    """
    Predict activity from a single sensor reading.
    Note: Requires buffering to reach window_size samples.
    """
    if not predictor:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Add data to buffer
        data_buffer.add_sample({
            'ax_g': sensor_data.ax_g,
            'ay_g': sensor_data.ay_g,
            'az_g': sensor_data.az_g,
            'gx_dps': sensor_data.gx_dps,
            'gy_dps': sensor_data.gy_dps,
            'gz_dps': sensor_data.gz_dps,
            'amag_g': sensor_data.amag_g,
            'pitch_kf': sensor_data.pitch_kf,
            'roll_kf': sensor_data.roll_kf,
            'timestamp': sensor_data.timestamp or int(datetime.now().timestamp() * 1000)
        })
        
        # Check if we have enough data for prediction
        if data_buffer.can_predict():
            window = data_buffer.get_window()
            
            # Predict
            activity, confidence, probabilities = predictor.predict_window(window)
            
            return PredictionResponse(
                activity=activity,
                confidence=confidence,
                probabilities=probabilities,
                timestamp=datetime.now().isoformat(),
                samples_used=len(window)
            )
        else:
            # Not enough data yet
            raise HTTPException(
                status_code=202,
                detail=f"Buffering data... {data_buffer.get_buffer_size()}/{predictor.window_size} samples collected"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/batch", response_model=PredictionResponse, tags=["Prediction"])
async def predict_batch(batch: BatchSensorData):
    """
    Predict activity from a batch of sensor readings.
    This is more efficient than single predictions.
    """
    if not predictor:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if len(batch.data) < predictor.window_size:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data. Need at least {predictor.window_size} samples, got {len(batch.data)}"
        )
    
    try:
        # Convert batch to DataFrame
        sensor_list = []
        for reading in batch.data:
            sensor_list.append({
                'ax_g': reading.ax_g,
                'ay_g': reading.ay_g,
                'az_g': reading.az_g,
                'gx_dps': reading.gx_dps,
                'gy_dps': reading.gy_dps,
                'gz_dps': reading.gz_dps,
                'amag_g': reading.amag_g,
                'pitch_kf': reading.pitch_kf,
                'roll_kf': reading.roll_kf,
                'timestamp': reading.timestamp or int(datetime.now().timestamp() * 1000)
            })
        
        df = pd.DataFrame(sensor_list)
        
        # Predict
        activity, confidence, probabilities = predictor.predict_from_dataframe(df)
        
        return PredictionResponse(
            activity=activity,
            confidence=confidence,
            probabilities=probabilities,
            timestamp=datetime.now().isoformat(),
            samples_used=len(batch.data),
            device_id=batch.device_id
        )
    
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/firebase/start", tags=["Firebase"])
async def start_firebase_listener(config: FirebaseConfig, background_tasks: BackgroundTasks):
    """
    Start listening to Firebase Realtime Database for real-time sensor data from ESP32.
    Predictions will be automatically saved to Firestore.
    """
    global firebase_handler, stream_active
    
    if stream_active:
        return {
            "status": "already_running",
            "message": "Firebase listener is already active"
        }
    
    try:
        # Check if Firebase handler already exists (initialized at startup)
        if not firebase_handler:
            logger.info("📡 Initializing Firebase handler (not initialized at startup)...")
            # Initialize Firebase handler with Firestore support
            firebase_handler = FirebaseHandler(
                database_url=config.database_url,
                service_account_path=config.service_account_path,
                credentials_dict=config.credentials_dict,
                use_firestore=True  # Enable Firestore
            )
        else:
            logger.info("📡 Using existing Firebase handler from startup")
        
        # Store config for use in callback
        firebase_handler.user_id = config.user_id
        firebase_handler.firestore_collection = config.firestore_collection
        
        # Start listening in background
        firebase_handler.start_listening(
            callback=lambda data: handle_firebase_data(data, config),
            path=config.realtime_db_path
        )
        
        stream_active = True
        logger.info(f"🔥 Firebase listener started on path: {config.realtime_db_path}")
        logger.info(f"📊 Predictions will be saved to Firestore collection: {config.firestore_collection}")
        
        return {
            "status": "started",
            "message": "Firebase listener started successfully",
            "realtime_db_path": config.realtime_db_path,
            "firestore_collection": config.firestore_collection,
            "user_id": config.user_id,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to start Firebase listener: {e}")
        stream_active = False
        raise HTTPException(status_code=500, detail=f"Firebase connection failed: {str(e)}")


@app.post("/firebase/stop", tags=["Firebase"])
async def stop_firebase_listener():
    """Stop listening to Firebase"""
    global stream_active, prediction_count
    
    if not firebase_handler:
        raise HTTPException(status_code=400, detail="Firebase not initialized")
    
    if not stream_active:
        return {
            "status": "not_running",
            "message": "Firebase listener is not active"
        }
    
    try:
        firebase_handler.stop_listening()
        
        total_predictions = prediction_count
        stream_active = False
        prediction_count = 0
        
        logger.info("🛑 Firebase listener stopped")
        
        return {
            "status": "stopped",
            "message": "Firebase listener stopped successfully (Firebase connection kept alive)",
            "total_predictions": total_predictions,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to stop Firebase listener: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop listener: {str(e)}")


@app.get("/buffer/status", tags=["Buffer"])
async def get_buffer_status():
    """Get current buffer status"""
    return {
        "buffer_size": data_buffer.get_buffer_size(),
        "window_size": data_buffer.window_size,
        "can_predict": data_buffer.can_predict(),
        "stream_active": stream_active,
        "predictions_made": prediction_count,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/buffer/clear", tags=["Buffer"])
async def clear_buffer():
    """Clear the data buffer"""
    data_buffer.clear()
    return {
        "status": "cleared",
        "message": "Data buffer cleared successfully",
        "timestamp": datetime.now().isoformat()
    }


# ==================== Firestore Endpoints ====================

@app.get("/firestore/predictions", tags=["Firestore"])
async def get_predictions(user_id: str = "user1", limit: int = 10):
    """Get recent predictions from Firestore"""
    if not firebase_handler:
        raise HTTPException(status_code=400, detail="Firebase not connected")
    
    try:
        predictions = firebase_handler.get_predictions_from_firestore(
            user_id=user_id,
            limit=limit
        )
        return {
            "status": "success",
            "count": len(predictions),
            "predictions": predictions,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get predictions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get predictions: {str(e)}")


@app.get("/firestore/predictions/{doc_id}", tags=["Firestore"])
async def get_prediction_by_id(doc_id: str):
    """Get a specific prediction by document ID"""
    if not firebase_handler:
        raise HTTPException(status_code=400, detail="Firebase not connected")
    
    try:
        firestore_client = firebase_handler.get_firestore_client()
        doc = firestore_client.collection("activity_predictions").document(doc_id).get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Prediction not found")
        
        pred_data = doc.to_dict()
        pred_data['id'] = doc.id
        
        return {
            "status": "success",
            "prediction": pred_data,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get prediction: {str(e)}")


@app.delete("/firestore/predictions/{doc_id}", tags=["Firestore"])
async def delete_prediction(doc_id: str):
    """Delete a prediction from Firestore"""
    if not firebase_handler:
        raise HTTPException(status_code=400, detail="Firebase not connected")
    
    try:
        firebase_handler.delete_prediction_from_firestore(doc_id)
        return {
            "status": "deleted",
            "message": f"Prediction {doc_id} deleted successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to delete prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete prediction: {str(e)}")


@app.get("/stream/status", tags=["Firebase"])
async def get_stream_status():
    """Get current streaming status"""
    return {
        "stream_active": stream_active,
        "firebase_connected": firebase_handler is not None and firebase_handler.is_connected(),
        "model_loaded": predictor is not None,
        "predictions_made": prediction_count,
        "buffer_size": data_buffer.get_buffer_size(),
        "can_predict": data_buffer.can_predict(),
        "timestamp": datetime.now().isoformat()
    }


# ==================== Helper Functions ====================

def handle_firebase_data(data: dict, config: FirebaseConfig = None):
    """
    Callback function to handle incoming data from Firebase Realtime Database.
    This processes data, makes predictions, and saves to Firestore.
    """
    global prediction_count
    
    try:
        # ====== IN RA DỮ LIỆU NHẬN ĐƯỢC TỪ FIREBASE ======
        logger.info("="*80)
        logger.info("📥 DỮ LIỆU NHẬN ĐƯỢC TỪ FIREBASE:")
        logger.info(f"   Kiểu dữ liệu: {type(data)}")
        logger.info(f"   Số lượng mẫu: {len(data) if isinstance(data, dict) else 1}")
        
        # Handle different data structures
        # Case 1: Single sensor reading
        if 'ax_g' in data:
            logger.info("   📊 Dữ liệu cảm biến đơn:")
            logger.info(f"      - Accelerometer: ax={data.get('ax_g'):.3f}, ay={data.get('ay_g'):.3f}, az={data.get('az_g'):.3f}")
            logger.info(f"      - Gyroscope: gx={data.get('gx_dps'):.3f}, gy={data.get('gy_dps'):.3f}, gz={data.get('gz_dps'):.3f}")
            logger.info(f"      - Magnitude: {data.get('amag_g'):.3f}")
            logger.info(f"      - Pitch: {data.get('pitch_kf'):.2f}°, Roll: {data.get('roll_kf'):.2f}°")
            
            sensor_data = SensorData(**data)
            data_buffer.add_sample(data)
        
        # Case 2: Nested structure (e.g., /sensor_data/sample_0)
        elif isinstance(data, dict):
            logger.info("   📦 Dữ liệu cảm biến lồng nhau:")
            # Extract sensor readings from nested structure
            sample_count = 0
            for key, value in data.items():
                if isinstance(value, dict) and 'ax_g' in value:
                    try:
                        sensor_data = SensorData(**value)
                        data_buffer.add_sample(value)
                        sample_count += 1
                        
                        # In ra mẫu đầu tiên và cuối cùng
                        if sample_count == 1:
                            logger.info(f"      📍 Mẫu đầu tiên ({key}):")
                            logger.info(f"         Accel: [{value.get('ax_g'):.3f}, {value.get('ay_g'):.3f}, {value.get('az_g'):.3f}]")
                            logger.info(f"         Gyro: [{value.get('gx_dps'):.3f}, {value.get('gy_dps'):.3f}, {value.get('gz_dps'):.3f}]")
                        elif sample_count == len([k for k, v in data.items() if isinstance(v, dict) and 'ax_g' in v]):
                            logger.info(f"      📍 Mẫu cuối cùng ({key}):")
                            logger.info(f"         Accel: [{value.get('ax_g'):.3f}, {value.get('ay_g'):.3f}, {value.get('az_g'):.3f}]")
                            logger.info(f"         Gyro: [{value.get('gx_dps'):.3f}, {value.get('gy_dps'):.3f}, {value.get('gz_dps'):.3f}]")
                        
                    except Exception as e:
                        logger.warning(f"⚠️  Bỏ qua mẫu không hợp lệ {key}: {e}")
            
            logger.info(f"   ✅ Đã thêm {sample_count} mẫu vào buffer")
        
        # Hiển thị trạng thái buffer
        logger.info(f"   📊 Trạng thái Buffer: {data_buffer.get_buffer_size()}/{data_buffer.window_size} mẫu")
        
        # Make prediction if buffer is full
        if data_buffer.can_predict() and predictor:
            logger.info("   🔮 BẮT ĐẦU DỰ ĐOÁN...")
            
            window = data_buffer.get_window()
            logger.info(f"   📐 Kích thước cửa sổ dự đoán: {window.shape}")
            
            # ====== IN RA SAMPLES DÙNG ĐỂ DỰ ĐOÁN ======
            logger.info("   📋 SAMPLES DÙNG ĐỂ DỰ ĐOÁN:")
            logger.info("   " + "-"*76)
            
            # Print header
            header = f"   {'time_ms':<12} {'ax_g':<8} {'ay_g':<8} {'az_g':<8} {'gx_dps':<8} {'gy_dps':<8} {'gz_dps':<8} {'amag_g':<8} {'pitch_kf':<9} {'roll_kf':<9}"
            logger.info(header)
            logger.info("   " + "-"*76)
            
            # Get timestamps from buffer (need to access internal buffer)
            # Window format: [ax, ay, az, gx, gy, gz, amag, pitch, roll, ax_deriv, ay_deriv]
            # We'll print first 5, middle, and last 5 samples
            total_samples = len(window)
            
            # Get buffer data with timestamps
            buffer_data = list(data_buffer.buffer)  # Access the internal deque
            
            # Print first 5 samples
            for i in range(min(5, total_samples)):
                sample = buffer_data[i] if i < len(buffer_data) else {}
                time_ms = sample.get('timestamp', 0)
                row = f"   {time_ms:<12} {window[i,0]:<8.4f} {window[i,1]:<8.4f} {window[i,2]:<8.4f} {window[i,3]:<8.4f} {window[i,4]:<8.4f} {window[i,5]:<8.4f} {window[i,6]:<8.4f} {window[i,7]:<9.4f} {window[i,8]:<9.4f}"
                logger.info(row)
            
            # Print middle sample if window > 10
            if total_samples > 10:
                logger.info("   " + "."*76)
                mid = total_samples // 2
                sample = buffer_data[mid] if mid < len(buffer_data) else {}
                time_ms = sample.get('timestamp', 0)
                row = f"   {time_ms:<12} {window[mid,0]:<8.4f} {window[mid,1]:<8.4f} {window[mid,2]:<8.4f} {window[mid,3]:<8.4f} {window[mid,4]:<8.4f} {window[mid,5]:<8.4f} {window[mid,6]:<8.4f} {window[mid,7]:<9.4f} {window[mid,8]:<9.4f}"
                logger.info(row)
                logger.info("   " + "."*76)
            
            # Print last 5 samples
            start_idx = max(5, total_samples - 5)
            for i in range(start_idx, total_samples):
                sample = buffer_data[i] if i < len(buffer_data) else {}
                time_ms = sample.get('timestamp', 0)
                row = f"   {time_ms:<12} {window[i,0]:<8.4f} {window[i,1]:<8.4f} {window[i,2]:<8.4f} {window[i,3]:<8.4f} {window[i,4]:<8.4f} {window[i,5]:<8.4f} {window[i,6]:<8.4f} {window[i,7]:<9.4f} {window[i,8]:<9.4f}"
                logger.info(row)
            
            logger.info("   " + "-"*76)
            logger.info(f"   📊 Tổng số samples: {total_samples}")
            logger.info(f"   📈 Giá trị trung bình:")
            logger.info(f"      - Accelerometer: [{window[:, 0].mean():.4f}, {window[:, 1].mean():.4f}, {window[:, 2].mean():.4f}]")
            logger.info(f"      - Gyroscope: [{window[:, 3].mean():.4f}, {window[:, 4].mean():.4f}, {window[:, 5].mean():.4f}]")
            logger.info("   " + "-"*76)
            
            activity, confidence, probabilities = predictor.predict_window(window)
            
            # ====== IN RA KẾT QUẢ DỰ ĐOÁN ======
            logger.info("   " + "="*76)
            logger.info("   🎯 KẾT QUẢ DỰ ĐOÁN:")
            logger.info(f"   🏃 Hoạt động: {activity}")
            logger.info(f"   📊 Độ tin cậy: {confidence:.2%}")
            logger.info("   📈 Xác suất các hoạt động:")
            
            # Sort probabilities by value for better display
            sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
            for act, prob in sorted_probs:
                bar_length = int(prob * 40)
                bar = "█" * bar_length + "░" * (40 - bar_length)
                logger.info(f"      {act:12s} {prob:6.2%} |{bar}|")
            
            logger.info("   " + "="*76)
            
            # Save prediction to Firestore
            if firebase_handler:
                try:
                    user_id = config.user_id if config else "user1"
                    collection = config.firestore_collection if config else "activity_predictions"
                    
                    logger.info(f"   💾 Đang lưu dự đoán vào Firestore...")
                    logger.info(f"      - User ID: {user_id}")
                    logger.info(f"      - Collection: {collection}")
                    
                    doc_id = firebase_handler.save_prediction_to_firestore(
                        activity=activity,
                        confidence=float(confidence),
                        probabilities=probabilities,
                        user_id=user_id,
                        collection=collection
                    )
                    
                    prediction_count += 1
                    logger.info(f"   ✅ Lưu thành công! (Doc ID: {doc_id})")
                    logger.info(f"   📊 Tổng số dự đoán: {prediction_count}")
                    
                except Exception as e:
                    logger.error(f"   ❌ Lỗi khi lưu vào Firestore: {e}")
            
            logger.info("="*80)
            logger.info("")  # Blank line for readability
            
            # Optional: Also send to Realtime Database for real-time updates
            # firebase_handler.send_prediction(activity, confidence, probabilities)
    
    except Exception as e:
        logger.error(f"❌ Error handling Firebase data: {e}", exc_info=True)


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
