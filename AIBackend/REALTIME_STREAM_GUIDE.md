# 📡 Hướng Dẫn Stream Dữ Liệu Realtime từ Firebase

## 🎯 Tổng Quan

Hệ thống này stream dữ liệu cảm biến từ **Firebase Realtime Database**, thực hiện dự đoán hoạt động (activity prediction), và lưu kết quả vào **Firestore Database**.

```
ESP32 → Firebase Realtime DB → FastAPI Backend → AI Model → Firestore Database
```

---

## 🚀 Khởi Động Hệ Thống

### 1. Cài Đặt Dependencies

```bash
cd AIBackend/backend
pip install -r requirements.txt
```

### 2. Khởi Động Backend Server

```bash
python main.py
```

Server sẽ chạy tại: `http://localhost:8000`

### 3. Truy Cập API Documentation

Mở trình duyệt và truy cập: `http://localhost:8000/docs`

---

## 📊 Cấu Trúc Dữ Liệu

### Firebase Realtime Database (Input)
```json
{
  "sensor_data": {
    "sample_0": {
      "ax_g": 0.05,
      "ay_g": 0.98,
      "az_g": 0.15,
      "gx_dps": 1.2,
      "gy_dps": -0.5,
      "gz_dps": 0.3,
      "amag_g": 1.01,
      "pitch_kf": 5.2,
      "roll_kf": 2.8,
      "timestamp": 513671
    },
    "sample_1": { ... }
  }
}
```

### Firestore Database (Output)
```json
{
  "activity": "STANDING",
  "confidence": 0.9995654225349426,
  "probabilities": {
    "DOWNSTAIRS": 0.0000016030040831298,
    "RUNNING": 2.405012028658045e-10,
    "SITTING": 0.00040585972601547837,
    "STANDING": 0.9995654225349426,
    "UPSTAIRS": 0.00001251727917406,
    "WALKING": 1.4370442613653722e-7
  },
  "timestamp": "2025-11-14T11:16:20.000Z",
  "created_at": "2025-11-14T11:20:30.320884",
  "user_id": "user1"
}
```

---

## 🔧 API Endpoints

### 1. Khởi Động Stream

**POST** `/firebase/start`

Bắt đầu lắng nghe dữ liệu từ Firebase Realtime Database.

**Request Body:**
```json
{
  "database_url": "https://imu-detection-app-default-rtdb.asia-southeast1.firebasedatabase.app",
  "service_account_path": "serviceAccountKey.json",
  "realtime_db_path": "/sensor_data",
  "firestore_collection": "activity_predictions",
  "user_id": "user1"
}
```

**Response:**
```json
{
  "status": "started",
  "message": "Firebase listener started successfully",
  "realtime_db_path": "/sensor_data",
  "firestore_collection": "activity_predictions",
  "user_id": "user1",
  "timestamp": "2025-11-14T11:20:30.320884"
}
```

### 2. Dừng Stream

**POST** `/firebase/stop`

Dừng lắng nghe dữ liệu từ Firebase.

**Response:**
```json
{
  "status": "stopped",
  "message": "Firebase listener stopped successfully",
  "total_predictions": 150,
  "timestamp": "2025-11-14T12:30:45.123456"
}
```

### 3. Kiểm Tra Trạng Thái Stream

**GET** `/stream/status`

**Response:**
```json
{
  "stream_active": true,
  "firebase_connected": true,
  "model_loaded": true,
  "predictions_made": 45,
  "buffer_size": 15,
  "can_predict": false,
  "timestamp": "2025-11-14T11:25:00.000000"
}
```

### 4. Lấy Predictions từ Firestore

**GET** `/firestore/predictions?user_id=user1&limit=10`

**Response:**
```json
{
  "status": "success",
  "count": 10,
  "predictions": [
    {
      "id": "0vQd8jmwBn31xS5yHkZj",
      "activity": "STANDING",
      "confidence": 0.9995654225349426,
      "probabilities": { ... },
      "timestamp": "2025-11-14T11:16:20.000Z",
      "user_id": "user1"
    },
    ...
  ],
  "timestamp": "2025-11-14T11:30:00.000000"
}
```

### 5. Lấy Chi Tiết Một Prediction

**GET** `/firestore/predictions/{doc_id}`

### 6. Xóa Prediction

**DELETE** `/firestore/predictions/{doc_id}`

### 7. Kiểm Tra Buffer

**GET** `/buffer/status`

**Response:**
```json
{
  "buffer_size": 35,
  "window_size": 40,
  "can_predict": false,
  "stream_active": true,
  "predictions_made": 78,
  "timestamp": "2025-11-14T11:35:00.000000"
}
```

### 8. Xóa Buffer

**POST** `/buffer/clear`

---

## 🔄 Luồng Hoạt Động

### Bước 1: ESP32 Gửi Dữ Liệu
ESP32 gửi dữ liệu cảm biến tới Firebase Realtime Database theo định dạng:
- Path: `/sensor_data/sample_X`
- Tần suất: 20Hz (20 mẫu/giây)
- 9 features: ax, ay, az, gx, gy, gz, amag, pitch, roll

### Bước 2: Backend Nhận Dữ Liệu
- FastAPI backend lắng nghe thay đổi trên `/sensor_data`
- Mỗi mẫu mới được thêm vào buffer
- Buffer có kích thước 40 mẫu (2 giây dữ liệu)

