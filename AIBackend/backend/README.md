# Human Activity Recognition Backend

FastAPI backend để nhận dữ liệu cảm biến từ ESP32 qua Firebase và dự đoán hành vi người dùng.

## 🚀 Tính năng

- ✅ **Real-time Prediction**: Dự đoán hành vi theo thời gian thực từ dữ liệu cảm biến
- ✅ **Firebase Integration**: Kết nối với Firebase Realtime Database
- ✅ **Data Buffering**: Quản lý buffer thông minh cho sliding window
- ✅ **RESTful API**: API đầy đủ với FastAPI
- ✅ **Preprocessing Pipeline**: Tiền xử lý dữ liệu giống như training pipeline
- ✅ **Multiple Prediction Modes**: Single sample, batch, và streaming prediction

## 📋 Yêu cầu

- Python 3.8+
- TensorFlow 2.15+
- Firebase Admin SDK
- FastAPI & Uvicorn

## 🔧 Cài đặt

### 1. Tạo Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# hoặc
venv\Scripts\activate  # Windows
```

### 2. Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

### 3. Cấu hình

Tạo file `.env` từ `.env.example`:

```bash
cp .env.example .env
```

Chỉnh sửa `.env` với thông tin của bạn:

```env
# Model path
MODEL_PATH=../AI/final_model_test_PHONG_QUANG.h5

# Firebase
FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
```

### 4. Tải Firebase Service Account

1. Vào [Firebase Console](https://console.firebase.google.com/)
2. Chọn project của bạn
3. Settings > Service Accounts
4. Generate new private key
5. Lưu file JSON vào `backend/firebase-service-account.json`

## 🎯 Sử dụng

### Chạy Server

```bash
# Development mode (auto-reload)
python main.py

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

Server sẽ chạy tại: `http://localhost:8000`

### API Documentation

Sau khi chạy server, truy cập:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📡 API Endpoints

### 1. Health Check

```bash
GET /health
```

