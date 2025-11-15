# 🔥 Firebase Realtime Stream Integration - Summary

## 📝 Tổng Quan Các Thay Đổi

### 1. **firebase_handler.py** - Thêm Firestore Support
✅ **Các thay đổi:**
- Import `firestore` từ `firebase_admin`
- Thêm `use_firestore` parameter trong constructor
- Khởi tạo Firestore client
- Thêm các phương thức Firestore:
  - `get_firestore_client()` - Lấy Firestore client
  - `save_prediction_to_firestore()` - Lưu prediction vào Firestore
  - `get_predictions_from_firestore()` - Lấy predictions từ Firestore
  - `update_prediction_in_firestore()` - Cập nhật prediction
  - `delete_prediction_from_firestore()` - Xóa prediction

### 2. **main.py** - Stream Flow Implementation
✅ **Các thay đổi:**

#### Global Variables:
- `stream_active` - Theo dõi trạng thái stream
- `prediction_count` - Đếm số lượng predictions

#### Models:
- **FirebaseConfig**: Thêm fields:
  - `realtime_db_path` - Path trong Realtime Database
  - `firestore_collection` - Collection name trong Firestore
  - `user_id` - User identifier

#### Endpoints:

**Firebase Endpoints:**
- `POST /firebase/start` - Khởi động stream (cập nhật)
- `POST /firebase/stop` - Dừng stream (cập nhật)
- `GET /stream/status` - Kiểm tra trạng thái stream (mới)

**Firestore Endpoints (mới):**
- `GET /firestore/predictions` - Lấy danh sách predictions
- `GET /firestore/predictions/{doc_id}` - Lấy chi tiết prediction
- `DELETE /firestore/predictions/{doc_id}` - Xóa prediction

**Buffer Endpoints:**
- `GET /buffer/status` - Cập nhật với stream info
- `POST /buffer/clear` - Không thay đổi

#### Helper Functions:
- **handle_firebase_data()**: Hoàn toàn mới
  - Xử lý nhiều cấu trúc dữ liệu
  - Tự động lưu predictions vào Firestore
  - Logging chi tiết
  - Error handling tốt hơn

### 3. **Các File Mới**

#### 📄 REALTIME_STREAM_GUIDE.md
- Hướng dẫn chi tiết về luồng stream
- Cấu trúc dữ liệu
- API documentation
- Test examples (cURL, Python)
- Troubleshooting guide

#### 🐍 test_stream.py
- Script test tương tác
- Menu-driven interface
- Các chức năng:
  - Full test (30s monitoring)
  - Quick test (10s monitoring)
  - Start/Stop stream
  - Check status
  - Get predictions
  - Clear buffer
  - Custom monitoring

#### 🖥️ test_stream.bat
- Windows batch script
- Tự động activate virtual environment
- Chạy test script
- Error handling

---

## 🎯 Luồng Hoạt Động Mới

```
┌─────────┐
│  ESP32  │ Gửi sensor data (20Hz)
└────┬────┘
     │
     ▼
┌──────────────────────────────┐
│ Firebase Realtime Database   │
│ Path: /sensor_data/sample_X  │
└──────────┬───────────────────┘
           │
           │ Realtime Listener
           ▼
┌──────────────────────────────┐
│   FastAPI Backend            │
│   - firebase_handler.py      │
│   - data_buffer.py          │
└──────────┬───────────────────┘
           │
           │ Buffer 40 samples
           ▼
┌──────────────────────────────┐
│   AI Model (CNN-GRU)         │
│   - predictor.py            │
└──────────┬───────────────────┘
           │
           │ Prediction
           ▼
┌──────────────────────────────┐
│   Firestore Database         │
│   Collection: activity_      │
│   predictions                │
└──────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Khởi Động Backend
```bash
cd AIBackend/backend
python main.py
```

### 2. Start Stream (Python)
```python
import requests

requests.post("http://localhost:8000/firebase/start", json={
    "database_url": "https://your-project.firebasedatabase.app",
    "service_account_path": "serviceAccountKey.json",
    "realtime_db_path": "/sensor_data",
    "firestore_collection": "activity_predictions",
    "user_id": "user1"
})
```

### 3. Monitor
```python
# Check status
requests.get("http://localhost:8000/stream/status")

# Get predictions
requests.get("http://localhost:8000/firestore/predictions?user_id=user1&limit=10")
```

### 4. Stop Stream
```python
requests.post("http://localhost:8000/firebase/stop")
```

---

## 🧪 Testing

### Option 1: Interactive Script
```bash
cd AIBackend/backend
python test_stream.py
```

### Option 2: Batch Script (Windows)
```bash
cd AIBackend/backend
test_stream.bat
```

### Option 3: Manual cURL
```bash
# Start
curl -X POST "http://localhost:8000/firebase/start" \
  -H "Content-Type: application/json" \
  -d '{"database_url":"https://...","service_account_path":"serviceAccountKey.json"}'