### Bước 3: Dự Đoán
Khi buffer đầy (40 mẫu):
- Dữ liệu được chuẩn hóa
- Model CNN-GRU dự đoán hoạt động
- Trả về: activity, confidence, probabilities

### Bước 4: Lưu Vào Firestore
Prediction được lưu vào Firestore:
- Collection: `activity_predictions`
- Document ID: Auto-generated
- Timestamp: Server timestamp

### Bước 5: Lặp Lại
Buffer sliding window với overlap 50%:
- Khi có 20 mẫu mới → Dự đoán tiếp

---

## 🧪 Test với Python Script

### Test Script: `test_stream.py`

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Start streaming
def start_stream():
    url = f"{BASE_URL}/firebase/start"
    payload = {
        "database_url": "https://imu-detection-app-default-rtdb.asia-southeast1.firebasedatabase.app",
        "service_account_path": "serviceAccountKey.json",
        "realtime_db_path": "/sensor_data",
        "firestore_collection": "activity_predictions",
        "user_id": "user1"
    }
    response = requests.post(url, json=payload)
    print("Start Stream:", response.json())

# 2. Check stream status
def check_status():
    url = f"{BASE_URL}/stream/status"
    response = requests.get(url)
    print("Stream Status:", response.json())

# 3. Get predictions
def get_predictions():
    url = f"{BASE_URL}/firestore/predictions?user_id=user1&limit=5"
    response = requests.get(url)
    print("Recent Predictions:", json.dumps(response.json(), indent=2))

# 4. Stop stream
def stop_stream():
    url = f"{BASE_URL}/firebase/stop"
    response = requests.post(url)
    print("Stop Stream:", response.json())

if __name__ == "__main__":
    # Start
    start_stream()
    
    # Wait for some predictions...
    import time
    time.sleep(10)
    
    # Check status
    check_status()
    
    # Get predictions
    get_predictions()
    
    # Stop
    stop_stream()
```

---

## 🎯 Test với cURL

### Start Stream
```bash
curl -X POST "http://localhost:8000/firebase/start" \
  -H "Content-Type: application/json" \
  -d '{
    "database_url": "https://imu-detection-app-default-rtdb.asia-southeast1.firebasedatabase.app",
    "service_account_path": "serviceAccountKey.json",
    "realtime_db_path": "/sensor_data",
    "firestore_collection": "activity_predictions",
    "user_id": "user1"
  }'
```

### Check Status
```bash
curl -X GET "http://localhost:8000/stream/status"
```

### Get Predictions
```bash
curl -X GET "http://localhost:8000/firestore/predictions?user_id=user1&limit=5"
```

### Stop Stream
```bash
curl -X POST "http://localhost:8000/firebase/stop"
```

---

## 📈 Monitoring

### Logs
Backend sẽ in ra logs chi tiết:
```
INFO - 📨 Received data from Firebase: {...}
INFO - Added sample sample_1 to buffer
INFO - 🎯 Prediction: STANDING (99.96%)
INFO - ✅ Saved prediction to Firestore (Doc ID: 0vQd8jmwBn31xS5yHkZj)
INFO - 💾 Prediction saved to Firestore (Doc ID: ...)
```

### Metrics
- **predictions_made**: Tổng số predictions
- **buffer_size**: Số mẫu hiện tại trong buffer
- **stream_active**: Stream có đang hoạt động không

---

## ⚙️ Configuration

### Buffer Settings (main.py)
```python
data_buffer = DataBuffer(
    window_size=40,   # 40 samples = 2 seconds at 20Hz
    overlap=0.5       # 50% overlap = 20 samples step
)
```

### Model Settings (predictor.py)
```python
model_path = "../AI/final_model_test_PHONG_QUANG.h5"
activities = ['WALKING', 'UPSTAIRS', 'DOWNSTAIRS', 'SITTING', 'STANDING', 'RUNNING']
```

---

## 🐛 Troubleshooting

### Problem: Stream không bắt đầu
**Solution:**
- Kiểm tra `serviceAccountKey.json` có đúng path không
- Kiểm tra Firebase Realtime Database URL
- Kiểm tra network connection

### Problem: Không lưu được vào Firestore
**Solution:**
- Kiểm tra Firestore được enable trong Firebase Console
- Kiểm tra service account có quyền write vào Firestore
- Kiểm tra collection name đúng chưa

### Problem: Predictions không chính xác
**Solution:**
- Kiểm tra model path
- Kiểm tra dữ liệu input có đúng format không
- Kiểm tra buffer có đủ 40 samples không

---

## 📚 Tài Liệu Liên Quan

- [Firebase Realtime Database](https://firebase.google.com/docs/database)
- [Cloud Firestore](https://firebase.google.com/docs/firestore)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TensorFlow/Keras](https://www.tensorflow.org/)

---

## ✨ Features

- ✅ Real-time streaming từ Firebase Realtime Database
- ✅ Sliding window buffer với overlap 50%
- ✅ Dự đoán hoạt động với CNN-GRU model
- ✅ Lưu predictions vào Firestore tự động
- ✅ RESTful API để quản lý stream
- ✅ Monitoring và logging chi tiết
- ✅ Support multiple users
- ✅ Swagger UI documentation

---

## 🔮 Future Enhancements

- [ ] WebSocket support cho real-time updates
- [ ] Activity history và analytics
- [ ] User dashboard
- [ ] Alert system cho activities đặc biệt
- [ ] Multi-model ensemble predictions
- [ ] Data validation và cleaning pipeline

---

**Happy Streaming! 🚀**