Kiểm tra trạng thái server và model.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "firebase_connected": false,
  "timestamp": "2024-11-12T10:30:00",
  "model_info": {
    "activities": ["WALKING", "UPSTAIRS", "DOWNSTAIRS", "SITTING", "STANDING", "RUNNING"],
    "window_size": 40,
    "n_features": 11
  }
}
```

### 2. Single Prediction

```bash
POST /predict/single
```

Dự đoán từ một sample (cần buffer đủ 40 samples).

**Request:**
```json
{
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
```

**Response:**
```json
{
  "activity": "WALKING",
  "confidence": 0.95,
  "probabilities": {
    "WALKING": 0.95,
    "UPSTAIRS": 0.02,
    "DOWNSTAIRS": 0.01,
    "SITTING": 0.01,
    "STANDING": 0.01,
    "RUNNING": 0.00
  },
  "timestamp": "2024-11-12T10:30:00",
  "samples_used": 40
}
```

### 3. Batch Prediction

```bash
POST /predict/batch
```

Dự đoán từ một batch samples (nhanh hơn single).

**Request:**
```json
{
  "data": [
    {
      "ax_g": 0.05,
      "ay_g": 0.98,
      "az_g": 0.15,
      "gx_dps": 1.2,
      "gy_dps": -0.5,
      "gz_dps": 0.3,
      "amag_g": 1.01,
      "pitch_kf": 5.2,
      "roll_kf": 2.8
    },
    ... // Ít nhất 40 samples
  ],
  "device_id": "ESP32_001"
}
```

### 4. Firebase Integration

#### Start Listening

```bash
POST /firebase/start
```

Bắt đầu lắng nghe Firebase.

**Request:**
```json
{
  "database_url": "https://your-project-id.firebaseio.com",
  "service_account_path": "./firebase-service-account.json"
}
```

#### Stop Listening

```bash
POST /firebase/stop
```

Dừng lắng nghe Firebase.

### 5. Buffer Management

```bash
# Get buffer status
GET /buffer/status

# Clear buffer
POST /buffer/clear
```

## 🔥 Firebase Structure

### Cấu trúc dữ liệu gợi ý:

```json
{
  "sensor_data": {
    "ESP32_001": {
      "latest": {
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
  },
  "predictions": {
    "ESP32_001": {
      "latest": {
        "activity": "WALKING",
        "confidence": 0.95,
        "timestamp": "2024-11-12T10:30:00"
      }
    }
  }
}
```

## 📊 Workflow

### 1. Single Sample Flow

```
ESP32 → Firebase → Backend API
                    ↓
                 Buffer (40 samples)
                    ↓
                 Preprocessing
                    ↓
                 Model Prediction
                    ↓
                 Response/Firebase
```

### 2. Batch Flow

```
ESP32 (batch) → Firebase/HTTP → Backend API
                                  ↓
                              Preprocessing
                                  ↓
                              Model Prediction
                                  ↓
                              Response
```

## 🧪 Testing

### Test với cURL

```bash
# Health check
curl http://localhost:8000/health

# Single prediction
curl -X POST http://localhost:8000/predict/single \
  -H "Content-Type: application/json" \
  -d '{
    "ax_g": 0.05,
    "ay_g": 0.98,
    "az_g": 0.15,
    "gx_dps": 1.2,
    "gy_dps": -0.5,
    "gz_dps": 0.3,
    "amag_g": 1.01,
    "pitch_kf": 5.2,
    "roll_kf": 2.8
  }'
```

### Test với Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Single prediction
data = {
    "ax_g": 0.05,
    "ay_g": 0.98,
    "az_g": 0.15,
    "gx_dps": 1.2,
    "gy_dps": -0.5,
    "gz_dps": 0.3,
    "amag_g": 1.01,
    "pitch_kf": 5.2,
    "roll_kf": 2.8
}

response = requests.post("http://localhost:8000/predict/single", json=data)
print(response.json())
```

## 🏗️ Architecture

```
backend/
├── main.py                 # FastAPI application & endpoints
├── predictor.py           # Model loading & prediction logic
├── firebase_handler.py    # Firebase connection & streaming
├── data_buffer.py         # Data buffering & window management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## 🎓 Activities

Model dự đoán 6 hoạt động:

1. **WALKING** - Đi bộ
2. **UPSTAIRS** - Đi lên cầu thang
3. **DOWNSTAIRS** - Đi xuống cầu thang
4. **SITTING** - Ngồi
5. **STANDING** - Đứng
6. **RUNNING** - Chạy

## 📝 Sensor Data Format

### Required Fields:

- `ax_g`: Accelerometer X (g)
- `ay_g`: Accelerometer Y (g)
- `az_g`: Accelerometer Z (g)
- `gx_dps`: Gyroscope X (degrees/second)
- `gy_dps`: Gyroscope Y (degrees/second)
- `gz_dps`: Gyroscope Z (degrees/second)
- `amag_g`: Accelerometer magnitude (g)
- `pitch_kf`: Kalman filtered pitch (degrees)
- `roll_kf`: Kalman filtered roll (degrees)

### Optional Fields:

- `timestamp`: Timestamp in milliseconds

## ⚙️ Configuration

### Window Size

Default: 40 samples (2 giây @ 20Hz)

Có thể thay đổi trong `predictor.py`:

```python
self.window_size = 40  # Số samples trong 1 window
self.overlap = 0.5     # 50% overlap
```

### Buffer Settings

Trong `data_buffer.py`:

```python
self.buffer = deque(maxlen=window_size * 2)  # Circular buffer
```

## 🐛 Troubleshooting

### Model không load được

```bash
# Kiểm tra path
ls -la ../AI/final_model_test_PHONG_QUANG.h5

# Thử load model trực tiếp
python -c "from tensorflow import keras; keras.models.load_model('../AI/final_model_test_PHONG_QUANG.h5')"
```

### Firebase connection lỗi

1. Kiểm tra `firebase-service-account.json` tồn tại
2. Kiểm tra `FIREBASE_DATABASE_URL` đúng
3. Kiểm tra Firebase rules cho phép read/write

### Buffer không đủ data

- Cần ít nhất 40 samples trước khi predict
- Kiểm tra `/buffer/status` để xem buffer size