# Status
curl "http://localhost:8000/stream/status"

# Get predictions
curl "http://localhost:8000/firestore/predictions?user_id=user1&limit=5"

# Stop
curl -X POST "http://localhost:8000/firebase/stop"
```

---

## 📊 Data Flow Example

### Input (Realtime DB)
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
    }
  }
}
```

### Output (Firestore)
```json
{
  "id": "0vQd8jmwBn31xS5yHkZj",
  "activity": "STANDING",
  "confidence": 0.9995654225349426,
  "probabilities": {
    "STANDING": 0.9995654225349426,
    "SITTING": 0.00040585972601547837,
    "DOWNSTAIRS": 0.0000016030040831298,
    "UPSTAIRS": 0.00001251727917406,
    "WALKING": 1.4370442613653722e-7,
    "RUNNING": 2.405012028658045e-10
  },
  "timestamp": "2025-11-14T11:16:20.000Z",
  "created_at": "2025-11-14T11:20:30.320884",
  "user_id": "user1"
}
```

---

## ⚙️ Configuration

### Buffer Settings
```python
# main.py
data_buffer = DataBuffer(
    window_size=40,   # 2 seconds at 20Hz
    overlap=0.5       # 50% overlap
)
```

### Firebase Paths
```python
# Default paths
realtime_db_path = "/sensor_data"
firestore_collection = "activity_predictions"
```

### Model
```python
# predictor.py
model_path = "../AI/final_model_test_PHONG_QUANG.h5"
```

---

## 📈 Monitoring & Logs

### Backend Logs
```
INFO - 📨 Received data from Firebase: {...}
INFO - Added sample sample_1 to buffer
INFO - 🎯 Prediction: STANDING (99.96%)
INFO - ✅ Saved prediction to Firestore (Doc ID: 0vQd8jmw...)
INFO - 💾 Prediction saved to Firestore
```

### Stream Status Response
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

---

## 🔧 Dependencies

### Python Packages (requirements.txt)
```
fastapi
uvicorn
firebase-admin
tensorflow
pandas
numpy
scikit-learn
pydantic
```

### Firebase Setup
1. Firebase Realtime Database (enabled)
2. Cloud Firestore (enabled)
3. Service Account Key (downloaded)
4. Rules configured for read/write

---

## 🎯 Key Features

✅ **Real-time Streaming**: Lắng nghe dữ liệu từ Firebase Realtime Database
✅ **Automatic Prediction**: Tự động dự đoán khi buffer đầy
✅ **Firestore Integration**: Lưu predictions vào Firestore tự động
✅ **Buffer Management**: Sliding window với overlap 50%
✅ **RESTful API**: Đầy đủ endpoints để quản lý
✅ **Monitoring**: Theo dõi status, metrics, logs
✅ **Error Handling**: Xử lý lỗi tốt, logging chi tiết
✅ **Testing Tools**: Script test tương tác, batch file
✅ **Documentation**: Hướng dẫn chi tiết, examples

---

## 🐛 Common Issues & Solutions

### Issue: "Firebase not connected"
**Solution**: Kiểm tra service account key path và database URL

### Issue: "Model not loaded"
**Solution**: Kiểm tra model path trong predictor initialization

### Issue: "Not enough data in buffer"
**Solution**: Đợi buffer đầy 40 samples (2 giây ở 20Hz)

### Issue: "Firestore permission denied"
**Solution**: Kiểm tra Firestore rules và service account permissions

---

## 📚 Documentation Files

1. **REALTIME_STREAM_GUIDE.md** - Chi tiết về API và usage
2. **README_STREAM.md** - Tóm tắt thay đổi (file này)
3. **main.py** - Backend với Firestore integration
4. **firebase_handler.py** - Firebase utilities
5. **test_stream.py** - Interactive test script

---

## 🔮 Next Steps

Có thể mở rộng thêm:
- [ ] WebSocket support cho real-time updates
- [ ] Dashboard để hiển thị predictions
- [ ] Alert system cho activities đặc biệt
- [ ] Multi-user support với authentication
- [ ] Activity history và analytics
- [ ] Export data to CSV/JSON
- [ ] Performance metrics và optimization

---

**Created**: November 14, 2025
**Version**: 1.0.0
**Status**: ✅ Production Ready

---

## 👥 Team

Hệ thống được phát triển cho PBL4 Project - Human Activity Recognition

**Happy Streaming! 🚀🔥**
