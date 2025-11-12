from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import numpy as np
import pandas as pd
from datetime import datetime
import logging
import uvicorn

from predictor import ActivityPredictor
from firebase_handler import FirebaseHandler
from data_buffer import DataBuffer

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


# ==================== Startup & Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Initialize model and Firebase connection on startup"""
    global predictor, firebase_handler
    
    logger.info(" Starting Human Activity Recognition API...")
    
    # Load predictor
    try:
        predictor = ActivityPredictor(
            model_path="../AI/final_model_test_PHONG_QUANG.h5"
        )
        logger.info("✅ Activity Predictor loaded successfully")
    except Exception as e:
        logger.error(f" Failed to load predictor: {e}")
        predictor = None
    
    logger.info("API is ready to accept requests")


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
    Start listening to Firebase for real-time sensor data from ESP32.
    """
    global firebase_handler
    
    if firebase_handler and firebase_handler.is_connected():
        return {
            "status": "already_running",
            "message": "Firebase listener is already active"
        }
    
    try:
        firebase_handler = FirebaseHandler(
            database_url=config.database_url,
            service_account_path=config.service_account_path,
            credentials_dict=config.credentials_dict
        )
        
        # Start listening in background
        firebase_handler.start_listening(
            callback=lambda data: handle_firebase_data(data),
            path="/sensor_data"  # Adjust to your Firebase structure
        )
        
        logger.info(" Firebase listener started")
        
        return {
            "status": "started",
            "message": "Firebase listener started successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to start Firebase listener: {e}")
        raise HTTPException(status_code=500, detail=f"Firebase connection failed: {str(e)}")


@app.post("/firebase/stop", tags=["Firebase"])
async def stop_firebase_listener():
    """Stop listening to Firebase"""
    global firebase_handler
    
    if not firebase_handler:
        raise HTTPException(status_code=400, detail="Firebase listener not active")
    
    try:
        firebase_handler.stop_listening()
        firebase_handler.disconnect()
        firebase_handler = None
        
        logger.info(" Firebase listener stopped")
        
        return {
            "status": "stopped",
            "message": "Firebase listener stopped successfully",
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


# ==================== Helper Functions ====================

def handle_firebase_data(data: dict):
    """
    Callback function to handle incoming data from Firebase.
    This processes data and makes predictions.
    """
    try:
        # Convert Firebase data to SensorData format
        sensor_data = SensorData(**data)
        
        # Add to buffer
        data_buffer.add_sample(data)
        
        # Make prediction if buffer is full
        if data_buffer.can_predict() and predictor:
            window = data_buffer.get_window()
            activity, confidence, probabilities = predictor.predict_window(window)
            
            logger.info(f" Prediction: {activity} ({confidence:.2%})")
            
            # Here you could send prediction back to Firebase or trigger webhooks
            # firebase_handler.send_prediction(activity, confidence, probabilities)
    
    except Exception as e:
        logger.error(f"Error handling Firebase data: {e}")


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
