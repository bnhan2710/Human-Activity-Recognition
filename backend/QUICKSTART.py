"""
Quick Start Guide for Human Activity Recognition Backend
"""

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║         🏃 HUMAN ACTIVITY RECOGNITION BACKEND - QUICK START 🏃              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 SYSTEM OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ESP32 (Sensor) → Firebase → FastAPI Backend → ML Model → Prediction
                    ↓                              ↓
                HTTP API ←─────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 ACTIVITIES DETECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. WALKING     - Đi bộ
2. UPSTAIRS    - Đi lên cầu thang
3. DOWNSTAIRS  - Đi xuống cầu thang
4. SITTING     - Ngồi
5. STANDING    - Đứng
6. RUNNING     - Chạy

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 QUICK START
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: Install Dependencies
────────────────────────────────────────────────────────────────────────────────
$ cd backend
$ pip install -r requirements.txt

STEP 2: Configure Environment
────────────────────────────────────────────────────────────────────────────────
$ cp .env.example .env
$ nano .env  # Edit configuration

Required settings:
  - MODEL_PATH: Path to your .h5 model file
  - FIREBASE_DATABASE_URL: Your Firebase database URL (optional)
  - FIREBASE_SERVICE_ACCOUNT_PATH: Path to Firebase credentials (optional)

STEP 3: Start Server
────────────────────────────────────────────────────────────────────────────────
$ python main.py

Server will start at: http://localhost:8000
API Docs: http://localhost:8000/docs

STEP 4: Test API
────────────────────────────────────────────────────────────────────────────────
$ python test_api.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 PROJECT STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

backend/
├── main.py                  # FastAPI application & API endpoints
├── predictor.py            # ML model loading & prediction logic
├── firebase_handler.py     # Firebase Real-time Database integration
├── data_buffer.py          # Circular buffer for sensor data
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── README.md              # Full documentation
├── ESP32_GUIDE.md         # ESP32 integration guide
└── test_api.py            # API testing script

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔌 API ENDPOINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

General:
  GET  /              - Root endpoint
  GET  /health        - Health check

Prediction:
  POST /predict/single   - Predict from single sensor reading (needs buffer)
  POST /predict/batch    - Predict from batch of readings (faster)

Firebase:
  POST /firebase/start   - Start Firebase listener
  POST /firebase/stop    - Stop Firebase listener

Buffer:
  GET  /buffer/status    - Get buffer status
  POST /buffer/clear     - Clear buffer

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 SENSOR DATA FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Required fields (9 features):
  • ax_g       : Accelerometer X (g)
  • ay_g       : Accelerometer Y (g)
  • az_g       : Accelerometer Z (g)
  • gx_dps     : Gyroscope X (degrees/second)
  • gy_dps     : Gyroscope Y (degrees/second)
  • gz_dps     : Gyroscope Z (degrees/second)
  • amag_g     : Accelerometer magnitude (g)
  • pitch_kf   : Kalman filtered pitch (degrees)
  • roll_kf    : Kalman filtered roll (degrees)

Optional:
  • timestamp  : Timestamp in milliseconds

Note: Backend automatically computes 2 derivative features (d_pitch_kf, d_roll_kf)
      Total: 11 features for model input

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 EXAMPLE USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Python:
────────────────────────────────────────────────────────────────────────────────
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Batch prediction
data = {
    "data": [
        {
            "ax_g": 0.05, "ay_g": 0.98, "az_g": 0.15,
            "gx_dps": 1.2, "gy_dps": -0.5, "gz_dps": 0.3,
            "amag_g": 1.01, "pitch_kf": 5.2, "roll_kf": 2.8
        },
        # ... 40+ samples total
    ]
}
response = requests.post("http://localhost:8000/predict/batch", json=data)
print(response.json())

cURL:
────────────────────────────────────────────────────────────────────────────────
# Health check
curl http://localhost:8000/health

# Single prediction
curl -X POST http://localhost:8000/predict/single \\
  -H "Content-Type: application/json" \\
  -d '{
    "ax_g": 0.05, "ay_g": 0.98, "az_g": 0.15,
    "gx_dps": 1.2, "gy_dps": -0.5, "gz_dps": 0.3,
    "amag_g": 1.01, "pitch_kf": 5.2, "roll_kf": 2.8
  }'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Window Configuration:
  • Window Size: 40 samples (2 seconds @ 20Hz)
  • Overlap: 50% (20 samples)
  • Buffer Size: 80 samples (2x window size)

Model Configuration:
  • Input Shape: (40, 11)  # 40 timesteps, 11 features
  • Output: 6 classes (activity probabilities)
  • Architecture: CNN-GRU hybrid

Preprocessing Pipeline:
  1. Compute derivatives (d_pitch_kf, d_roll_kf)
  2. Separate raw (9) and derivative (2) features
  3. QuantileTransformer on raw features
  4. Combine to 11 features
  5. StandardScaler on all features

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 FIREBASE INTEGRATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Setup:
1. Create Firebase project at https://console.firebase.google.com/
2. Enable Realtime Database
3. Download service account key (Settings → Service Accounts)
4. Save as firebase-service-account.json
5. Configure database URL in .env

Recommended Database Structure:
{
  "sensor_data": {
    "ESP32_001": {
      "latest": { /* sensor reading */ }
    }
  },
  "predictions": {
    "ESP32_001": {
      "latest": { /* prediction result */ }
    }
  }
}

Start Listening:
POST /firebase/start with Firebase config

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 ESP32 INTEGRATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

See ESP32_GUIDE.md for:
  • Complete Arduino code
  • Wiring diagram
  • Library requirements
  • Calibration procedure
  • Firebase integration
  • Troubleshooting

Required Hardware:
  • ESP32 development board
  • MPU6050 6-axis IMU sensor
  • USB cable for programming

Sampling Rate:
  • 20Hz (50ms interval)
  • Matches training data

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🐛 TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Model not loading:
  → Check MODEL_PATH in .env
  → Verify .h5 file exists
  → Ensure TensorFlow is installed correctly

Predictions are wrong:
  → Check sensor data format
  → Verify all 9 features are present
  → Ensure sampling rate is 20Hz
  → Check sensor orientation

Buffer errors:
  → Need 40 samples before first prediction
  → Check /buffer/status endpoint
  → Clear buffer with /buffer/clear if stuck

Firebase connection failed:
  → Verify service account JSON is valid
  → Check database URL format
  → Ensure Firebase rules allow read/write

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Full Documentation:
  • README.md          - Complete API documentation
  • ESP32_GUIDE.md     - ESP32 integration guide
  • .env.example       - Configuration template
  • http://localhost:8000/docs - Interactive API docs (Swagger)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ✓ Install dependencies          → pip install -r requirements.txt
2. ✓ Configure environment         → Edit .env file
3. ✓ Start server                  → python main.py
4. ✓ Test API                      → python test_api.py
5. ⚬ Setup ESP32                   → See ESP32_GUIDE.md
6. ⚬ Configure Firebase (optional) → Setup service account
7. ⚬ Deploy to production          → Use gunicorn or docker

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 You're all set! Start the server and begin recognizing activities!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
